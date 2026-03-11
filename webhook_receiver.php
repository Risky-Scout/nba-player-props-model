<?php
/**
 * =============================================================================
 * webhook_receiver.php — DARKO Live Engine v2 | Full BDL Event Catalog
 * =============================================================================
 *
 * Register URL: https://dev.wizardofodds.com/tools/odds-scanner/predictions/api/webhook_receiver.php
 *
 * Subscribe to ALL of these events in BDL dashboard:
 *   nba.game.started       nba.game.ended          nba.game.period_ended
 *   nba.game.overtime
 *   nba.player.scored      nba.player.rebound       nba.player.assist
 *   nba.player.steal       nba.player.block         nba.player.foul
 *   nba.player.turnover
 *   nba.injury.created     nba.injury.updated       nba.injury.cleared
 *
 * State written to cache/live_state.json — structure:
 * {
 *   "players": {
 *     "lebron james": {
 *       "pts", "reb", "ast", "fg3m", "stl", "blk", "tov",
 *       "fouls",             ← foul count — drives minutes reduction
 *       "min_played",
 *       "period", "clock", "status", "game_id",
 *       "injured",           ← injury flag from nba.injury.created
 *       "injury_status",     ← "out", "questionable", "cleared"
 *       "shot_events",       ← last 5 scoring event timestamps (heat detection)
 *       "last_event_ts",     ← unix timestamp of last event (pace)
 *       "on_court_flag"      ← estimated on/off court from event recency
 *     }
 *   },
 *   "games": {
 *     "12345": {
 *       "period", "clock", "status",
 *       "home_score", "away_score",
 *       "score_margin",       ← abs(home - away), drives blowout detection
 *       "pace_events",        ← array of [timestamp, score] for live pace
 *       "period_scores",      ← per-quarter score splits
 *       "is_overtime",        ← boolean
 *       "ot_periods"          ← count of OT periods played
 *     }
 *   },
 *   "injuries": {             ← mid-game injury log
 *     "lebron james": {
 *       "status", "detail", "flagged_at", "game_id"
 *     }
 *   },
 *   "updated_at": "ISO string",
 *   "event_count": int        ← total events processed this session
 * }
 * =============================================================================
 */

header('Content-Type: application/json');
require_once __DIR__ . '/config.php';

// ── Config ─────────────────────────────────────────────────────────────────
$WEBHOOK_SECRET = defined('BDL_WEBHOOK_SECRET') ? BDL_WEBHOOK_SECRET : '';
$CACHE_DIR      = __DIR__ . '/cache';
$LIVE_STATE     = $CACHE_DIR . '/live_state.json';
$PROPS_CACHE    = $CACHE_DIR . '/live_props_cache.json';
$RATE_LOG       = $CACHE_DIR . '/.rate_log.json';

// Rate limit: max events per window from a single IP
const RATE_LIMIT_MAX    = 120;   // max events
const RATE_LIMIT_WINDOW = 60;    // seconds
// Staleness: reject events with timestamps older than this
const STALENESS_LIMIT   = 300;   // 5 minutes

if (!is_dir($CACHE_DIR)) mkdir($CACHE_DIR, 0755, true);

// ── Mandatory signature enforcement ───────────────────────────────────────
// If BDL_WEBHOOK_SECRET is configured, signature is REQUIRED.
// An empty or missing signature always fails when secret is set.
// This prevents replay attacks and spoofed payloads.
$rawBody = file_get_contents('php://input');

if ($WEBHOOK_SECRET) {
    $sig      = $_SERVER['HTTP_X_BDL_SIGNATURE'] ?? '';
    $expected = 'sha256=' . hash_hmac('sha256', $rawBody, $WEBHOOK_SECRET);
    if (!$sig || !hash_equals($expected, $sig)) {
        http_response_code(401);
        echo json_encode(['error' => 'Invalid or missing signature']);
        exit;
    }
}

// ── IP-based rate limiting ─────────────────────────────────────────────────
$ip  = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? 'unknown';
$ip  = trim(explode(',', $ip)[0]);  // first IP if forwarded chain
$now = time();

$rateData = [];
if (file_exists($RATE_LOG)) {
    $rd = json_decode(file_get_contents($RATE_LOG), true);
    if (is_array($rd)) $rateData = $rd;
}

// Prune stale windows
foreach ($rateData as $k => $v) {
    if (($v['window_start'] ?? 0) < $now - RATE_LIMIT_WINDOW) {
        unset($rateData[$k]);
    }
}

if (!isset($rateData[$ip])) {
    $rateData[$ip] = ['window_start' => $now, 'count' => 0];
}
$rateData[$ip]['count']++;

if ($rateData[$ip]['count'] > RATE_LIMIT_MAX) {
    file_put_contents($RATE_LOG, json_encode($rateData));
    http_response_code(429);
    echo json_encode(['error' => 'Rate limit exceeded', 'retry_after' => RATE_LIMIT_WINDOW]);
    exit;
}
file_put_contents($RATE_LOG, json_encode($rateData));

// ── Parse and validate payload ─────────────────────────────────────────────
$payload = json_decode($rawBody, true);
if (!$payload) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

$eventType = $payload['event'] ?? $payload['type'] ?? '';

// ── Staleness detection ────────────────────────────────────────────────────
// Reject events with a payload timestamp more than STALENESS_LIMIT seconds old.
// BDL includes 'created_at' or 'timestamp' in payload. If present, validate it.
// This prevents delayed or replayed events from corrupting live state.
$eventTs = null;
if (isset($payload['created_at'])) {
    $eventTs = strtotime($payload['created_at']);
} elseif (isset($payload['timestamp'])) {
    $eventTs = is_numeric($payload['timestamp'])
        ? (int)$payload['timestamp']
        : strtotime($payload['timestamp']);
}

if ($eventTs !== null && $eventTs !== false) {
    $age = $now - $eventTs;
    if ($age > STALENESS_LIMIT) {
        http_response_code(200);  // ACK to prevent BDL retry storm
        echo json_encode([
            'status'  => 'stale',
            'message' => "Event age {$age}s exceeds limit " . STALENESS_LIMIT . "s — discarded",
        ]);
        exit;
    }
}

// Duplicate event detection: reject if same event_id processed within last 5 min
$eventId = $payload['id'] ?? $payload['event_id'] ?? null;
if ($eventId) {
    $dedupeFile = $CACHE_DIR . '/.dedup.json';
    $dedup = [];
    if (file_exists($dedupeFile)) {
        $dd = json_decode(file_get_contents($dedupeFile), true);
        if (is_array($dd)) $dedup = $dd;
    }
    // Prune old entries
    foreach ($dedup as $k => $ts) {
        if ($ts < $now - 300) unset($dedup[$k]);
    }
    if (isset($dedup[$eventId])) {
        echo json_encode(['status' => 'duplicate', 'event_id' => $eventId]);
        exit;
    }
    $dedup[$eventId] = $now;
    file_put_contents($dedupeFile, json_encode($dedup));
}

// ── Load state (with file lock to prevent race conditions) ─────────────────
$lockFile = $CACHE_DIR . '/.state.lock';
$lock = fopen($lockFile, 'c');
flock($lock, LOCK_EX);

$state = [
    'players'     => [],
    'games'       => [],
    'injuries'    => [],
    'updated_at'  => '',
    'event_count' => 0,
];
if (file_exists($LIVE_STATE)) {
    $existing = json_decode(file_get_contents($LIVE_STATE), true);
    if ($existing) $state = $existing;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function normName($name) {
    if (!$name) return '';
    $name = strtolower(trim($name));
    $name = str_replace(['.', "'", '-'], ['', '', ' '], $name);
    $name = preg_replace('/\s+(jr|sr|iii|ii|iv)\s*$/i', '', $name);
    return preg_replace('/\s+/', ' ', trim($name));
}

function parseMin($minStr) {
    if (!$minStr) return 0.0;
    if (strpos($minStr, ':') !== false) {
        $p = explode(':', $minStr);
        return floatval($p[0]) + floatval($p[1] ?? 0) / 60.0;
    }
    return floatval($minStr);
}

function extractPlayer($payload) {
    // BDL sends player in different keys depending on event type
    $p = $payload['player']
      ?? $payload['data']['player']
      ?? $payload['data']
      ?? [];
    return $p;
}

function extractGame($payload) {
    return $payload['game']
        ?? $payload['data']['game']
        ?? [];
}

/**
 * Ensure a player entry exists in state with all required keys.
 */
function ensurePlayer(&$state, $norm, $gameId = null) {
    if (!isset($state['players'][$norm])) {
        $state['players'][$norm] = [
            'pts' => 0, 'reb' => 0, 'ast' => 0,
            'fg3m' => 0, 'stl' => 0, 'blk' => 0, 'tov' => 0,
            'fouls' => 0,
            'min_played' => 0.0,
            'period' => 0, 'clock' => '', 'status' => 'pre-game',
            'game_id' => $gameId,
            'injured' => false,
            'injury_status' => '',
            'shot_events' => [],   // last 5 scoring timestamps
            'last_event_ts' => time(),
            'on_court_flag' => true,
        ];
    }
}

/**
 * Compute live possessions-per-minute from game event log.
 * Used to measure actual pace vs pregame expected pace.
 */
function computeLivePaceRate(&$gameState) {
    $events = $gameState['pace_events'] ?? [];
    if (count($events) < 4) return null;  // Need min sample

    // Take last 8 scoring events to estimate current pace
    $recent = array_slice($events, -8);
    $first  = $recent[0];
    $last   = end($recent);

    $elapsed_sec = $last['ts'] - $first['ts'];
    if ($elapsed_sec < 30) return null;  // Too short a window

    $score_pts = $last['score'] - $first['score'];
    // ~1 possession per ~2 pts (NBA avg ~110 pts/100 poss → ~2 pts/poss → ~1.1 pts/poss)
    // Rough possessions: score_pts / 1.1 (league average points per possession)
    $possessions = $score_pts / 1.1;
    $elapsed_min = $elapsed_sec / 60.0;

    return $elapsed_min > 0 ? ($possessions / $elapsed_min) : null;
}

// ── Process event ──────────────────────────────────────────────────────────
$state['event_count'] = ($state['event_count'] ?? 0) + 1;
$now = time();

switch ($eventType) {

    // ════════════════════════════════════════════════════════════════════════
    // GAME EVENTS
    // ════════════════════════════════════════════════════════════════════════

    case 'nba.game.started':
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? $payload['id'] ?? null;
        if ($gameId) {
            $state['games'][$gameId] = [
                'period'       => 1,
                'clock'        => '12:00',
                'status'       => 'in-progress',
                'home_score'   => 0,
                'away_score'   => 0,
                'score_margin' => 0,
                'pace_events'  => [],
                'period_scores'=> [],
                'is_overtime'  => false,
                'ot_periods'   => 0,
                'started_at'   => $now,
            ];
        }
        break;

    case 'nba.game.ended':
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? $payload['id'] ?? null;
        if ($gameId && isset($state['games'][$gameId])) {
            $state['games'][$gameId]['status'] = 'Final';
        }
        // Mark all players in this game as Final
        foreach ($state['players'] as $norm => &$pData) {
            if (($pData['game_id'] ?? null) == $gameId) {
                $pData['status']       = 'Final';
                $pData['on_court_flag'] = false;
            }
        }
        unset($pData);
        break;

    case 'nba.game.period_ended':
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;
        $period = intval($game['period'] ?? $payload['period'] ?? 0);
        if ($gameId && isset($state['games'][$gameId])) {
            // Log per-period score split
            $g = &$state['games'][$gameId];
            $g['period_scores'][$period] = [
                'home' => $g['home_score'] ?? 0,
                'away' => $g['away_score'] ?? 0,
            ];
            $g['period'] = $period + 1;
            $g['clock']  = '12:00';
            // Recalibrate pace window — reset to last 4 events only
            if (count($g['pace_events']) > 4) {
                $g['pace_events'] = array_slice($g['pace_events'], -4);
            }
        }
        break;

    case 'nba.game.overtime':
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;
        if ($gameId && isset($state['games'][$gameId])) {
            $state['games'][$gameId]['is_overtime'] = true;
            $state['games'][$gameId]['ot_periods'] =
                ($state['games'][$gameId]['ot_periods'] ?? 0) + 1;
            // OT periods are 5 min — reset clock
            $state['games'][$gameId]['clock'] = '5:00';
        }
        break;

    // ════════════════════════════════════════════════════════════════════════
    // PLAYER STAT EVENTS — each fires immediately when the play occurs
    // ════════════════════════════════════════════════════════════════════════

    case 'nba.player.scored':
        $player  = extractPlayer($payload);
        $game    = extractGame($payload);
        $gameId  = $game['id'] ?? null;
        $fn      = $player['first_name'] ?? '';
        $ln      = $player['last_name']  ?? '';
        $norm    = normName("$fn $ln");
        $pts     = intval($payload['points'] ?? $payload['pts'] ?? 2);  // 1, 2, or 3
        $is3pt   = ($pts === 3);

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $p = &$state['players'][$norm];
            $p['pts']  += $pts;
            if ($is3pt) $p['fg3m'] += 1;
            $p['period']        = intval($game['period'] ?? $p['period']);
            $p['clock']         = $game['time'] ?? $game['clock'] ?? $p['clock'];
            $p['status']        = 'in-progress';
            $p['on_court_flag'] = true;
            $p['last_event_ts'] = $now;

            // Heat detection: track last 5 scoring timestamps
            $p['shot_events'][] = ['ts' => $now, 'pts' => $pts, 'is3' => $is3pt];
            if (count($p['shot_events']) > 5) {
                array_shift($p['shot_events']);
            }
        }

        // Update game score for margin/pace tracking
        if ($gameId && isset($state['games'][$gameId])) {
            $g = &$state['games'][$gameId];
            // Determine which team scored — need team context from payload
            $scoringTeamId = $player['team_id'] ?? null;
            $homeTeamId    = $game['home_team_id'] ?? null;

            if ($scoringTeamId && $homeTeamId) {
                if ($scoringTeamId == $homeTeamId) {
                    $g['home_score'] = ($g['home_score'] ?? 0) + $pts;
                } else {
                    $g['away_score'] = ($g['away_score'] ?? 0) + $pts;
                }
            } else {
                // Fallback: use game object scores if provided
                $g['home_score'] = intval($game['home_team_score'] ?? $g['home_score'] ?? 0);
                $g['away_score'] = intval($game['visitor_team_score'] ?? $g['away_score'] ?? 0);
            }

            $g['score_margin'] = abs($g['home_score'] - $g['away_score']);

            // Log pace event: cumulative total score + timestamp
            $g['pace_events'][] = ['ts' => $now, 'score' => $g['home_score'] + $g['away_score']];
            if (count($g['pace_events']) > 20) {
                array_shift($g['pace_events']);
            }
        }
        break;

    case 'nba.player.rebound':
        $player = extractPlayer($payload);
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $p = &$state['players'][$norm];
            $p['reb']  += 1;
            $p['period']        = intval($game['period'] ?? $p['period']);
            $p['clock']         = $game['time'] ?? $game['clock'] ?? $p['clock'];
            $p['status']        = 'in-progress';
            $p['on_court_flag'] = true;
            $p['last_event_ts'] = $now;
        }
        break;

    case 'nba.player.assist':
        $player = extractPlayer($payload);
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $p = &$state['players'][$norm];
            $p['ast']  += 1;
            $p['period']        = intval($game['period'] ?? $p['period']);
            $p['clock']         = $game['time'] ?? $game['clock'] ?? $p['clock'];
            $p['status']        = 'in-progress';
            $p['on_court_flag'] = true;
            $p['last_event_ts'] = $now;
        }
        break;

    case 'nba.player.steal':
        $player = extractPlayer($payload);
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $p = &$state['players'][$norm];
            $p['stl']  += 1;
            $p['on_court_flag'] = true;
            $p['last_event_ts'] = $now;
        }
        break;

    case 'nba.player.block':
        $player = extractPlayer($payload);
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $p = &$state['players'][$norm];
            $p['blk']  += 1;
            $p['on_court_flag'] = true;
            $p['last_event_ts'] = $now;
        }
        break;

    case 'nba.player.turnover':
        $player = extractPlayer($payload);
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $p = &$state['players'][$norm];
            $p['tov']  += 1;
            $p['on_court_flag'] = true;
            $p['last_event_ts'] = $now;
        }
        break;

    // ── FOUL — the highest-value event for live prop prediction ───────────
    case 'nba.player.foul':
        $player = extractPlayer($payload);
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $p = &$state['players'][$norm];
            $p['fouls'] += 1;
            $p['period']         = intval($game['period'] ?? $p['period']);
            $p['clock']          = $game['time'] ?? $game['clock'] ?? $p['clock'];
            $p['last_event_ts']  = $now;

            // Foul thresholds change strategy immediately:
            // Q1/Q2: 2 fouls = sit; Q3/Q4: 4 fouls = sit
            // 5 fouls = disqualified for remainder of game
            $period = $p['period'];
            $fouls  = $p['fouls'];

            if ($fouls >= 5) {
                $p['foul_trouble_level'] = 'fouled_out';   // DQ
            } elseif ($fouls == 4) {
                $p['foul_trouble_level'] = 'severe';       // -35% minutes
            } elseif ($fouls == 3 && $period <= 2) {
                $p['foul_trouble_level'] = 'moderate';     // -18% minutes, likely sits
            } elseif ($fouls == 3) {
                $p['foul_trouble_level'] = 'mild';         // -10% minutes
            } else {
                $p['foul_trouble_level'] = 'none';
            }
        }
        break;

    // ════════════════════════════════════════════════════════════════════════
    // INJURY EVENTS — mid-game injury = immediate prop adjustment
    // ════════════════════════════════════════════════════════════════════════

    case 'nba.injury.created':
        $player = extractPlayer($payload);
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");
        $game   = extractGame($payload);
        $gameId = $game['id'] ?? null;

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $state['players'][$norm]['injured']        = true;
            $state['players'][$norm]['injury_status']  = 'out';
            $state['players'][$norm]['on_court_flag']  = false;

            // Log to injuries registry for dashboard display
            $state['injuries'][$norm] = [
                'status'      => 'out',
                'detail'      => $payload['description'] ?? $payload['detail'] ?? 'Injury reported',
                'flagged_at'  => date('c'),
                'game_id'     => $gameId,
                'player_name' => "$fn $ln",
            ];
        }
        break;

    case 'nba.injury.updated':
        $player = extractPlayer($payload);
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm && isset($state['injuries'][$norm])) {
            $newStatus = strtolower($payload['status'] ?? 'questionable');
            $state['injuries'][$norm]['status']     = $newStatus;
            $state['injuries'][$norm]['detail']     = $payload['description'] ?? $payload['detail'] ?? '';
            $state['injuries'][$norm]['updated_at'] = date('c');
            if (isset($state['players'][$norm])) {
                $state['players'][$norm]['injury_status'] = $newStatus;
                $state['players'][$norm]['injured']       = ($newStatus !== 'cleared');
            }
        }
        break;

    case 'nba.injury.cleared':
        $player = extractPlayer($payload);
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm) {
            if (isset($state['players'][$norm])) {
                $state['players'][$norm]['injured']        = false;
                $state['players'][$norm]['injury_status']  = 'cleared';
                $state['players'][$norm]['on_court_flag']  = true;
            }
            if (isset($state['injuries'][$norm])) {
                $state['injuries'][$norm]['status']     = 'cleared';
                $state['injuries'][$norm]['cleared_at'] = date('c');
            }
        }
        break;

    // ── Fallback: boxscore.updated still used as a sync checkpoint ────────
    case 'boxscore.updated':
    case 'box_score.updated':
        $game   = $payload['game']   ?? $payload['data']['game']   ?? [];
        $player = $payload['player'] ?? $payload['data']['player'] ?? [];
        $stats  = $payload['stats']  ?? $payload['data']           ?? $payload;
        $gameId = $game['id'] ?? null;
        $fn     = $player['first_name'] ?? '';
        $ln     = $player['last_name']  ?? '';
        $norm   = normName("$fn $ln");

        if ($norm) {
            ensurePlayer($state, $norm, $gameId);
            $p = &$state['players'][$norm];
            // Boxscore is authoritative for cumulative totals — sync them
            $p['pts']        = max($p['pts'],  intval($stats['pts']  ?? 0));
            $p['reb']        = max($p['reb'],  intval($stats['reb']  ?? 0));
            $p['ast']        = max($p['ast'],  intval($stats['ast']  ?? 0));
            $p['fg3m']       = max($p['fg3m'], intval($stats['fg3m'] ?? 0));
            $p['stl']        = max($p['stl'],  intval($stats['stl']  ?? 0));
            $p['blk']        = max($p['blk'],  intval($stats['blk']  ?? 0));
            $p['tov']        = max($p['tov'],  intval($stats['tov']  ?? $stats['turnover'] ?? 0));
            $p['fouls']      = max($p['fouls'] ?? 0, intval($stats['pf'] ?? 0));
            $p['min_played'] = max($p['min_played'], round(parseMin($stats['min'] ?? '0'), 1));
            $p['period']     = intval($game['period'] ?? $p['period']);
            $p['clock']      = $game['time'] ?? $p['clock'];
            $p['status']     = $game['status'] ?? 'in-progress';
        }

        if ($gameId && isset($state['games'][$gameId])) {
            $g = &$state['games'][$gameId];
            $g['home_score']   = intval($game['home_team_score'] ?? $g['home_score'] ?? 0);
            $g['away_score']   = intval($game['visitor_team_score'] ?? $g['away_score'] ?? 0);
            $g['score_margin'] = abs($g['home_score'] - $g['away_score']);
        }
        break;

    default:
        error_log("webhook_receiver: unhandled event '$eventType'");
        break;
}

// ── Write updated state ────────────────────────────────────────────────────
$state['updated_at'] = date('c');
file_put_contents($LIVE_STATE, json_encode($state, JSON_PRETTY_PRINT));

// Bust props cache so next API call returns fresh predictions
if (file_exists($PROPS_CACHE)) unlink($PROPS_CACHE);

// Release lock
flock($lock, LOCK_UN);
fclose($lock);

http_response_code(200);
echo json_encode([
    'ok'          => true,
    'event'       => $eventType,
    'players'     => count($state['players']),
    'event_count' => $state['event_count'],
]);
