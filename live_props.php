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

if (file_exists($LIVE_STATE)) {
    $ls = json_decode(file_get_contents($LIVE_STATE), true);
    if ($ls) {
        $liveStatePlayers  = $ls['players']  ?? [];
        $liveStateGames    = $ls['games']    ?? [];
        $liveStateInjuries = $ls['injuries'] ?? [];
        $webhookEventCount = $ls['event_count'] ?? 0;
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

            if ($isInjured) {
                $injuryAlert = 'INJURED: ' . ($liveStateInjuries[$norm]['detail'] ?? 'Injury reported');
            }

            if ($minPlayed > 0.5) {
                $minRem = estimateMinRemainingV2($period, $clock, $isOT);
                $result = calcLiveProbabilityV2(
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
// LIVE ENGINE v2
// ============================================================================

const FOUL_MIN_FACTORS = [
    'none'=>1.00,'mild'=>0.90,'moderate'=>0.72,'severe'=>0.58,'fouled_out'=>0.00
];
const BLOWOUT_THRESHOLDS = [
    ['margin'=>30,'period'=>3,'factor'=>0.35],['margin'=>25,'period'=>3,'factor'=>0.50],
    ['margin'=>20,'period'=>3,'factor'=>0.65],['margin'=>25,'period'=>4,'factor'=>0.30],
    ['margin'=>20,'period'=>4,'factor'=>0.45],['margin'=>15,'period'=>4,'factor'=>0.65],
    ['margin'=>12,'period'=>4,'factor'=>0.80],
];
const HEAT_WINDOW_SEC  = 240;
const HEAT_MIN_SHOTS   = 3;
const HEAT_BOOST_PTS   = 1.12;
const HEAT_BOOST_3PT   = 1.18;

// Bayesian prior weight: equivalent "prior game minutes" of trust in pregame model.
// At 15 min played, trust = 15/(15+15) = 50/50. At 30 min played, trust = 67% in-game.
// This is materially slower than linear extrapolation — correct for stat variance.
const BAYES_PRIOR_WEIGHT = 15.0;

/**
 * calcLiveProbabilityV3 — Bayesian Quantile Distribution Update
 * ==============================================================
 * Core principle: the pregame model outputs a full Q10–Q90 distribution,
 * not a point estimate. Live updating should shift the ENTIRE distribution
 * based on observed evidence, then re-query P(stat > line) from that
 * updated distribution. This is fundamentally different from projecting
 * a final number and computing a normal CDF around it.
 *
 * Algorithm:
 * 1. Parse pregame Q10–Q90 into a piecewise linear CDF
 * 2. Compute Bayesian trust weight from minutes played
 * 3. Shift the distribution mean by the rate evidence (in-game vs pregame rate)
 * 4. Apply context factors (foul trouble, blowout, pace, heat)
 * 5. Query the shifted distribution at the sportsbook line
 *
 * This correctly handles:
 * - Blowout shrinkage: shifts distribution DOWN, doesn't just truncate
 * - Hot hand: shifts distribution UP proportionally across all quantiles
 * - Minutes uncertainty: wide distribution → less confident update
 */
function calcLiveProbabilityV3(float $pregameProj, float $pregameMin, float $actual,
    float $minPlayed, float $minRemBase, float $line, string $stat,
    array $playerState=[], array $gameState=[], array $qPreds=[]): array {

    $adj = [];

    // ── Terminal states ────────────────────────────────────────────────────────
    if ($actual > $line)
        return ['prob'=>0.97,'live_proj'=>$actual,'method'=>'terminal_over','adjustments'=>['already_over'=>true]];
    if (($playerState['foul_trouble_level']??'') === 'fouled_out')
        return ['prob'=>0.03,'live_proj'=>$actual,'method'=>'terminal_fouledout','adjustments'=>['fouled_out'=>true]];
    if ($playerState['injured']??false)
        return ['prob'=>0.03,'live_proj'=>$actual,'method'=>'terminal_injured','adjustments'=>['injured'=>true]];
    if ($minRemBase < 0.5)
        return ['prob'=>($actual>$line)?0.97:0.03,'live_proj'=>$actual,'method'=>'terminal_gameover','adjustments'=>['game_over'=>true]];
    if ($minPlayed < 0.5) {
        // Pre-tip: use pregame distribution directly
        if (!empty($qPreds)) {
            $prob = queryQuantileDistribution($qPreds, $line);
        } else {
            $adjProj = $pregameProj * ($minRemBase / max($pregameMin, 1.0));
            $prob = calcStatProbFromCV($adjProj, $line, $stat);
        }
        return ['prob'=>$prob,'live_proj'=>round($pregameProj,1),'method'=>'pregame_dist','adjustments'=>['pre_game'=>true]];
    }

    // ── Context factors ────────────────────────────────────────────────────────
    // 1. Foul trouble → projected minutes reduction
    $foulFactor = FOUL_MIN_FACTORS[$playerState['foul_trouble_level']??'none'] ?? 1.0;
    $minRem = $minRemBase * $foulFactor;
    if ($foulFactor < 1.0) $adj['foul_trouble'] = ['level'=>$playerState['foul_trouble_level'],'factor'=>$foulFactor];

    // 2. Live pace adjustment
    $paceFactor = 1.0;
    $paceEvents = $gameState['pace_events'] ?? [];
    if (count($paceEvents) >= 4) {
        $recent  = array_slice($paceEvents, -8);
        $first   = $recent[0]; $last = end($recent);
        $elapsed = $last['ts'] - $first['ts'];
        $scored  = $last['score'] - $first['score'];
        if ($elapsed > 45 && $scored > 0) {
            $livePossMin = ($scored / $elapsed * 60) / 2.2;
            $paceFactor  = min(1.40, max(0.70, $livePossMin / (100.0/48.0)));
            if (abs($paceFactor - 1.0) > 0.05)
                $adj['live_pace'] = ['factor'=>round($paceFactor,3)];
        }
    }

    // 3. Blowout garbage time
    $blowoutFactor = 1.0;
    $margin = $gameState['score_margin'] ?? 0;
    $period = $playerState['period'] ?? 1;
    if ($margin > 0) {
        foreach (BLOWOUT_THRESHOLDS as $t) {
            if ($margin >= $t['margin'] && $period >= $t['period']) {
                if (isOnLosingTeam($playerState, $gameState)) {
                    $blowoutFactor = $t['factor'];
                    $adj['blowout'] = ['margin'=>$margin,'factor'=>$blowoutFactor];
                    break;
                }
            }
        }
    }
    $minRem *= $blowoutFactor;

    // ── Bayesian update of distribution mean ───────────────────────────────────
    // trust = fraction of evidence weight given to observed in-game rate.
    // At minPlayed=0: trust=0 (pure prior). At minPlayed=BAYES_PRIOR_WEIGHT: trust=0.5.
    $pregameRate = $pregameProj / max($pregameMin, 1.0);
    $inGameRate  = $actual / max($minPlayed, 0.1);
    $trust       = $minPlayed / ($minPlayed + BAYES_PRIOR_WEIGHT);
    $blendedRate = ((1 - $trust) * $pregameRate + $trust * $inGameRate) * $paceFactor;

    $projRem  = $blendedRate * $minRem;
    $liveProj = $actual + $projRem;
    $adj['bayesian'] = [
        'trust'         => round($trust, 3),
        'blended_rate'  => round($blendedRate, 3),
        'proj_remaining'=> round($projRem, 2),
    ];

    // 5. Heat detection (pts, fg3m only)
    $heatBoost = 1.0;
    if (in_array($stat, ['pts','fg3m'])) {
        $now      = time();
        $shots    = $playerState['shot_events'] ?? [];
        $hotShots = array_filter($shots, fn($e) => ($e['ts']??0) > ($now - HEAT_WINDOW_SEC));
        if (count($hotShots) >= HEAT_MIN_SHOTS) {
            $heatBoost = ($stat==='fg3m') ? HEAT_BOOST_3PT : HEAT_BOOST_PTS;
            $adj['heat'] = ['shots_in_window'=>count($hotShots),'boost'=>$heatBoost];
        }
    }
    $liveProj *= $heatBoost;

    // ── Probability from shifted distribution ──────────────────────────────────
    // If we have the pregame quantile distribution, shift it by the ratio of
    // liveProj / pregameProj and query P(total > line) from the shifted CDF.
    // This preserves the shape of the distribution (variance, skew) while
    // updating the location parameter — far superior to a fixed-CV normal CDF.
    if (!empty($qPreds) && $pregameProj > 0) {
        $distRatio = $liveProj / max($pregameProj, 0.1);
        // Build shifted quantile distribution
        $shiftedQ = [];
        foreach ($qPreds as $tau => $qVal) {
            $shiftedQ[$tau] = max(0.0, $qVal * $distRatio);
        }
        $prob = queryQuantileDistribution($shiftedQ, $line - $actual);
        $adj['method'] = 'quantile_shift';
    } else {
        // Fallback: normal approximation with stat-specific CV
        $prob = calcStatProbFromCV($liveProj, $line, $stat);
        $adj['method'] = 'normal_approx';
    }

    $prob = max(0.02, min(0.98, $prob));
    return ['prob'=>$prob,'live_proj'=>round($liveProj,1),'method'=>'bayesian_v3','adjustments'=>$adj];
}

/**
 * queryQuantileDistribution — piecewise linear CDF interpolation
 * Queries P(X > threshold) from a quantile distribution.
 * Identical algorithm to the Python inference engine.
 */
function queryQuantileDistribution(array $qPreds, float $threshold): float {
    if (empty($qPreds)) return 0.5;

    // Sort by quantile value
    asort($qPreds);
    $taus = array_keys($qPreds);
    $vals = array_values($qPreds);
    $n    = count($vals);

    // Below all quantiles: probability ≈ 1.0 (certain to exceed)
    if ($threshold <= $vals[0]) return min(0.98, 1.0 - (float)$taus[0]);
    // Above all quantiles: probability ≈ 0.0
    if ($threshold >= $vals[$n-1]) return max(0.02, 1.0 - (float)$taus[$n-1]);

    // Linear interpolation between bracketing quantiles
    for ($i = 0; $i < $n - 1; $i++) {
        if ($vals[$i] <= $threshold && $threshold < $vals[$i+1]) {
            $frac = ($threshold - $vals[$i]) / max($vals[$i+1] - $vals[$i], 1e-9);
            $tau  = (float)$taus[$i] + $frac * ((float)$taus[$i+1] - (float)$taus[$i]);
            return max(0.02, min(0.98, 1.0 - $tau));
        }
    }
    return 0.5;
}

/**
 * calcStatProbFromCV — fallback normal approximation
 * Used when quantile distribution is unavailable.
 */
function calcStatProbFromCV(float $proj, float $line, string $stat): float {
    $cv = ['pts'=>0.35,'reb'=>0.45,'ast'=>0.50,'fg3m'=>0.65,'stl'=>0.80,'blk'=>0.90,'tov'=>0.60][$stat] ?? 0.45;
    $sd = max(0.5, $proj * $cv);
    return max(0.01, min(0.99, 1.0 - normalCDF(($line - $proj) / $sd)));
}

// Legacy alias — keeps existing call sites working
function calcLiveProbabilityV2(float $pregameProj, float $pregameMin, float $actual,
    float $minPlayed, float $minRemBase, float $line, string $stat,
    array $playerState=[], array $gameState=[]): array {
    return calcLiveProbabilityV3($pregameProj, $pregameMin, $actual,
        $minPlayed, $minRemBase, $line, $stat, $playerState, $gameState, []);
}

function estimateMinRemainingV2(int $period, string $clock, bool $isOT=false): float {
    $clockMin = 0.0;
    if ($clock && strpos($clock,':') !== false) {
        $p2 = explode(':',$clock);
        $clockMin = floatval($p2[0]) + floatval($p2[1]??0)/60.0;
    } elseif (is_numeric($clock)) {
        $clockMin = floatval($clock);
    }
    if ($period <= 0) return 48.0;
    if ($isOT || $period > 4) return max(0.0, $clockMin + 5.0);
    return max(0.0, (4-$period)*12.0 + $clockMin);
}

function calcStatProb(float $proj, float $line, string $stat): float {
    return calcStatProbFromCV($proj, $line, $stat);
}

function normalCDF(float $z): float {
    if ($z < -7.0) return 0.0;
    if ($z >  7.0) return 1.0;
    $sign = ($z>=0)?1:-1;
    $z = abs($z);
    $t = 1.0/(1.0+0.2316419*$z);
    $poly = $t*(0.319381530+$t*(-0.356563782+$t*(1.781477937+$t*(-1.821255978+$t*1.330274429))));
    $pdf  = exp(-0.5*$z*$z)/sqrt(2*M_PI);
    $cdf  = 1.0 - $pdf*$poly;
    return ($sign===1)?$cdf:1.0-$cdf;
}

function isOnLosingTeam(array $playerState, array $gameState): bool {
    $homeScore = $gameState['home_score'] ?? 0;
    $awayScore = $gameState['away_score'] ?? 0;
    $isHome    = $playerState['home_flag'] ?? null;
    if ($isHome===null) return false;
    $myScore  = $isHome ? $homeScore : $awayScore;
    $oppScore = $isHome ? $awayScore : $homeScore;
    return $myScore < $oppScore;
}
