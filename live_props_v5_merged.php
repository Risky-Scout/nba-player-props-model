<?php
/**
 * =============================================================================
 * live_props.php — NBA Props Model API v3
 * =============================================================================
 * Deploy: /tools/odds-scanner/predictions/api/live_props.php
 *
 * DATA FLOW:
 *   predictions/singles_{YYYY-MM-DD}.json → model output (quantile dist, EV)
 *   Ball Don't Lie /v1/box_scores/live     → live in-game box scores
 *   cache/live_state.json (webhooks)       → real-time event-driven state
 *   The Odds API                           → posted odds per book
 *
 * MODES (?mode=):
 *   auto    → live if games running, else pregame (default)
 *   pregame → cached pregame output only
 *   live    → always blend live box score data
 *
 * MODEL OUTPUT (from singles JSON):
 *   model_prob  → P(side hits) from LightGBM ensemble + isotonic calibration
 *   market_prob → vig-removed true probability from posted two-sided market
 *   model_odds  → FAIR ODDS: what we would charge if we were the book
 *   edge        → model_prob − market_implied_prob (after vig removal)
 *   ev          → expected return: (decimal−1)×p − (1−p)
 *   kelly       → fractional Kelly criterion for position sizing
 *   q_preds     → full quantile distribution P10→P90
 *   fair_line   → model's P50 (median projection = where we'd set the line)
 *
 * LIVE ENGINE v2 adjustments (in-game):
 *   1. Foul trouble minutes reduction
 *   2. Live vs pregame pace dynamic scaling
 *   3. Blowout / garbage time detection
 *   4. Bayesian stat update (prior=pregame, likelihood=in-game rate)
 *   5. Heat detection (pts + fg3m)
 *   6. OT-aware clock math
 *   7. Injury suppression + teammate usage redistribution
 *
 * CACHE: 60s (webhook receiver busts on every live event)
 * =============================================================================
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Cache-Control: no-cache');

error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);

require_once __DIR__ . '/nba_name_map.php';
require_once __DIR__ . '/config.php';

// ============================================================================
// CONFIG
// ============================================================================

$ODDS_API_KEY  = defined('ODDS_API_KEY') ? ODDS_API_KEY : '';
$BDL_API_KEY   = defined('BDL_API_KEY')  ? BDL_API_KEY  : '';
$CACHE_FILE    = __DIR__ . '/cache/live_props_cache.json';
$LIVE_STATE    = __DIR__ . '/cache/live_state.json';
$PRED_DIR      = __DIR__ . '/../';  // local fallback path
$GITHUB_RAW    = 'https://raw.githubusercontent.com/Risky-Scout/nba-player-props-model/main/predictions';
$CACHE_TTL     = 60;
$MODE          = $_GET['mode'] ?? 'auto';

// Affiliate books (revenue share priority order)
$BOOKS = ['bovada', 'betonlineag', 'betus', 'betanysports',
          'draftkings', 'fanduel', 'betmgm', 'betway', 'betrivers',
          'betparx', 'caesars', 'fanatics'];

$BOOK_NAMES = [
    'bovada'       => 'Bovada',
    'betonlineag'  => 'BetOnline',
    'betonline'    => 'BetOnline',
    'betus'        => 'BetUS',
    'betanysports' => 'BetAnySports',
    'draftkings'   => 'DraftKings',
    'fanduel'      => 'FanDuel',
    'betmgm'       => 'BetMGM',
    'betway'       => 'Betway',
    'betrivers'    => 'BetRivers',
    'betparx'      => 'BetParx',
    'caesars'      => 'Caesars',
    'fanatics'     => 'Fanatics',
];

$STAT_KEYS = [
    'player_points'    => 'pts',
    'player_rebounds'  => 'reb',
    'player_assists'   => 'ast',
    'player_threes'    => 'fg3m',
    'player_steals'    => 'stl',
    'player_blocks'    => 'blk',
];

// ============================================================================
// CACHE CHECK
// ============================================================================

if ($MODE !== 'live' && file_exists($CACHE_FILE) &&
    (time() - filemtime($CACHE_FILE)) < $CACHE_TTL) {
    echo file_get_contents($CACHE_FILE);
    exit;
}

// ============================================================================
// LINEUP POLLER — auto-trigger if data is stale (>60s)
// Polls BDL /v1/lineups so we know who is actually on court
// ============================================================================
$lineupPollLog = __DIR__ . '/cache/lineup_poll.log';
$lastPoll      = file_exists($lineupPollLog) ? filemtime($lineupPollLog) : 0;
if (time() - $lastPoll > 60) {
    $pollerPath = __DIR__ . '/lineup_poller.php';
    if (file_exists($pollerPath)) {
        exec('php ' . escapeshellarg($pollerPath) . ' > /dev/null 2>&1 &');
    }
}

// ============================================================================
// HTTP HELPERS
// ============================================================================

function oddsApiGet($url) {
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL            => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 12,
        CURLOPT_HTTPHEADER     => ['Accept: application/json'],
    ]);
    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return ($code === 200) ? json_decode($resp, true) : null;
}

function bdlApiGet($url, $apiKey) {
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL            => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_HTTPHEADER     => ['Accept: application/json', "Authorization: $apiKey"],
    ]);
    $resp = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    return ($code === 200) ? json_decode($resp, true) : null;
}

function toDecimal($american) {
    if ($american == 0) return 1.909;
    return $american > 0 ? ($american / 100) + 1 : (100 / abs($american)) + 1;
}

// Model probability → fair American odds (what we'd post if we were the book)
function toAmerican($prob) {
    if ($prob <= 0.01 || $prob >= 0.99) return 0;
    return $prob >= 0.5
        ? intval(-100 * $prob / (1 - $prob))
        : intval(100 * (1 - $prob) / $prob);
}

// ============================================================================
// LOAD MODEL PROJECTIONS — reads singles_{YYYY-MM-DD}.json
// Falls back to nba_props_today.json (legacy format)
// ============================================================================

function fetchFromGitHub($url) {
    // Fetch a file from GitHub raw with a 10s timeout
    $ctx = stream_context_create(['http' => [
        'timeout'       => 10,
        'ignore_errors' => true,
        'header'        => "User-Agent: WizardOfOdds-Props-Model/1.0\r\n",
    ]]);
    $data = @file_get_contents($url, false, $ctx);
    // Check HTTP status — GitHub returns 404 body for missing files
    $status = 0;
    foreach ($http_response_header ?? [] as $h) {
        if (preg_match('/HTTP\/\S+ (\d+)/', $h, $m)) $status = (int)$m[1];
    }
    return ($status === 200 && $data !== false) ? $data : null;
}

function findSinglesFile($predDir, $githubRaw) {
    // ── Strategy 1: GitHub raw (authoritative — workflow commits here daily) ──
    for ($i = 0; $i <= 1; $i++) {
        $d   = date('Y-m-d', strtotime("-{$i} day"));
        $url = $githubRaw . '/singles_' . $d . '.json';
        $raw = fetchFromGitHub($url);
        if ($raw !== null) {
            // Write to local cache so subsequent requests skip the GitHub call
            $local = $predDir . 'singles_' . $d . '.json';
            @file_put_contents($local, $raw);
            return [$local, $d, 'github'];
        }
    }
    // ── Strategy 2: Local filesystem (manual CyberDuck upload or cached) ──
    for ($i = 0; $i <= 3; $i++) {
        $d    = date('Y-m-d', strtotime("-{$i} day"));
        $path = $predDir . 'singles_' . $d . '.json';
        if (file_exists($path)) return [$path, $d, 'local'];
    }
    // ── Strategy 3: Glob — any singles file on disk ──
    $files = glob($predDir . 'singles_*.json');
    if ($files) {
        usort($files, fn($a, $b) => filemtime($b) - filemtime($a));
        $latest = $files[0];
        preg_match('/singles_(\d{4}-\d{2}-\d{2})\.json$/', $latest, $m);
        return [$latest, $m[1] ?? 'unknown', 'local_stale'];
    }
    return [null, null, null];
}

function loadModelProjections($predDir, $githubRaw) {
    [$singlesPath, $singlesDate, $dataSource] = findSinglesFile($predDir, $githubRaw);

    if ($singlesPath) {
        return loadFromSingles($singlesPath, $singlesDate);
    }

    // Legacy fallback: nba_props_today.json
    $legacy = $predDir . 'nba_props_today.json';
    if (file_exists($legacy)) {
        return loadFromLegacy($legacy);
    }

    return [[], null, null];
}

/**
 * Load from singles_{date}.json — the native model output format.
 * Builds a two-level index:
 *   $index[normName|stat]            = merged OVER+UNDER data
 *   $sideIndex[normName|stat|SIDE]   = side-specific pick (has q_preds, kelly, ev)
 */
function loadFromSingles($path, $date) {
    $raw = json_decode(file_get_contents($path), true);
    if (!$raw || empty($raw['picks'])) return [[], null, $date];

    $index     = [];   // normName|stat → merged model data
    $sideIndex = [];   // normName|stat|SIDE → pick-level data

    foreach ($raw['picks'] as $pick) {
        $norm    = normalizeName($pick['player_name'] ?? '');
        $stat    = strtolower($pick['stat'] ?? '');
        $side    = strtoupper($pick['side'] ?? 'OVER');
        if (!$norm || !$stat) continue;

        $baseKey = $norm . '|' . $stat;
        $sideKey = $norm . '|' . $stat . '|' . $side;

        // Side-level index: full quantile data lives here
        $sideIndex[$sideKey] = [
            'player'        => $pick['player_name'],
            'player_id'     => $pick['player_id'],
            'stat'          => $stat,
            'side'          => $side,
            'line'          => floatval($pick['line']),
            'model_prob'    => floatval($pick['model_prob']),
            'market_prob'   => floatval($pick['market_prob']),
            'ev_raw'        => floatval($pick['ev']),          // (decimal-1)*p - (1-p)
            'kelly_raw'     => floatval($pick['kelly_units']),
            'q50'           => floatval($pick['q50']),          // fair line (median projection)
            'q_preds'       => $pick['q_preds'] ?? [],
            'vendor'        => $pick['bet_vendor'] ?? '',
            'game'          => $pick['game'] ?? '',
            'game_id'       => $pick['game_id'] ?? null,
        ];

        // Merged index: one entry per player+stat covering both sides
        if (!isset($index[$baseKey])) {
            $index[$baseKey] = [
                'player'           => $pick['player_name'],
                'stat'             => $stat,
                'fair_line'        => floatval($pick['q50']),  // model's P50
                'q_preds'          => $pick['q_preds'] ?? [],
            ];
        }
        // Store side-specific probs into the base entry
        if ($side === 'OVER') {
            $index[$baseKey]['model_prob_over']  = floatval($pick['model_prob']);
            $index[$baseKey]['market_prob_over'] = floatval($pick['market_prob']);
            $index[$baseKey]['kelly_over']       = floatval($pick['kelly_units']);
            $index[$baseKey]['ev_over']          = floatval($pick['ev']);
        } else {
            $index[$baseKey]['model_prob_under']  = floatval($pick['model_prob']);
            $index[$baseKey]['market_prob_under'] = floatval($pick['market_prob']);
            $index[$baseKey]['kelly_under']       = floatval($pick['kelly_units']);
            $index[$baseKey]['ev_under']          = floatval($pick['ev']);
        }
    }

    // Fill in missing sides by complement
    foreach ($index as $key => &$entry) {
        if (!isset($entry['model_prob_over'])) {
            $entry['model_prob_over']  = 1 - ($entry['model_prob_under']  ?? 0.5);
            $entry['market_prob_over'] = 1 - ($entry['market_prob_under'] ?? 0.5);
            $entry['kelly_over']       = 0;
            $entry['ev_over']          = 0;
        }
        if (!isset($entry['model_prob_under'])) {
            $entry['model_prob_under']  = 1 - ($entry['model_prob_over']  ?? 0.5);
            $entry['market_prob_under'] = 1 - ($entry['market_prob_over'] ?? 0.5);
            $entry['kelly_under']       = 0;
            $entry['ev_under']          = 0;
        }
    }
    unset($entry);

    return [$index, $sideIndex, $date];
}

function loadFromLegacy($path) {
    $data = json_decode(file_get_contents($path), true);
    if (!$data || empty($data['props'])) return [[], null, null];
    $index = [];
    foreach ($data['props'] as $p) {
        $norm = normalizeName($p['player'] ?? '');
        $stat = strtolower($p['stat'] ?? '');
        if ($norm && $stat) {
            $index[$norm . '|' . $stat] = [
                'player'            => $p['player'],
                'stat'              => $stat,
                'fair_line'         => floatval($p['projection'] ?? 0),
                'model_prob_over'   => floatval($p['model_prob_over']  ?? 0.5),
                'model_prob_under'  => floatval($p['model_prob_under'] ?? 0.5),
                'market_prob_over'  => floatval($p['market_prob_over'] ?? 0.5),
                'market_prob_under' => floatval($p['market_prob_under'] ?? 0.5),
                'kelly_over'        => 0,
                'kelly_under'       => 0,
                'ev_over'           => 0,
                'ev_under'          => 0,
                'q_preds'           => [],
            ];
        }
    }
    return [$index, null, null];
}

[$modelIndex, $sideIndex, $predDate] = loadModelProjections($PRED_DIR, $GITHUB_RAW);

// ============================================================================
// LOAD MODEL-GENERATED SGPs (sgps_{date}.json)
// ============================================================================
function loadModelSGPs($predDir, $githubRaw, $date) {
    if (!$date) return [];
    $path = $predDir . 'sgps_' . $date . '.json';
    if (!file_exists($path)) return [];
    $raw = json_decode(file_get_contents($path), true);
    return $raw['sgps'] ?? [];
}
$modelSGPs = loadModelSGPs($PRED_DIR, $GITHUB_RAW, $predDate);

if (empty($modelIndex)) {
    echo json_encode([
        'error'      => 'Model predictions not yet available for today. Check back after 8AM EST.',
        'error_code' => 'no_predictions',
        'props'      => [], 'count' => 0, 'events' => 0,
        'live_games' => 0, 'status' => 'no_data',
        'retry_after' => 300,
    ]);
    exit;
}

// ============================================================================
// LOAD LIVE STATE (webhook receiver)
// ============================================================================

$liveStatePlayers  = [];
$liveStateGames    = [];
$liveStateInjuries = [];
$webhookEventCount = 0;

$lineupPlayers = [];  // player_id → on_court, starter, position

if (file_exists($LIVE_STATE)) {
    $ls = json_decode(file_get_contents($LIVE_STATE), true);
    if ($ls) {
        $liveStatePlayers  = $ls['players']  ?? [];
        $liveStateGames    = $ls['games']    ?? [];
        $liveStateInjuries = $ls['injuries'] ?? [];
        $webhookEventCount = $ls['event_count'] ?? 0;
        // Lineup poller writes lineup_players: player_id → on_court/starter/position
        $lineupPlayers     = $ls['lineup_players'] ?? [];
    }
}

// ============================================================================
// FETCH BDL LIVE BOX SCORES (60s fallback when webhook state is stale)
// ============================================================================

$liveBoxScores  = [];
$liveGamesCount = 0;

if ($BDL_API_KEY && in_array($MODE, ['live', 'auto'])) {
    $bdlLive = bdlApiGet("https://api.balldontlie.io/v1/box_scores/live", $BDL_API_KEY);
    if ($bdlLive && !empty($bdlLive['data'])) {
        foreach ($bdlLive['data'] as $entry) {
            $game   = $entry['game']   ?? [];
            $player = $entry['player'] ?? [];
            $period = intval($game['period'] ?? 0);
            $gameId = $game['id']     ?? null;

            if ($period > 0 && $gameId) $liveGamesCount++;

            $fn = $player['first_name'] ?? '';
            $ln = $player['last_name']  ?? '';
            if (!$fn || !$ln) continue;

            $norm   = normalizeName("$fn $ln");
            $minStr = $entry['min'] ?? '0';
            if (strpos($minStr, ':') !== false) {
                $p2 = explode(':', $minStr);
                $minPlayed = floatval($p2[0]) + floatval($p2[1] ?? 0) / 60.0;
            } else {
                $minPlayed = floatval($minStr);
            }

            $liveBoxScores[$norm] = [
                'pts'        => intval($entry['pts']  ?? 0),
                'reb'        => intval($entry['reb']  ?? 0),
                'ast'        => intval($entry['ast']  ?? 0),
                'fg3m'       => intval($entry['fg3m'] ?? 0),
                'stl'        => intval($entry['stl']  ?? 0),
                'blk'        => intval($entry['blk']  ?? 0),
                'tov'        => intval($entry['tov']  ?? 0),
                'fouls'      => intval($entry['pf']   ?? 0),
                'min_played' => round($minPlayed, 1),
                'period'     => $period,
                'clock'      => $game['time'] ?? '',
                'status'     => $game['status'] ?? '',
                'game_id'    => $gameId,
                'injured'    => false,
                'foul_trouble_level' => 'none',
            ];
        }
    }
}

// Webhook state wins (more real-time); BDL box score is fallback
$allLiveData  = array_merge($liveBoxScores, $liveStatePlayers);
$hasLiveGames = $liveGamesCount > 0 || !empty($liveStatePlayers);
if ($MODE === 'auto') $MODE = $hasLiveGames ? 'live' : 'pregame';

// ============================================================================
// FETCH POSTED ODDS — The Odds API
// ============================================================================

$MARKETS    = ['player_points','player_rebounds','player_assists',
               'player_threes','player_steals','player_blocks'];
$marketsStr = implode(',', $MARKETS);
$booksStr   = implode(',', array_keys($BOOK_NAMES));

$events = $ODDS_API_KEY
    ? (oddsApiGet("https://api.the-odds-api.com/v4/sports/basketball_nba/events?apiKey={$ODDS_API_KEY}") ?? [])
    : [];

$rawProps = [];

foreach ($events as $event) {
    $eid  = $event['id'];
    $home = $event['home_team'];
    $away = $event['away_team'];
    $game = "$away @ $home";
    $time = $event['commence_time'];

    $url = "https://api.the-odds-api.com/v4/sports/basketball_nba/events/{$eid}/odds?"
         . http_build_query([
               'apiKey'     => $ODDS_API_KEY,
               'regions'    => 'us,us2',
               'markets'    => $marketsStr,
               'oddsFormat' => 'american',
               'bookmakers' => $booksStr,
           ]);

    $data = oddsApiGet($url);
    if (!$data || empty($data['bookmakers'])) continue;

    // Best posted odds per player+stat+side across all books
    $bestOdds = [];

    foreach ($data['bookmakers'] as $bk) {
        $bookKey = $bk['key'];
        foreach ($bk['markets'] ?? [] as $mkt) {
            $statKey = $STAT_KEYS[$mkt['key']] ?? null;
            if (!$statKey) continue;

            $byPlayer = [];
            foreach ($mkt['outcomes'] ?? [] as $o) {
                $pName = $o['description'] ?? '';
                $side  = $o['name'] ?? '';
                if ($pName && $side) $byPlayer[$pName][$side] = $o;
            }

            foreach ($byPlayer as $pName => $sides) {
                if (!isset($sides['Over'])) continue;
                $oddsO = intval($sides['Over']['price']  ?? -110);
                $oddsU = intval($sides['Under']['price'] ?? -110);
                $line  = floatval($sides['Over']['point'] ?? 0);
                $pk    = $pName . '|' . $statKey;

                if (!isset($bestOdds[$pk])) {
                    $bestOdds[$pk] = [
                        'line'          => $line,
                        'player_name'   => $pName,
                        'stat'          => $statKey,
                        'game'          => $game,
                        'commence_time' => $time,
                        'over_odds'     => $oddsO,
                        'under_odds'    => $oddsU,
                        'over_book'     => $bookKey,
                        'under_book'    => $bookKey,
                    ];
                } else {
                    if (toDecimal($oddsO) > toDecimal($bestOdds[$pk]['over_odds'])) {
                        $bestOdds[$pk]['over_odds'] = $oddsO;
                        $bestOdds[$pk]['over_book'] = $bookKey;
                    }
                    if (toDecimal($oddsU) > toDecimal($bestOdds[$pk]['under_odds'])) {
                        $bestOdds[$pk]['under_odds'] = $oddsU;
                        $bestOdds[$pk]['under_book'] = $bookKey;
                    }
                }
            }
        }
    }

    // ── BUILD PROP ROWS ────────────────────────────────────────────────
    foreach ($bestOdds as $pk => $oddsData) {
        $pName   = $oddsData['player_name'];
        $statKey = $oddsData['stat'];
        $norm    = normalizeName($pName);
        $baseKey = $norm . '|' . $statKey;

        $model = $modelIndex[$baseKey] ?? null;
        if (!$model) {
            global $NAME_ALIASES;
            $alias = $NAME_ALIASES[$norm] ?? null;
            if ($alias) $model = $modelIndex[$alias . '|' . $statKey] ?? null;
        }
        if (!$model) continue;

        $line      = $oddsData['line'];
        $overOdds  = $oddsData['over_odds'];
        $underOdds = $oddsData['under_odds'];
        $overBook  = $oddsData['over_book'];
        $underBook = $oddsData['under_book'];

        // Probabilities from model
        $probOver  = floatval($model['model_prob_over']  ?? 0.5);
        $probUnder = floatval($model['model_prob_under'] ?? (1 - $probOver));
        $fairLine  = floatval($model['fair_line']        ?? 0);
        $qPreds    = $model['q_preds'] ?? [];

        // Kelly and raw EV from singles (side-specific, pre-computed by model)
        $kellyOver  = floatval($model['kelly_over']  ?? 0);
        $kellyUnder = floatval($model['kelly_under'] ?? 0);
        $evOver     = floatval($model['ev_over']     ?? 0);
        $evUnder    = floatval($model['ev_under']    ?? 0);

        // Market implied probs (vig-removed)
        $mktProbOver  = floatval($model['market_prob_over']  ?? 0.5);
        $mktProbUnder = floatval($model['market_prob_under'] ?? (1 - $mktProbOver));

        // Edge: model vs market implied (after vig removal)
        $decO  = toDecimal($overOdds);
        $decU  = toDecimal($underOdds);
        $edgeO = round($probOver  - (1.0 / $decO), 4);
        $edgeU = round($probUnder - (1.0 / $decU), 4);

        // Fair odds the model would set (= what we'd charge as the book)
        $fairOddsOver  = toAmerican($probOver);
        $fairOddsUnder = toAmerican($probUnder);

        // ── LIVE BLENDING (v2 engine) ──────────────────────────────────
        $liveData    = $allLiveData[$norm] ?? null;
        $gameStatus  = 'pre-game';
        $actual      = null;
        $minPlayed   = 0.0;
        $period      = 0;
        $clock       = '';
        $liveProj    = $fairLine;
        $foulCount   = 0;
        $foulLevel   = 'none';
        $isInjured   = false;
        $injuryAlert = '';
        $scoreMargin = 0;
        $isOT        = false;
        $liveAdj     = [];

        if (isset($liveStateInjuries[$norm])) {
            $injStatus = $liveStateInjuries[$norm]['status'] ?? '';
            if ($injStatus === 'out') {
                $isInjured   = true;
                $injuryAlert = 'OUT: ' . ($liveStateInjuries[$norm]['detail'] ?? 'Listed out');
            } elseif (in_array($injStatus, ['questionable', 'doubtful'])) {
                $injuryAlert = strtoupper($injStatus) . ': ' .
                               ($liveStateInjuries[$norm]['detail'] ?? '');
            }
        }

        if ($liveData && $MODE === 'live') {
            $gameStatus  = $liveData['status']     ?? 'in-progress';
            $actual      = floatval($liveData[$statKey] ?? 0);
            $minPlayed   = floatval($liveData['min_played'] ?? 0);
            $period      = intval($liveData['period'] ?? 0);
            $clock       = $liveData['clock']      ?? '';
            $foulCount   = intval($liveData['fouls'] ?? 0);
            $foulLevel   = $liveData['foul_trouble_level'] ?? 'none';
            $isInjured   = (bool)($liveData['injured'] ?? false);
            $gameId      = $liveData['game_id']    ?? null;
            $gameCtx     = $liveStateGames[$gameId] ?? [];
            $isOT        = (bool)($gameCtx['is_overtime'] ?? false);
            $scoreMargin = intval($gameCtx['score_margin'] ?? 0);

            // ── V5 playerState enrichment ─────────────────────────────────
            $liveData['is_star']        = ($fairLine >= 20.0 && $statKey === 'pts')
                                       || ($fairLine >= 7.0  && $statKey === 'reb')
                                       || ($fairLine >= 6.0  && $statKey === 'ast');
            $liveData['usage_pct']      = floatval($model['adv_usage'] ?? 0.22);
            $liveData['is_closer']      = $liveData['is_star'];
            $liveData['is_ball_handler']= in_array($statKey, ['pts','ast']);
            $liveData['star_teammate_on_court']    = true;
            $liveData['primary_creator_on_court']  = true;
            $liveData['lineup_usage_share']        = floatval($model['adv_usage'] ?? 0.22);
            $liveData['opp_defender_fouls']        = 0;
            $liveData['rim_defender_benched']      = false;
            $gameCtx['team_in_bonus']              = false;
            $gameCtx['opp_in_bonus']               = false;

            // ── On-court state from lineup poller (BDL /v1/lineups) ──────
            $playerId    = intval($model['player_id'] ?? 0);
            $lineupEntry = $playerId ? ($lineupPlayers[$playerId] ?? null) : null;
            $onCourt     = true; // default optimistic
            $isStarter   = false;
            if ($lineupEntry !== null) {
                $lineupAge = time() - intval($lineupEntry['last_seen'] ?? 0);
                if ($lineupAge < 600) { // only trust if <10 min old
                    $onCourt   = boolval($lineupEntry['on_court'] ?? true);
                    $isStarter = boolval($lineupEntry['starter']  ?? false);
                }
            }
            // Also check webhook on_court flag (play-by-play sub events)
            $webhookOnCourt = boolval($liveData['on_court'] ?? $liveData['on_court_flag'] ?? true);
            // Webhook overrides lineup if more recent
            $onCourt = $webhookOnCourt && $onCourt;

            // If player is confirmed off court, suppress projection
            if (!$onCourt && $minPlayed < 1.0) {
                // DNP — hasn't played yet and not in lineup
                continue; // skip this prop entirely
            }

            if ($isInjured) {
                $injuryAlert = 'INJURED: ' . ($liveStateInjuries[$norm]['detail'] ?? 'Injury reported');
            }

            if ($minPlayed > 0.5) {
                $minRem = estimateLiveMinutesRemaining($period, $clock, $isOT);
                $result = calcLiveProbabilityV5(
                    $fairLine, 36.0, $actual, $minPlayed, $minRem,
                    $line, $statKey, $liveData, $gameCtx
                );
                $probOver  = $result['prob'];
                $probUnder = 1.0 - $probOver;
                $liveProj  = $result['live_proj'];
                $liveAdj   = $result['adjustments'];
                // Recalc fair odds and edge from live-adjusted probs
                $fairOddsOver  = toAmerican($probOver);
                $fairOddsUnder = toAmerican($probUnder);
                $edgeO = round($probOver  - (1.0 / $decO), 4);
                $edgeU = round($probUnder - (1.0 / $decU), 4);
            }
        }

        // Recalc Kelly from live prob (caps at 25%)
        $kO = $decO > 1 ? max(0, min(0.25, (($decO-1)*$probOver  - (1-$probOver))  / ($decO-1))) : $kellyOver;
        $kU = $decU > 1 ? max(0, min(0.25, (($decU-1)*$probUnder - (1-$probUnder)) / ($decU-1))) : $kellyUnder;

        // Shared base row
        $baseRow = [
            'player'         => $pName,
            'stat'           => strtoupper($statKey),
            'stat_key'       => $statKey,
            'line'           => $line,
            'fair_line'      => $fairLine,       // MODEL P50: where we'd set the line
            'game'           => $game,
            'commence_time'  => $time,
            'projection'     => round($liveProj, 1),
            'q_preds'        => $qPreds,         // full quantile dist P10→P90
            'game_status'    => $gameStatus,
            'actual'         => $actual,
            'min_played'     => $minPlayed,
            'game_period'    => $period,
            'game_clock'     => $clock,
            'fouls'          => $foulCount,
            'foul_trouble'   => $foulLevel,
            'injured'        => $isInjured,
            'injury_alert'   => $injuryAlert,
            'score_margin'   => $scoreMargin,
            'is_overtime'    => $isOT,
            'live_adjustments' => !empty($liveAdj) ? $liveAdj : null,
        ];

        // OVER row
        $rawProps[] = array_merge($baseRow, [
            'side'           => 'OVER',
            'odds'           => $overOdds,           // posted market odds
            'book_key'       => $overBook,
            'book'           => $BOOK_NAMES[$overBook] ?? ucfirst($overBook),
            'model_prob'     => round($probOver, 4),  // model probability
            'market_prob'    => round($mktProbOver, 4), // market vig-removed prob
            'fair_odds'      => $fairOddsOver,         // OUR price (the key output)
            'model_odds'     => $fairOddsOver,
            'edge'           => $edgeO,
            'kelly'          => round($kO, 4),
            'ev'             => $evOver > 0 ? round($evOver, 4) : round($edgeO, 4),
        ]);

        // UNDER row
        $rawProps[] = array_merge($baseRow, [
            'side'           => 'UNDER',
            'odds'           => $underOdds,
            'book_key'       => $underBook,
            'book'           => $BOOK_NAMES[$underBook] ?? ucfirst($underBook),
            'model_prob'     => round($probUnder, 4),
            'market_prob'    => round($mktProbUnder, 4),
            'fair_odds'      => $fairOddsUnder,
            'model_odds'     => $fairOddsUnder,
            'edge'           => $edgeU,
            'kelly'          => round($kU, 4),
            'ev'             => $evUnder > 0 ? round($evUnder, 4) : round($edgeU, 4),
        ]);
    }
}

// ============================================================================
// TEAMMATE USAGE BOOST — mid-game injury redistributes usage
// ============================================================================

$injuredGames = [];
foreach ($liveStateInjuries as $injNorm => $injData) {
    if (($injData['status'] ?? '') !== 'out') continue;
    if ($gid = ($injData['game_id'] ?? null)) $injuredGames[$gid] = true;
}

if (!empty($injuredGames)) {
    foreach ($rawProps as &$prop) {
        if ($prop['game_status'] !== 'in-progress') continue;
        $propNorm = normalizeName($prop['player']);
        if (isset($liveStateInjuries[$propNorm])) continue;
        $propGameId = ($allLiveData[$propNorm] ?? [])['game_id'] ?? null;
        if ($propGameId && isset($injuredGames[$propGameId])) {
            $prop['projection'] = round($prop['projection'] * 1.06, 1);
            $prop['model_prob'] = $prop['side'] === 'OVER'
                ? min(0.97, round($prop['model_prob'] * 1.03, 4))
                : max(0.03, round($prop['model_prob'] * 0.97, 4));
            $prop['fair_odds']  = toAmerican($prop['model_prob']);
            $prop['model_odds'] = $prop['fair_odds'];
            $dec = toDecimal($prop['odds']);
            $prop['edge'] = round($prop['model_prob'] - (1.0 / $dec), 4);
            $prop['live_adjustments'] = array_merge(
                $prop['live_adjustments'] ?? [],
                ['teammate_injury_boost' => true]
            );
        }
    }
    unset($prop);
}

// ============================================================================
// SORT — by edge descending
// ============================================================================

usort($rawProps, fn($a, $b) => $b['edge'] <=> $a['edge']);

// ============================================================================
// COMPUTE PORTFOLIO METRICS for frontend display
// ============================================================================

$posEdge = array_filter($rawProps, fn($p) => $p['edge'] > 0 && $p['side'] === 'OVER');

$metrics = [
    'total_picks'    => count($rawProps) / 2,   // unique player+stat picks
    'positive_edge'  => count($posEdge),
    'avg_edge'       => count($posEdge) > 0
        ? round(array_sum(array_column(array_values($posEdge), 'edge')) / count($posEdge) * 100, 2)
        : 0,
    'avg_kelly'      => count($posEdge) > 0
        ? round(array_sum(array_column(array_values($posEdge), 'kelly')) / count($posEdge) * 100, 2)
        : 0,
    'max_edge'       => count($posEdge) > 0
        ? round(max(array_column(array_values($posEdge), 'edge')) * 100, 2)
        : 0,
    'pred_date'      => $predDate,
];

// ============================================================================
// OUTPUT
// ============================================================================

$liveCount = 0;
foreach ($rawProps as $p) {
    if ($p['game_status'] !== 'pre-game') $liveCount++;
}

$output = [
    'props'          => $rawProps,
    'model_sgps'     => $modelSGPs,
    'updated'        => date('c'),
    'count'          => count($rawProps),
    'events'         => count($events),
    'live_games'     => $liveGamesCount,
    'live_props'     => $liveCount,
    'mode'           => $MODE,
    'webhook_events' => $webhookEventCount,
    'injuries'       => array_values($liveStateInjuries),
    'metrics'        => $metrics,
    'status'         => empty($rawProps) ? 'no_props' : 'ok',
];

$cacheDir = dirname($CACHE_FILE);
if (!is_dir($cacheDir)) mkdir($cacheDir, 0755, true);
file_put_contents($CACHE_FILE, json_encode($output, JSON_PRETTY_PRINT));
echo json_encode($output);

// ============================================================================
// LIVE ENGINE v5 — Sprint 1: stat-specific trust + remainder model
// ============================================================================

// SECTION 1: CONSTANTS
// ═══════════════════════════════════════════════════════════════════════════

// ── Foul trouble minute reduction ─────────────────────────────────────────
const FOUL_MIN_FACTORS_V5 = [
    'none'       => 1.00,
    'mild'       => 0.90,
    'moderate'   => 0.72,
    'severe'     => 0.58,
    'fouled_out' => 0.00,
];

// ── P1: Stat-specific Bayesian prior weights ──────────────────────────────
// Higher = trust pregame longer = correct for noisy/sparse stats
// Interpretation: at minPlayed = weight, trust = 0.50
const BAYES_PRIOR_WEIGHTS_V5 = [
    'pts'  => 12.0,   // scoring is consistent — update moderately fast
    'reb'  => 16.0,   // rebounds need rebound-chance context to trust
    'ast'  => 16.0,   // assists depend on teammates — slower
    'fg3m' => 22.0,   // 3PM very sparse — attempts update faster than makes
    'fg3a' => 10.0,   // attempt rate is more stable than make rate
    'blk'  => 30.0,   // ultra-sparse — trust prior until ~30 min played
    'stl'  => 30.0,   // ultra-sparse
    'tov'  => 14.0,
    'pra'  => 12.0,
    'pr'   => 13.0,
    'pa'   => 13.0,
    'ra'   => 15.0,
];

// ── P1: Stat-specific pace factors ────────────────────────────────────────
// How much does live pace affect this stat's projection?
// 1.0 = full pace effect, 0.0 = no effect, shrink sparse stats toward 1.0
const PACE_SENSITIVITY_V5 = [
    'pts'  => 1.00,   // full: more possessions = more scoring
    'reb'  => 0.80,   // high: more misses = more boards, but position matters
    'ast'  => 0.70,   // moderate: pace creates ast opps but creation is role-driven
    'fg3m' => 0.60,   // moderate: more possessions but 3PA share is player-specific
    'blk'  => 0.15,   // very low: rim events per possession barely change with pace
    'stl'  => 0.15,   // very low: steal events per possession barely change with pace
    'tov'  => 0.50,
    'pra'  => 0.90,
    'pr'   => 0.85,
    'pa'   => 0.80,
    'ra'   => 0.70,
];

// ── Blowout thresholds — covers BOTH teams ────────────────────────────────
const BLOWOUT_THRESHOLDS_V5 = [
    ['margin'=>30,'period'=>3,'losing'=>0.35,'winning_star'=>0.80],
    ['margin'=>25,'period'=>3,'losing'=>0.50,'winning_star'=>0.85],
    ['margin'=>20,'period'=>3,'losing'=>0.65,'winning_star'=>0.92],
    ['margin'=>25,'period'=>4,'losing'=>0.30,'winning_star'=>0.70],
    ['margin'=>20,'period'=>4,'losing'=>0.45,'winning_star'=>0.78],
    ['margin'=>15,'period'=>4,'losing'=>0.65,'winning_star'=>0.88],
    ['margin'=>12,'period'=>4,'losing'=>0.80,'winning_star'=>0.94],
];

// ── Heat/cold detection ───────────────────────────────────────────────────
const HEAT_WINDOW_SEC_V5      = 480;    // 8-minute rolling window
const HEAT_MIN_ATTEMPTS       = 3;      // minimum attempts to detect heat
const HEAT_MAKE_RATE_THRESH   = 0.60;   // must make >= 60% in window
const HEAT_EXPECTED_DEVIATION = 0.15;   // must be >= 15pp above expected rate
const COLD_MAKE_RATE_THRESH   = 0.20;   // making <= 20% = cold
const COLD_EXPECTED_DEVIATION = 0.15;   // must be >= 15pp below expected rate
const COLD_MIN_ATTEMPTS       = 3;

// ── Clutch window ────────────────────────────────────────────────────────
const CLUTCH_MARGIN    = 6;     // within 6 = clutch
const CLUTCH_TIME_REM  = 5.0;   // last 5 minutes of Q4

// ── Base CV per stat (full-game, pre-narrowing) ───────────────────────────
const BASE_CV_V5 = [
    'pts'  => 0.35,
    'reb'  => 0.45,
    'ast'  => 0.50,
    'fg3m' => 0.65,
    'blk'  => 0.90,
    'stl'  => 0.85,
    'tov'  => 0.60,
    'pra'  => 0.30,
    'pr'   => 0.32,
    'pa'   => 0.32,
    'ra'   => 0.38,
];

// ── Variance shrink speed per stat ────────────────────────────────────────
// How fast does uncertainty narrow as game progresses?
// 1.0 = fully narrows by game end, 0.5 = retains 50% of original uncertainty
const VARIANCE_SHRINK_SPEED = [
    'pts'  => 0.85,   // fast: pts is consistent, narrows quickly
    'reb'  => 0.80,
    'ast'  => 0.78,
    'fg3m' => 0.70,   // slower: fg3m has higher variance even late
    'blk'  => 0.50,   // slow: sparse events stay uncertain longer
    'stl'  => 0.50,
    'tov'  => 0.70,
    'pra'  => 0.85,
    'pr'   => 0.83,
    'pa'   => 0.82,
    'ra'   => 0.78,
];


// ═══════════════════════════════════════════════════════════════════════════
// SECTION 2: LIVE FEATURES EXTRACTION
// Builds the complete live feature vector from raw inputs
// ═══════════════════════════════════════════════════════════════════════════

/**
 * buildLiveFeatureVector
 * ──────────────────────
 * Extracts all live features from raw game/player state.
 * This is the live equivalent of build_v19_features() in Python.
 * Call this BEFORE the stat-specific update engines.
 */
function buildLiveFeatureVector(
    array $playerState,
    array $gameState,
    array $pick,            // pregame prediction record
    float $minPlayed,
    float $minRemBase
): array {
    $f = [];

    // ── P1: Minutes remaining engine ────────────────────────────────────────
    $f['min_played']       = $minPlayed;
    $f['min_rem_base']     = $minRemBase;
    $f['game_progress']    = $minPlayed / max($minPlayed + $minRemBase, 1.0);
    $f['period']           = intval($playerState['period'] ?? 1);
    $f['is_ot']            = $f['period'] > 4 ? 1 : 0;

    // Live minute remainder model
    $minEst = estimateLiveMinutesRemaining($playerState, $gameState, $minRemBase, $pick);
    $f['live_min_rem_q25'] = $minEst['q25'];
    $f['live_min_rem_q50'] = $minEst['q50'];
    $f['live_min_rem_q75'] = $minEst['q75'];
    $f['currently_on_court']         = floatval($playerState['on_court'] ?? 1);
    $f['rotation_pattern_score']     = floatval($playerState['rotation_pattern_match_score'] ?? 0.5);
    $f['coach_closing_probability']  = floatval($playerState['coach_closing_prob'] ?? 0.5);
    $f['opened_half_flag']           = floatval($playerState['opened_half'] ?? 0);
    $f['closed_last_quarter_flag']   = floatval($playerState['closed_last_q'] ?? 0);

    // ── Game script ──────────────────────────────────────────────────────────
    $f['score_margin']      = abs(floatval($gameState['score_margin'] ?? 0));
    $f['raw_score_margin']  = floatval($gameState['score_margin'] ?? 0);
    $f['is_losing_team']    = isOnLosingTeam($playerState, $gameState) ? 1 : 0;
    $f['is_winning_team']   = 1 - $f['is_losing_team'];
    $f['is_home']           = floatval($playerState['home_flag'] ?? 0);

    // Blowout and garbage time risk
    $f['garbage_time_risk']           = computeGarbageTimeRisk($f['score_margin'], $f['period'], $minRemBase);
    $f['blowout_pull_forward_risk']   = $f['garbage_time_risk'] * $f['is_winning_team'];
    $f['winning_team_star_rest_risk'] = $f['garbage_time_risk'] * floatval($playerState['is_star'] ?? 0);

    // ── Player role state ────────────────────────────────────────────────────
    $f['is_star']         = floatval($playerState['is_star'] ?? 0);
    $f['usage_pct']       = floatval($playerState['usage_pct'] ?? 0.18);
    $f['foul_level']      = $playerState['foul_trouble_level'] ?? 'none';
    $f['foul_factor']     = FOUL_MIN_FACTORS_V5[$f['foul_level']] ?? 1.0;
    $f['fouls_drawn']     = intval($playerState['fouls_drawn'] ?? 0);
    $f['live_pf']         = intval($playerState['pf'] ?? 0);

    // Foul-out risk by period
    $foulThresholds = [1=>2, 2=>3, 3=>4, 4=>5];
    $foulThresh = $foulThresholds[$f['period']] ?? 6;
    $f['foul_trouble_flag']   = ($f['live_pf'] >= $foulThresh) ? 1 : 0;
    $f['fouls_until_trouble'] = max(0, $foulThresh - $f['live_pf']);

    // ── Foul environment (P4) ─────────────────────────────────────────────
    $f['opp_defender_foul_trouble']  = floatval($playerState['opp_defender_fouls'] ?? 0);
    $f['rim_defender_on_bench']      = floatval($playerState['rim_defender_benched'] ?? 0);
    $f['team_in_bonus']              = floatval($gameState['team_in_bonus'] ?? 0);
    $f['opp_in_bonus']               = floatval($gameState['opp_in_bonus'] ?? 0);

    // ── Lineup / on-court state (P2) ─────────────────────────────────────
    $f['star_teammate_on_court']     = floatval($playerState['star_teammate_on_court'] ?? 1);
    $f['primary_creator_on_court']   = floatval($playerState['primary_creator_on_court'] ?? 1);
    $f['starting_center_on_court']   = floatval($playerState['starting_center_on_court'] ?? 1);
    $f['small_ball_lineup']          = floatval($playerState['small_ball_lineup'] ?? 0);
    $f['bench_unit_flag']            = floatval($playerState['bench_unit'] ?? 0);
    $f['current_lineup_usage_share'] = floatval($playerState['lineup_usage_share'] ?? $f['usage_pct']);
    $f['current_lineup_reb_share']   = floatval($playerState['lineup_reb_share'] ?? 0.20);
    $f['current_lineup_ast_share']   = floatval($playerState['lineup_ast_share'] ?? 0.20);

    // ── Clutch window (P3) ────────────────────────────────────────────────
    $f['is_clutch_window']     = ($f['period'] >= 4 && $f['score_margin'] <= CLUTCH_MARGIN && $minRemBase <= CLUTCH_TIME_REM) ? 1 : 0;
    $f['is_late_game_closer']  = floatval($playerState['is_closer'] ?? $f['is_star']);
    $f['late_game_ball_handler']= floatval($playerState['late_game_ball_handler'] ?? ($f['usage_pct'] >= 0.25 ? 1 : 0));
    $f['clutch_usage_boost']   = computeClutchBoost($f['is_clutch_window'], $f['is_star'], $f['late_game_ball_handler']);
    $f['clutch_min_boost']     = ($f['is_clutch_window'] && $f['is_late_game_closer']) ? 1.05 : 1.0;

    // ── Overtime probability (P3) ─────────────────────────────────────────
    $otEst = computeOTProbability($f['score_margin'], $f['period'], $minRemBase);
    $f['ot_probability']      = $otEst['prob'];
    $f['expected_ot_minutes'] = $otEst['exp_minutes'];

    // ── Pace (P1) ─────────────────────────────────────────────────────────
    $f['live_pace_factor'] = computeLivePaceFactor($gameState);

    return $f;
}


// ═══════════════════════════════════════════════════════════════════════════
// SECTION 3: LIVE OPPORTUNITY STATE FEATURES (P2)
// Per-stat live opportunity and conversion tracking
// ═══════════════════════════════════════════════════════════════════════════

/**
 * buildLiveOpportunityFeatures
 * ─────────────────────────────
 * Extracts per-stat opportunity and conversion features from live box score.
 * This separates "how many chances" from "how many conversions" — the right split.
 *
 * Opportunity features update fast (FGA rate is stable early).
 * Conversion features update slow (FG% on 3 shots is noise).
 */
function buildLiveOpportunityFeatures(
    string $stat,
    array $playerState,     // live box score data for this player
    float $minPlayed
): array {
    $f = [];
    $minS = max($minPlayed, 0.1);

    switch ($stat) {

        case 'pts':
            // Opportunity: how many shots/FTAs is he generating per minute?
            $f['live_fga']          = floatval($playerState['fga'] ?? 0);
            $f['live_fgm']          = floatval($playerState['fgm'] ?? 0);
            $f['live_3pa']          = floatval($playerState['fg3a'] ?? 0);
            $f['live_3pm']          = floatval($playerState['fg3m'] ?? 0);
            $f['live_fta']          = floatval($playerState['fta'] ?? 0);
            $f['live_ftm']          = floatval($playerState['ftm'] ?? 0);
            // Opportunity rates
            $f['live_fga_rate']     = $f['live_fga'] / $minS;
            $f['live_fta_rate']     = $f['live_fta'] / $minS;
            $f['live_3pa_rate']     = $f['live_3pa'] / $minS;
            // Conversion — trust slowly (use shrinkage-style blend)
            $f['live_fg_pct']       = $f['live_fga'] > 2 ? $f['live_fgm'] / $f['live_fga'] : null;
            $f['live_3p_pct']       = $f['live_3pa'] > 2 ? $f['live_3pm'] / $f['live_3pa'] : null;
            $f['live_ft_pct']       = $f['live_fta'] > 2 ? $f['live_ftm'] / $f['live_fta'] : null;
            // Live drives (if available from event feed)
            $f['live_drives']       = floatval($playerState['drives'] ?? 0);
            $f['live_touch_rate']   = floatval($playerState['touches'] ?? 0) / $minS;
            break;

        case 'reb':
            $f['live_reb_chances']  = floatval($playerState['reb_chances'] ?? 0);
            $f['live_oreb_chances'] = floatval($playerState['oreb_chances'] ?? 0);
            $f['live_dreb_chances'] = floatval($playerState['dreb_chances'] ?? 0);
            $f['live_oreb']         = floatval($playerState['oreb'] ?? 0);
            $f['live_dreb']         = floatval($playerState['dreb'] ?? 0);
            // Opportunity rates
            $f['live_reb_chance_rate']  = $f['live_reb_chances'] / $minS;
            // Conversion: reb / reb_chances (when available)
            $f['live_reb_conv_rate']    = $f['live_reb_chances'] > 2
                ? floatval($playerState['reb'] ?? 0) / $f['live_reb_chances']
                : null;
            // Miss volume from game context
            $f['live_miss_volume']  = floatval($playerState['live_miss_volume'] ?? 0);
            break;

        case 'ast':
            $f['live_potential_ast']    = floatval($playerState['potential_assists'] ?? 0);
            $f['live_passes']           = floatval($playerState['passes'] ?? 0);
            $f['live_touches']          = floatval($playerState['touches'] ?? 0);
            $f['live_time_of_poss']     = floatval($playerState['time_of_possession'] ?? 0);
            // Opportunity rates
            $f['live_potential_ast_rate'] = $f['live_potential_ast'] / $minS;
            $f['live_pass_rate']          = $f['live_passes'] / $minS;
            // Conversion: ast / potential_ast
            $f['live_ast_conv_rate']      = $f['live_potential_ast'] > 2
                ? floatval($playerState['ast'] ?? 0) / $f['live_potential_ast']
                : null;
            break;

        case 'fg3m':
            $f['live_3pa']              = floatval($playerState['fg3a'] ?? 0);
            $f['live_3pm']              = floatval($playerState['fg3m'] ?? 0);
            $f['live_catch_shoot_3pa']  = floatval($playerState['cs_3pa'] ?? 0);
            $f['live_pullup_3pa']       = floatval($playerState['pullup_3pa'] ?? 0);
            // Opportunity rates — update attempt rate fast
            $f['live_3pa_rate']         = $f['live_3pa'] / $minS;
            // Conversion — trust slowly (3P% is noisy on small samples)
            $f['live_3p_pct']           = $f['live_3pa'] > 3
                ? $f['live_3pm'] / $f['live_3pa']
                : null;
            break;

        case 'blk':
            $f['live_rim_defense_events']  = floatval($playerState['rim_defense_events'] ?? 0);
            $f['live_contested_shots']     = floatval($playerState['contested_2pt'] ?? 0);
            $f['live_blk']                 = floatval($playerState['blk'] ?? 0);
            $f['live_rim_event_rate']      = $f['live_rim_defense_events'] / $minS;
            // Conversion
            $f['live_blk_conv_rate']       = $f['live_rim_defense_events'] > 1
                ? $f['live_blk'] / $f['live_rim_defense_events']
                : null;
            break;

        case 'stl':
            $f['live_live_ball_tov_env']   = floatval($playerState['opp_live_ball_tov_rate'] ?? 0);
            $f['live_deflections']         = floatval($playerState['deflections'] ?? 0);
            $f['live_stl']                 = floatval($playerState['stl'] ?? 0);
            $f['live_deflection_rate']     = $f['live_deflections'] / $minS;
            break;
    }

    return $f;
}


// ═══════════════════════════════════════════════════════════════════════════
// SECTION 4: STAT-SPECIFIC LIVE UPDATE ENGINES (P1 + P2)
// Each stat family has its own trust curve, pace treatment, remainder model
// ═══════════════════════════════════════════════════════════════════════════

/**
 * computeRemainderProjection
 * ───────────────────────────
 * Models the REMAINDER distribution, not the full-game revision.
 * final_stat = actual + remainder
 * Returns: [mean_remainder, sd_remainder, trust_opportunity, trust_conversion]
 */
function computeRemainderProjection(
    string $stat,
    float $pregameProj,
    float $pregameMin,
    float $actual,
    float $minPlayed,
    array $liveFeatures,
    array $oppFeatures,
    array $liveCounts = []
): array {

    $minRem         = $liveFeatures['live_min_rem_q50'] ?? $liveFeatures['min_rem_base'];
    $gameProgress   = $liveFeatures['game_progress'];
    $paceFactor     = 1.0 + ($liveFeatures['live_pace_factor'] - 1.0) * (PACE_SENSITIVITY_V5[$stat] ?? 0.5);
    $priorWeight    = BAYES_PRIOR_WEIGHTS_V5[$stat] ?? 15.0;

    // ── Pregame rates ────────────────────────────────────────────────────────
    $pregameRate = $pregameProj / max($pregameMin, 1.0);

    // ── Stat-specific opportunity/conversion split ────────────────────────────
    switch ($stat) {

        case 'pts':
            // Split: update FGA rate (opportunity) fast, FG% (conversion) slow
            $liveFgaRate  = $liveCounts['live_fga_rate'] ?? ($actual / max($minPlayed, 0.1) / 1.1);
            $liveFtaRate  = $liveCounts['live_fta_rate'] ?? 0;
            $pregameFgaRate = ($pregameProj / 2.0) / max($pregameMin, 1.0);  // approx

            // Opportunity trust: update faster (shot volume stabilizes quickly)
            $oppTrust = min(0.90, $minPlayed / ($minPlayed + ($priorWeight * 0.6)));
            // Conversion trust: update slower (efficiency noisy on small FGA)
            $convTrust = min(0.80, $minPlayed / ($minPlayed + ($priorWeight * 1.5)));

            // Blended opportunity rate
            $blendedFgaRate = (1 - $oppTrust) * $pregameFgaRate + $oppTrust * $liveFgaRate;

            // Use live FG% only if sample is meaningful
            $liveFgPct = $liveCounts['live_fg_pct'] ?? null;
            $pregameFgPct = 0.46;  // league avg as prior
            $fgPct = ($liveFgPct !== null)
                ? (1 - $convTrust) * $pregameFgPct + $convTrust * $liveFgPct
                : $pregameFgPct;

            $ptsPerFga  = $fgPct * 2.2;  // rough pts per FGA including 3PM value
            $ftContrib  = ($liveFtaRate * max(0.75, $liveCounts['live_ft_pct'] ?? 0.75)) ?? 0;
            $remRate    = ($blendedFgaRate * $ptsPerFga + $ftContrib) * $paceFactor;

            // Clutch boost for stars in close Q4
            $remRate *= $liveFeatures['clutch_usage_boost'] ?? 1.0;
            break;

        case 'reb':
            // Split: update rebound-chance rate (opportunity) fast,
            //        conversion rate (reb/chance) slower
            $liveRebChanceRate = $liveCounts['live_reb_chance_rate'] ?? null;
            $pregameRebRate    = $pregameProj / max($pregameMin, 1.0);

            $oppTrust  = min(0.90, $minPlayed / ($minPlayed + ($priorWeight * 0.7)));
            $convTrust = min(0.80, $minPlayed / ($minPlayed + ($priorWeight * 1.2)));

            if ($liveRebChanceRate !== null && $liveRebChanceRate > 0) {
                $blendedChanceRate = (1 - $oppTrust) * ($pregameRebRate * 1.3) + $oppTrust * $liveRebChanceRate;
                $liveConvRate  = $liveCounts['live_reb_conv_rate'] ?? 0.65;
                $pregameConv   = 0.65;
                $convRate      = (1 - $convTrust) * $pregameConv + $convTrust * $liveConvRate;
                $remRate       = $blendedChanceRate * $convRate * $paceFactor;
            } else {
                // Fallback: standard blended rate
                $liveRebRate = $actual / max($minPlayed, 0.1);
                $trust       = $minPlayed / ($minPlayed + $priorWeight);
                $remRate     = ((1 - $trust) * $pregameRebRate + $trust * $liveRebRate) * $paceFactor;
            }

            // Lineup: if starting center is on bench, reb opportunity changes
            $remRate *= (1.0 + ($liveFeatures['current_lineup_reb_share'] - 0.20) * 0.5);
            break;

        case 'ast':
            // Split: update pass/touch rate (opportunity) fast,
            //        ast/potential_ast conversion slower
            $livePotAstRate   = $liveCounts['live_potential_ast_rate'] ?? null;
            $pregameAstRate   = $pregameProj / max($pregameMin, 1.0);

            $oppTrust  = min(0.85, $minPlayed / ($minPlayed + ($priorWeight * 0.65)));
            $convTrust = min(0.75, $minPlayed / ($minPlayed + ($priorWeight * 1.4)));

            if ($livePotAstRate !== null && $livePotAstRate > 0) {
                // Scale potential_ast rate to expected actual assists
                $pregamePotAstRate = $pregameAstRate * 1.6;  // potential:actual ~1.6:1
                $blendedPotRate    = (1 - $oppTrust) * $pregamePotAstRate + $oppTrust * $livePotAstRate;
                $liveConvRate      = $liveCounts['live_ast_conv_rate'] ?? 0.62;
                $convRate          = (1 - $convTrust) * 0.62 + $convTrust * $liveConvRate;
                $remRate           = $blendedPotRate * $convRate * $paceFactor;
            } else {
                $liveAstRate = $actual / max($minPlayed, 0.1);
                $trust       = $minPlayed / ($minPlayed + $priorWeight);
                $remRate     = ((1 - $trust) * $pregameAstRate + $trust * $liveAstRate) * $paceFactor;
            }

            // Creator on court affects ast ceiling
            if (!$liveFeatures['primary_creator_on_court'] && $liveFeatures['usage_pct'] < 0.25) {
                $remRate *= 1.15;  // secondary creator gets more creation when primary is out
            }
            $remRate *= $liveFeatures['clutch_usage_boost'] ?? 1.0;
            break;

        case 'fg3m':
            // CRITICAL SPLIT: update 3PA rate (attempt vol) fast,
            //                  3P% (conversion) very slowly
            $live3paRate     = $liveCounts['live_3pa_rate'] ?? null;
            $live3pPct       = $liveCounts['live_3p_pct'] ?? null;
            $pregame3paRate  = $pregameProj > 0 ? ($pregameProj / max($pregameMin, 1.0)) / 0.36 : 0;
            $pregame3pPct    = 0.36;  // Bayesian prior for 3P%

            // Attempt rate (opportunity): trust faster
            $attTrust  = min(0.85, $minPlayed / ($minPlayed + (BAYES_PRIOR_WEIGHTS_V5['fg3a'] ?? 10.0)));
            // Make rate (conversion): trust very slowly
            $convTrust = min(0.70, $minPlayed / ($minPlayed + ($priorWeight * 1.6)));

            $blended3paRate = ($live3paRate !== null)
                ? (1 - $attTrust) * $pregame3paRate + $attTrust * $live3paRate
                : $pregame3paRate;

            $blended3pPct = ($live3pPct !== null)
                ? (1 - $convTrust) * $pregame3pPct + $convTrust * $live3pPct
                : $pregame3pPct;

            $remRate = $blended3paRate * $blended3pPct * $paceFactor;
            break;

        case 'blk':
            // Ultra-sparse: trust prior very long, use rim defense events as opportunity
            $liveRimRate  = $liveCounts['live_rim_event_rate'] ?? null;
            $liveBlkConv  = $liveCounts['live_blk_conv_rate'] ?? null;
            $pregameBlkRate = $pregameProj / max($pregameMin, 1.0);

            // Opportunity trust: very slow (30-min prior weight)
            $oppTrust  = min(0.70, $minPlayed / ($minPlayed + $priorWeight));
            $convTrust = min(0.50, $minPlayed / ($minPlayed + ($priorWeight * 2.0)));

            if ($liveRimRate !== null && $liveRimRate > 0) {
                $pregameRimRate    = $pregameBlkRate * 4.0;  // ~4 rim events per block
                $blendedRimRate    = (1 - $oppTrust) * $pregameRimRate + $oppTrust * $liveRimRate;
                $blendedConvRate   = ($liveBlkConv !== null)
                    ? (1 - $convTrust) * 0.25 + $convTrust * $liveBlkConv
                    : 0.25;
                $remRate = $blendedRimRate * $blendedConvRate;
                // Opponent rim attack rate matters (not pace per se)
                $rimDefOnBench = $liveFeatures['rim_defender_on_bench'] ?? 0;
                $remRate *= (1.0 + $rimDefOnBench * 0.20);
            } else {
                $liveBlkRate = $actual / max($minPlayed, 0.1);
                $trust       = $minPlayed / ($minPlayed + $priorWeight);
                $remRate     = (1 - $trust) * $pregameBlkRate + $trust * $liveBlkRate;
                // NOTE: pace NOT applied to blk
            }
            break;

        case 'stl':
            // Ultra-sparse: deflection rate as opportunity signal
            $liveDefRate    = $liveCounts['live_deflection_rate'] ?? null;
            $pregameStlRate = $pregameProj / max($pregameMin, 1.0);
            $trust          = min(0.65, $minPlayed / ($minPlayed + $priorWeight));

            if ($liveDefRate !== null && $liveDefRate > 0) {
                $pregameDefRate   = $pregameStlRate * 5.0;  // ~5 deflections per steal
                $blendedDefRate   = (1 - $trust) * $pregameDefRate + $trust * $liveDefRate;
                $remRate          = $blendedDefRate * 0.20;  // ~20% deflection-to-steal conv
                // Opponent live-ball TOV environment
                $tovEnv    = $liveCounts['live_live_ball_tov_env'] ?? 0;
                $remRate  *= (1.0 + $tovEnv * 0.10);
            } else {
                $liveStlRate = $actual / max($minPlayed, 0.1);
                $remRate     = (1 - $trust) * $pregameStlRate + $trust * $liveStlRate;
                // NOTE: pace NOT applied to stl
            }
            break;

        default:
            // Combo props: standard blended rate
            $pregameRate2 = $pregameProj / max($pregameMin, 1.0);
            $liveRate     = $actual / max($minPlayed, 0.1);
            $trust        = $minPlayed / ($minPlayed + ($priorWeight));
            $remRate      = ((1 - $trust) * $pregameRate2 + $trust * $liveRate) * $paceFactor;
            break;
    }

    // ── Blowout minute adjustment ─────────────────────────────────────────────
    $blowoutFactor = computeBlowoutFactor(
        $liveFeatures['score_margin'],
        $liveFeatures['period'],
        $liveFeatures['is_losing_team'],
        $liveFeatures['is_star']
    );
    $adjMinRem = $minRem * $blowoutFactor * $liveFeatures['foul_factor']
                 * ($liveFeatures['clutch_min_boost'] ?? 1.0);

    // ── OT minutes bonus ──────────────────────────────────────────────────────
    $adjMinRem += $liveFeatures['expected_ot_minutes'] ?? 0;

    $meanRemainder = $remRate * $adjMinRem;

    // ── Dynamic variance narrowing ────────────────────────────────────────────
    $shrinkSpeed  = VARIANCE_SHRINK_SPEED[$stat] ?? 0.75;
    $varRetained  = max(0.15, 1.0 - $gameProgress * $shrinkSpeed);
    $baseCv       = BASE_CV_V5[$stat] ?? 0.45;
    $liveCv       = $baseCv * $varRetained;
    $sdRemainder  = max(0.3, $meanRemainder * $liveCv);

    return [
        'mean_remainder'  => $meanRemainder,
        'sd_remainder'    => $sdRemainder,
        'adj_min_rem'     => $adjMinRem,
        'rem_rate'        => $remRate,
        'var_retained'    => $varRetained,
        'live_cv'         => $liveCv,
        'blowout_factor'  => $blowoutFactor,
    ];
}


// ═══════════════════════════════════════════════════════════════════════════
// SECTION 5: MAIN LIVE PROBABILITY ENGINE V5
// ═══════════════════════════════════════════════════════════════════════════

/**
 * calcLiveProbabilityV5
 * ─────────────────────
 * Complete live prop probability engine.
 * Drop-in replacement for calcLiveProbabilityV3/V4.
 */
function calcLiveProbabilityV5(
    float $pregameProj,
    float $pregameMin,
    float $actual,
    float $minPlayed,
    float $minRemBase,
    float $line,
    string $stat,
    array $playerState = [],
    array $gameState = [],
    array $qPreds = []
): array {

    $adj = [];

    // ── Terminal states ────────────────────────────────────────────────────
    if ($actual > $line)
        return ['prob'=>0.97,'live_proj'=>$actual,'method'=>'terminal_over',
                'adjustments'=>['already_over'=>true]];
    if (($playerState['foul_trouble_level'] ?? '') === 'fouled_out')
        return ['prob'=>0.03,'live_proj'=>$actual,'method'=>'terminal_fouledout',
                'adjustments'=>['fouled_out'=>true]];
    if ($playerState['injured'] ?? false)
        return ['prob'=>0.03,'live_proj'=>$actual,'method'=>'terminal_injured',
                'adjustments'=>['injured'=>true]];
    if ($minRemBase < 0.5)
        return ['prob'=>($actual > $line) ? 0.97 : 0.03,'live_proj'=>$actual,
                'method'=>'terminal_gameover','adjustments'=>['game_over'=>true]];

    // Pre-tip: use pregame distribution directly
    if ($minPlayed < 0.5) {
        if (!empty($qPreds)) {
            $prob = queryQuantileDistribution($qPreds, $line);
        } else {
            $adjProj = $pregameProj * ($minRemBase / max($pregameMin, 1.0));
            $prob    = calcStatProbFromCVDynamic($adjProj, $line, $stat, 0.0);
        }
        return ['prob'=>$prob,'live_proj'=>round($pregameProj,1),
                'method'=>'pregame_dist','adjustments'=>['pre_game'=>true]];
    }

    // ── Build complete live feature vector ────────────────────────────────
    $lf = buildLiveFeatureVector($playerState, $gameState, [], $minPlayed, $minRemBase);

    // ── Build per-stat opportunity features ───────────────────────────────
    $oppF = buildLiveOpportunityFeatures($stat, $playerState, $minPlayed);

    // ── Compute remainder projection ──────────────────────────────────────
    $rem = computeRemainderProjection(
        $stat, $pregameProj, $pregameMin, $actual,
        $minPlayed, $lf, [], $oppF
    );

    $liveProj = $actual + $rem['mean_remainder'];

    $adj['remainder'] = [
        'mean'          => round($rem['mean_remainder'], 2),
        'sd'            => round($rem['sd_remainder'], 2),
        'adj_min_rem'   => round($rem['adj_min_rem'], 2),
        'rem_rate'      => round($rem['rem_rate'], 3),
        'var_retained'  => round($rem['var_retained'], 3),
        'blowout_factor'=> round($rem['blowout_factor'], 3),
    ];

    // ── Validated heat/cold detection (P3) ───────────────────────────────
    $heatMult = computeValidatedHeatCold($stat, $playerState, $lf['game_progress'], $pregameProj, $pregameMin);
    $liveProj *= $heatMult;
    if (abs($heatMult - 1.0) > 0.02)
        $adj['heat_cold'] = ['multiplier' => round($heatMult, 3)];

    // ── Probability from remainder distribution ───────────────────────────
    $needed = $line - $actual;  // remaining stat needed to hit line

    if (!empty($qPreds) && $pregameProj > 0) {
        // Shift pregame quantile distribution by (liveProj / pregameProj)
        // AND narrow variance by var_retained
        $distRatio = $liveProj / max($pregameProj, 0.1);
        $q50       = $qPreds[0.5] ?? $pregameProj;
        $shiftedQ  = [];
        $varRetained = $rem['var_retained'];

        foreach ($qPreds as $tau => $qVal) {
            $shifted  = floatval($qVal) * $distRatio;
            $shifted50= $q50 * $distRatio;
            $dev      = $shifted - $shifted50;
            $shiftedQ[$tau] = max(0.0, $shifted50 + $dev * $varRetained);
        }
        $prob = queryQuantileDistribution($shiftedQ, $needed);
        $adj['method'] = 'quantile_shift_v5_narrowed';

    } else {
        // Fallback: dynamic CV normal approximation
        $prob = calcStatProbFromCVDynamic($liveProj, $line, $stat, $lf['game_progress']);
        $adj['method'] = 'normal_approx_v5_dynamic';
    }

    $prob = max(0.02, min(0.98, $prob));

    // ── Log key diagnostic signals ────────────────────────────────────────
    $adj['live_features'] = [
        'game_progress'       => round($lf['game_progress'], 3),
        'garbage_time_risk'   => round($lf['garbage_time_risk'], 3),
        'ot_prob'             => round($lf['ot_probability'], 3),
        'is_clutch'           => $lf['is_clutch_window'],
        'clutch_boost'        => round($lf['clutch_usage_boost'], 3),
        'foul_trouble'        => $lf['foul_level'],
        'lineup_usage_share'  => round($lf['current_lineup_usage_share'], 3),
        'star_teammate_on_court' => $lf['star_teammate_on_court'],
        'opp_defender_fouls'  => $lf['opp_defender_foul_trouble'],
        'team_in_bonus'       => $lf['team_in_bonus'],
    ];

    return [
        'prob'        => $prob,
        'live_proj'   => round($liveProj, 1),
        'method'      => 'bayesian_v5',
        'adjustments' => $adj,
    ];
}


// ═══════════════════════════════════════════════════════════════════════════
// SECTION 6: HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * estimateLiveMinutesRemaining
 * ─────────────────────────────
 * P1: True live minute-remaining engine with rotation awareness.
 * Returns q25/q50/q75 distribution of remaining minutes.
 */
function estimateLiveMinutesRemaining(
    array $playerState,
    array $gameState,
    float $minRemBase,
    array $pick = []
): array {
    $period   = intval($playerState['period'] ?? 1);
    $onCourt  = boolval($playerState['on_court'] ?? true);
    $isStar   = boolval($playerState['is_star'] ?? false);
    $isCloser = boolval($playerState['is_closer'] ?? $isStar);
    $foulFactor = FOUL_MIN_FACTORS_V5[$playerState['foul_trouble_level'] ?? 'none'] ?? 1.0;
    $margin   = abs(floatval($gameState['score_margin'] ?? 0));

    // Base: clock-derived minutes remaining
    $base = $minRemBase;

    // Adjust for whether currently on court
    if (!$onCourt) {
        // Player is on bench — expected return window
        $lastSubTime = floatval($playerState['last_sub_time'] ?? 0);
        $typicalBenchStretch = 4.0;  // avg bench stretch
        $expectedReturn = max(0.0, $typicalBenchStretch - (time() - $lastSubTime) / 60.0);
        $base = max(0.0, $base - $expectedReturn);
    }

    // Rotation pattern adjustment
    $rotationScore = floatval($playerState['rotation_pattern_match_score'] ?? 0.5);
    $base *= (0.85 + $rotationScore * 0.30);  // 0.85 to 1.15

    // Foul trouble
    $base *= $foulFactor;

    // Closer bonus in clutch situations
    if ($isCloser && $period >= 4 && $margin <= 8) {
        $base = min($base * 1.10, $minRemBase);
    }

    // Uncertainty: wider early in game, narrower late
    $gameProgress = 1.0 - ($minRemBase / 48.0);
    $uncertainty  = max(0.5, 3.0 * (1.0 - $gameProgress));
    $q25 = max(0.0, $base - $uncertainty);
    $q75 = min($minRemBase, $base + $uncertainty);

    return [
        'q25' => round($q25, 1),
        'q50' => round($base, 1),
        'q75' => round($q75, 1),
    ];
}


/**
 * computeValidatedHeatCold
 * ─────────────────────────
 * P3: Heat/cold detection with make-rate and deviation-from-expectation.
 * Applies regression-to-mean so boost/penalty decay with trust level.
 */
function computeValidatedHeatCold(
    string $stat,
    array $playerState,
    float $gameProgress,
    float $pregameProj,
    float $pregameMin
): float {
    if (!in_array($stat, ['pts', 'fg3m'])) return 1.0;

    $now    = time();
    $shots  = $playerState['shot_events'] ?? [];
    if (empty($shots)) return 1.0;

    $recentShots = array_filter($shots, fn($e) => ($e['ts'] ?? 0) > ($now - HEAT_WINDOW_SEC_V5));
    $count = count($recentShots);
    if ($count < HEAT_MIN_ATTEMPTS) return 1.0;

    $makes     = array_filter($recentShots, fn($e) => ($e['made'] ?? false) === true);
    $makeRate  = count($makes) / $count;

    // Expected make rate from pregame model
    $expectedMakeRate = ($stat === 'pts') ? 0.46 : 0.36;  // league avg priors
    $deviation = $makeRate - $expectedMakeRate;

    // Trust level determines how much we adjust (regression to mean)
    // Low trust early = weaker heat/cold adjustment
    $priorWeight = BAYES_PRIOR_WEIGHTS_V5[$stat] ?? 20.0;
    $trust = min(0.80, ($count * 5.0) / (($count * 5.0) + $priorWeight));

    if ($makeRate >= HEAT_MAKE_RATE_THRESH && $deviation >= HEAT_EXPECTED_DEVIATION) {
        // Validated heat
        $maxBoost = ($stat === 'fg3m') ? 1.10 : 1.07;
        $boost    = 1.0 + ($maxBoost - 1.0) * $trust * (1.0 - $gameProgress);
        return $boost;
    } elseif ($makeRate <= COLD_MAKE_RATE_THRESH && $deviation <= -COLD_EXPECTED_DEVIATION
              && $count >= COLD_MIN_ATTEMPTS) {
        // Validated cold — regression to mean applies
        $maxPenalty = ($stat === 'fg3m') ? 0.88 : 0.93;
        $penalty    = 1.0 - (1.0 - $maxPenalty) * $trust * (1.0 - $gameProgress);
        return $penalty;
    }

    return 1.0;
}


/**
 * computeBlowoutFactor
 * ─────────────────────
 * Covers BOTH winning and losing team minute suppression.
 */
function computeBlowoutFactor(
    float $margin,
    int $period,
    int $isLosingTeam,
    float $isStar
): float {
    foreach (BLOWOUT_THRESHOLDS_V5 as $t) {
        if ($margin >= $t['margin'] && $period >= $t['period']) {
            if ($isLosingTeam) return $t['losing'];
            if ($isStar)       return $t['winning_star'];
        }
    }
    return 1.0;
}


/**
 * computeGarbageTimeRisk
 * ───────────────────────
 */
function computeGarbageTimeRisk(float $margin, int $period, float $minRem): float {
    if ($margin < 12 || $period < 3) return 0.0;
    $marginScore = min(1.0, ($margin - 12) / 20.0);
    $timeScore   = min(1.0, ($period - 2) / 2.0);
    $timeLeft    = min(1.0, max(0.0, 1.0 - $minRem / 24.0));
    return round($marginScore * $timeScore * $timeLeft, 3);
}


/**
 * computeClutchBoost
 * ───────────────────
 */
function computeClutchBoost(int $isClutch, float $isStar, float $isBallHandler): float {
    if (!$isClutch) return 1.0;
    $boost = 1.0;
    if ($isStar)        $boost += 0.06;  // stars get more touches
    if ($isBallHandler) $boost += 0.04;  // ball handlers get more isolation
    return min(1.12, $boost);
}


/**
 * computeOTProbability
 * ─────────────────────
 */
function computeOTProbability(float $margin, int $period, float $minRem): array {
    if ($period < 4 || $margin > CLUTCH_MARGIN || $minRem > CLUTCH_TIME_REM) {
        return ['prob' => 0.0, 'exp_minutes' => 0.0];
    }
    $marginFactor = max(0.0, (CLUTCH_MARGIN - $margin) / CLUTCH_MARGIN);
    $timeFactor   = max(0.0, 1.0 - $minRem / CLUTCH_TIME_REM);
    $otProb       = min(0.40, $marginFactor * $timeFactor * 0.40);
    return [
        'prob'        => round($otProb, 3),
        'exp_minutes' => round($otProb * 5.0, 2),
    ];
}


/**
 * computeLivePaceFactor
 * ──────────────────────
 */
function computeLivePaceFactor(array $gameState): float {
    $paceEvents = $gameState['pace_events'] ?? [];
    if (count($paceEvents) < 4) return 1.0;
    $recent  = array_slice($paceEvents, -8);
    $first   = $recent[0];
    $last    = end($recent);
    $elapsed = $last['ts'] - $first['ts'];
    $scored  = $last['score'] - $first['score'];
    if ($elapsed <= 45 || $scored <= 0) return 1.0;
    $livePossMin = ($scored / $elapsed * 60) / 2.2;
    return min(1.40, max(0.70, $livePossMin / (100.0 / 48.0)));
}


/**
 * calcStatProbFromCVDynamic
 * ──────────────────────────
 * Dynamic CV that narrows as game progresses.
 */
function calcStatProbFromCVDynamic(
    float $proj,
    float $line,
    string $stat,
    float $gameProgress
): float {
    $baseCv      = BASE_CV_V5[$stat] ?? 0.45;
    $shrinkSpeed = VARIANCE_SHRINK_SPEED[$stat] ?? 0.75;
    $cvMult      = max(0.15, 1.0 - $gameProgress * $shrinkSpeed);
    $cv          = $baseCv * $cvMult;
    $sd          = max(0.5, $proj * $cv);
    return max(0.01, min(0.99, 1.0 - normalCDF(($line - $proj) / $sd)));
}


/**
 * buildLiveLadderV5
 * ──────────────────
 * Enhanced live ladder with variance narrowing and stat-specific step.
 */
function buildLiveLadderV5(
    float $liveProj,
    float $postedLine,
    string $stat,
    array $qPreds,
    float $pregameProj,
    float $gameProgress = 0.0
): array {
    $step        = in_array($stat, ['pts','pra','pr','pa']) ? 1.0 : 0.5;
    $shrinkSpeed = VARIANCE_SHRINK_SPEED[$stat] ?? 0.75;
    $varRetained = max(0.15, 1.0 - $gameProgress * $shrinkSpeed);
    $ladder      = [];

    for ($i = 0; $i <= 10; $i++) {
        $l = round($postedLine + ($i - 5) * $step, 1);
        if ($l < 0) continue;

        if (!empty($qPreds) && $pregameProj > 0) {
            $ratio   = $liveProj / max($pregameProj, 0.1);
            $q50     = $qPreds[0.5] ?? $pregameProj;
            $shifted = [];
            foreach ($qPreds as $tau => $val) {
                $s   = floatval($val) * $ratio;
                $s50 = $q50 * $ratio;
                $dev = $s - $s50;
                $shifted[$tau] = max(0.0, $s50 + $dev * $varRetained);
            }
            $po = queryQuantileDistribution($shifted, $l);
        } else {
            $po = calcStatProbFromCVDynamic($liveProj, $l, $stat, $gameProgress);
        }

        $pu = 1.0 - $po;
        $ladder[] = [
            'line'       => $l,
            'prob_over'  => round($po, 4),
            'prob_under' => round($pu, 4),
            'fair_over'  => toAmerican($po),
            'fair_under' => toAmerican($pu),
            'posted'     => abs($l - $postedLine) < 0.01,
        ];
    }
    return $ladder;
}


// ═══════════════════════════════════════════════════════════════════════════
// SECTION 7: LIVE BET-SELECTION LAYER (SEPARATE FROM PROJECTION)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * computeLiveBetSelection
 * ────────────────────────
 * Separate from projection — determines WHETHER to bet a live prop.
 * Do NOT mix this into the projection engine.
 *
 * Inputs: updated live projection + current book line
 * Outputs: edge, recommendation, confidence, stale-line flag
 */
function computeLiveBetSelection(
    float $liveProj,
    float $modelProb,
    float $currentBookLine,
    float $openingLine,
    string $stat,
    string $side,           // 'over' or 'under'
    array $liveFeatures,
    float $gameProgress
): array {

    // ── Edge vs current live line ─────────────────────────────────────────
    $projEdge = ($side === 'over')
        ? $liveProj - $currentBookLine
        : $currentBookLine - $liveProj;

    // ── Stale line detection ──────────────────────────────────────────────
    // If the live book line hasn't moved but game state has changed materially,
    // the book may be slow — this is where live edge comes from
    $staleFlag = false;
    $lineMovedFromOpen = $currentBookLine - $openingLine;
    $expectedMove = 0.0;

    if ($liveFeatures['garbage_time_risk'] > 0.40 && abs($lineMovedFromOpen) < 0.5) {
        $staleFlag    = true;  // book hasn't priced garbage time yet
        $expectedMove = -2.0; // line should have moved down for over
    }
    if ($liveFeatures['is_clutch_window'] && $liveFeatures['is_star'] && abs($lineMovedFromOpen) < 0.5) {
        $staleFlag    = true;  // book hasn't priced clutch usage spike
        $expectedMove = +1.5;
    }

    // ── Per-stat, per-side thresholds ─────────────────────────────────────
    // Thresholds tighten late in game (less time = less variance = need more edge)
    $baseThresholds = [
        'pts'  => ['over'=>0.60,'under'=>0.75],
        'reb'  => ['over'=>0.60,'under'=>0.73],
        'ast'  => ['over'=>0.60,'under'=>0.75],
        'fg3m' => ['over'=>0.58,'under'=>0.73],
        'blk'  => ['over'=>0.56,'under'=>0.73],
        'stl'  => ['over'=>0.60,'under'=>0.75],
    ];
    $base      = $baseThresholds[$stat][$side] ?? 0.65;
    // Tighten threshold late in game — less time = less room for error
    $threshold = $base + ($gameProgress * 0.04);

    $recommend  = $modelProb >= $threshold;
    $edgeVsVig  = $modelProb - $threshold;

    // ── Confidence tier ───────────────────────────────────────────────────
    $confidence = 'low';
    if ($edgeVsVig >= 0.10) $confidence = 'high';
    elseif ($edgeVsVig >= 0.05) $confidence = 'medium';

    return [
        'recommend'          => $recommend,
        'model_prob'         => round($modelProb, 4),
        'threshold'          => round($threshold, 4),
        'edge_vs_vig'        => round($edgeVsVig, 4),
        'proj_edge'          => round($projEdge, 2),
        'confidence'         => $confidence,
        'stale_line_flag'    => $staleFlag,
        'expected_line_move' => $expectedMove,
        'game_progress'      => round($gameProgress, 3),
    ];
}

/**
 * =============================================================================
