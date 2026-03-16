<?php
/**
 * live_props_v5_lineup_patch.php
 *
 * PATCH INSTRUCTIONS for live_props_v5.php
 *
 * This file documents the exact changes needed to wire live_state.json
 * lineup data into live_props_v5.php.
 *
 * THREE CHANGES NEEDED:
 *
 * ─────────────────────────────────────────────────────────────────────────
 * CHANGE 1: Add state file reader near top of live_props_v5.php
 * (after any require/include statements, before main logic)
 * ─────────────────────────────────────────────────────────────────────────
 *
 * ADD THIS BLOCK:
 */

// ── Load live lineup state from webhook/poller cache ─────────────────────
$LIVE_STATE_PATH = __DIR__ . '/cache/live_state.json';
$liveState       = [];
$lineupPlayers   = [];

if (file_exists($LIVE_STATE_PATH)) {
    $raw = json_decode(file_get_contents($LIVE_STATE_PATH), true);
    if (is_array($raw)) {
        $liveState     = $raw;
        $lineupPlayers = $raw['lineup_players'] ?? [];
    }
}

/**
 * ─────────────────────────────────────────────────────────────────────────
 * CHANGE 2: Build playerState with real on_court value
 *
 * Find where playerState is assembled before calling computeLiveProbability
 * and replace the hardcoded on_court default with lineup lookup:
 * ─────────────────────────────────────────────────────────────────────────
 *
 * REPLACE this pattern:
 *   $playerState['on_court'] = true;   // hardcoded
 *
 * WITH:
 */

function buildOnCourtState(int $playerId, array $lineupPlayers): array {
    $entry = $lineupPlayers[$playerId] ?? null;

    if ($entry === null) {
        // Player not in lineup data — could be game not started yet
        // Default to true (optimistic) but flag as unconfirmed
        return [
            'on_court'           => true,
            'on_court_confirmed' => false,
            'starter'            => false,
            'position'           => '',
            'lineup_available'   => false,
        ];
    }

    // Stale check: if lineup was last seen > 10 minutes ago, treat as uncertain
    $stale = (time() - intval($entry['last_seen'] ?? 0)) > 600;

    return [
        'on_court'           => !$stale && boolval($entry['on_court'] ?? true),
        'on_court_confirmed' => !$stale,
        'starter'            => boolval($entry['starter'] ?? false),
        'position'           => $entry['position'] ?? '',
        'lineup_available'   => true,
        'lineup_stale'       => $stale,
    ];
}

/**
 * ─────────────────────────────────────────────────────────────────────────
 * CHANGE 3: Fix on_court_flag → on_court key name mismatch
 *
 * webhook_receiver.php writes: on_court_flag
 * live_props_v5.php reads:    on_court
 *
 * In webhook_receiver.php, find all occurrences of on_court_flag and
 * add an alias so both keys are written:
 * ─────────────────────────────────────────────────────────────────────────
 *
 * In webhook_receiver.php line ~242 (player init), change:
 *   'on_court_flag' => true,
 * TO:
 *   'on_court_flag' => true,
 *   'on_court'      => true,
 *
 * And in every place on_court_flag is set to true/false, also set on_court.
 * Example at line ~312:
 *   $pData['on_court_flag'] = false;
 *   $pData['on_court']      = false;   // ADD THIS
 *
 * ─────────────────────────────────────────────────────────────────────────
 * USAGE EXAMPLE in live_props_v5.php main loop:
 * ─────────────────────────────────────────────────────────────────────────
 */

// In your main prediction loop, replace hardcoded playerState with:
// (assuming $playerId is the BDL player ID integer)

/*
$playerState = buildOnCourtState($playerId, $lineupPlayers);

// Also merge any webhook-based state (play-by-play events)
$webhookPlayerKey = strtolower($playerName); // or however you key players
if (isset($liveState['players'][$webhookPlayerKey])) {
    $wp = $liveState['players'][$webhookPlayerKey];
    // Webhook on_court_flag overrides lineup if more recent
    $webhookTs  = intval($wp['last_event_ts'] ?? 0);
    $lineupTs   = intval($lineupPlayers[$playerId]['last_seen'] ?? 0);
    if ($webhookTs > $lineupTs) {
        $playerState['on_court'] = boolval($wp['on_court_flag'] ?? $playerState['on_court']);
    }
}
*/

/**
 * ─────────────────────────────────────────────────────────────────────────
 * CRON SETUP for lineup_poller.php
 * Run every 60 seconds during game hours (6 PM – 1 AM ET = 23:00 – 06:00 UTC)
 * ─────────────────────────────────────────────────────────────────────────
 *
 * Add to server crontab:
 *   * 23-23,0-5 * * * php /path/to/lineup_poller.php >> /tmp/lineup_poller.log 2>&1
 *
 * Or for simplicity every minute all day:
 *   * * * * * php /path/to/lineup_poller.php >> /tmp/lineup_poller.log 2>&1
 *
 * ─────────────────────────────────────────────────────────────────────────
 * BDL WEBHOOK SECRET — WHERE TO PUT IT ON SHARED HOSTING
 * ─────────────────────────────────────────────────────────────────────────
 *
 * webhook_receiver.php uses:
 *   define('BDL_WEBHOOK_SECRET') from config.php (require_once __DIR__ . '/config.php')
 *
 * On your shared hosting server:
 *   1. Open CyberDuck → navigate to the directory containing webhook_receiver.php
 *   2. Open config.php
 *   3. Find: define('BDL_WEBHOOK_SECRET', 'old_secret_here');
 *   4. Replace with your new rotated secret
 *   5. Save and upload
 *
 * Do NOT put BDL_WEBHOOK_SECRET in GitHub Actions secrets —
 * it is only needed on the server where webhook_receiver.php runs.
 */
