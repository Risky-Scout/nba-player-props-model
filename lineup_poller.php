<?php
/**
 * lineup_poller.php — BDL Lineup State Poller
 *
 * Polls GET https://api.balldontlie.io/v1/lineups?game_ids[]=<id>
 * every 60 seconds for all live/today games and merges on-court state
 * into cache/live_state.json so live_props_v5.php knows who is on court.
 *
 * Run via cron every 60 seconds during game hours (6 PM – 1 AM ET):
 *   * * * * * php /path/to/lineup_poller.php >> /tmp/lineup_poller.log 2>&1
 *
 * Or trigger manually:
 *   php lineup_poller.php
 *
 * Requires config.php with:
 *   define('BDL_API_KEY', 'your_key');
 */

require_once __DIR__ . '/config.php';

$CACHE_DIR  = __DIR__ . '/cache';
$LIVE_STATE = $CACHE_DIR . '/live_state.json';
$POLL_LOG   = $CACHE_DIR . '/lineup_poll.log';

if (!is_dir($CACHE_DIR)) mkdir($CACHE_DIR, 0755, true);

$apiKey = defined('BDL_API_KEY') ? BDL_API_KEY : '';
if (!$apiKey) {
    log_msg("ERROR: BDL_API_KEY not defined in config.php");
    exit(1);
}

// ── 1. Get today's game IDs from BDL ──────────────────────────────────────
$today    = date('Y-m-d');
$gameIds  = fetch_game_ids($apiKey, $today);

if (empty($gameIds)) {
    log_msg("No games found for {$today} — exiting");
    exit(0);
}

log_msg("Found " . count($gameIds) . " games: " . implode(', ', $gameIds));

// ── 2. Fetch lineups for all live games ───────────────────────────────────
$lineupData = fetch_lineups($apiKey, $gameIds);

if (empty($lineupData)) {
    log_msg("No lineup data returned (games may not have started yet)");
    exit(0);
}

log_msg("Lineup entries: " . count($lineupData));

// ── 3. Load existing live state ───────────────────────────────────────────
$lockFile = $CACHE_DIR . '/.state.lock';
$lock     = fopen($lockFile, 'w');
if (!flock($lock, LOCK_EX | LOCK_NB)) {
    log_msg("Could not acquire state lock — skipping poll");
    fclose($lock);
    exit(0);
}

$state = [];
if (file_exists($LIVE_STATE)) {
    $state = json_decode(file_get_contents($LIVE_STATE), true) ?: [];
}

// ── 4. Build on-court map from lineup data ────────────────────────────────
// BDL lineups returns all players for a game (starters + bench)
// We only track who is confirmed in the lineup for this game
// Since BDL /v1/lineups shows the starting lineup, we mark all returned
// players as potentially on court, using game_id for context

$onCourtByGame = []; // game_id => [ player_id => ['starter'=>bool, 'position'=>str] ]

foreach ($lineupData as $entry) {
    $gameId   = intval($entry['game_id'] ?? 0);
    $playerId = intval($entry['player']['id'] ?? 0);
    $starter  = boolval($entry['starter'] ?? false);
    $position = $entry['position'] ?? '';
    $teamId   = intval($entry['team']['id'] ?? 0);

    if (!$gameId || !$playerId) continue;

    if (!isset($onCourtByGame[$gameId])) {
        $onCourtByGame[$gameId] = [];
    }
    $onCourtByGame[$gameId][$playerId] = [
        'starter'    => $starter,
        'position'   => $position,
        'team_id'    => $teamId,
        'last_seen'  => time(),
    ];
}

// ── 5. Merge into live state ──────────────────────────────────────────────
if (!isset($state['lineups'])) {
    $state['lineups'] = [];
}
if (!isset($state['players'])) {
    $state['players'] = [];
}

$state['lineup_poll_ts']    = time();
$state['lineup_poll_date']  = $today;
$state['lineup_game_ids']   = $gameIds;

foreach ($onCourtByGame as $gameId => $players) {
    $state['lineups'][$gameId] = [
        'players'    => $players,
        'updated_at' => time(),
        'player_count' => count($players),
    ];
}

// Build player_id → on_court lookup used by live_props_v5.php
// A player is "on_court" if they appear in today's lineup data
$allLineupPlayerIds = [];
foreach ($onCourtByGame as $gameId => $players) {
    foreach ($players as $pid => $info) {
        $allLineupPlayerIds[$pid] = [
            'game_id'   => $gameId,
            'starter'   => $info['starter'],
            'position'  => $info['position'],
            'team_id'   => $info['team_id'],
            'on_court'  => true,  // present in lineup = confirmed in rotation
            'last_seen' => $info['last_seen'],
        ];
    }
}

$state['lineup_players'] = $allLineupPlayerIds;

// ── 6. Write updated state ────────────────────────────────────────────────
file_put_contents($LIVE_STATE, json_encode($state, JSON_PRETTY_PRINT));
flock($lock, LOCK_UN);
fclose($lock);

log_msg("State updated. " . count($allLineupPlayerIds) . " players in lineup.");

// ────────────────────────────────────────────────────────────────────────────
// FUNCTIONS
// ────────────────────────────────────────────────────────────────────────────

/**
 * Fetch today's NBA game IDs from BDL.
 * GET https://api.balldontlie.io/v1/games?dates[]=YYYY-MM-DD
 */
function fetch_game_ids(string $apiKey, string $date): array {
    $url = "https://api.balldontlie.io/v1/games?" . http_build_query([
        'dates[]' => $date,
        'per_page' => 15,
    ]);

    $response = bdl_get($url, $apiKey);
    if (!$response || empty($response['data'])) {
        return [];
    }

    $ids = [];
    foreach ($response['data'] as $game) {
        // Only include games that have started or are in progress
        $status = $game['status'] ?? '';
        $period = intval($game['period'] ?? 0);
        // status is a time string for upcoming games, or "1st Qtr" etc for live
        // period > 0 means game has started
        if ($period > 0 || in_array($status, ['Final', '1st Qtr', '2nd Qtr', 'Halftime', '3rd Qtr', '4th Qtr'])) {
            $ids[] = intval($game['id']);
        }
    }

    return $ids;
}

/**
 * Fetch lineup data for given game IDs.
 * GET https://api.balldontlie.io/v1/lineups?game_ids[]=<id>&game_ids[]=<id>
 *
 * From BDL docs: Lineup data only available starting from 2025 NBA season
 * and only once the game begins.
 */
function fetch_lineups(string $apiKey, array $gameIds): array {
    if (empty($gameIds)) return [];

    // Build query string with multiple game_ids[] params
    $params = [];
    foreach ($gameIds as $gid) {
        $params[] = 'game_ids[]=' . intval($gid);
    }
    $params[] = 'per_page=100';
    $url = 'https://api.balldontlie.io/v1/lineups?' . implode('&', $params);

    $response = bdl_get($url, $apiKey);
    if (!$response || empty($response['data'])) {
        return [];
    }

    return $response['data'];
}

/**
 * Generic BDL GET with curl.
 */
function bdl_get(string $url, string $apiKey): ?array {
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT        => 10,
        CURLOPT_HTTPHEADER     => [
            'Authorization: ' . $apiKey,
            'Accept: application/json',
        ],
    ]);
    $body = curl_exec($ch);
    $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $err  = curl_error($ch);
    curl_close($ch);

    if ($err) {
        log_msg("CURL error: {$err}");
        return null;
    }
    if ($code !== 200) {
        log_msg("BDL returned HTTP {$code} for: {$url}");
        return null;
    }

    $data = json_decode($body, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        log_msg("JSON parse error: " . json_last_error_msg());
        return null;
    }

    return $data;
}

/**
 * Simple timestamped logger.
 */
function log_msg(string $msg): void {
    $line = '[' . date('Y-m-d H:i:s') . '] ' . $msg . PHP_EOL;
    echo $line;
    global $POLL_LOG;
    file_put_contents($POLL_LOG, $line, FILE_APPEND);
}
