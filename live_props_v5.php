<?php
/**
 * =============================================================================
 * Live In-Play Feature Engineering v5
 * =============================================================================
 * Complete architectural overhaul of calcLiveProbabilityV3/V4.
 *
 * STRUCTURAL CHANGES FROM V4:
 *   - Separate update engines per stat family (pts/reb/ast/fg3m/blk/stl)
 *   - Model the REMAINDER, not the full game revision
 *   - Opportunity vs conversion split for every stat
 *   - True live minute-remaining engine with rotation state
 *   - Live lineup / on-court state layer
 *   - Stat-specific trust curves
 *   - Stat-specific pace treatment
 *   - Validated heat/cold with deviation-from-expectation
 *   - Foul environment beyond player foul trouble
 *   - Live market-aware bet selection separated from projection
 *
 * IMPLEMENTATION PRIORITY ORDER (per instructions):
 *   P1: stat-specific trust, stat-specific pace, live minute engine
 *   P2: opportunity/conversion split, lineup state, dynamic variance
 *   P3: OT probability, clutch adjustments, validated heat/cold
 *   P4: defender foul trouble, team bonus state, event-level features
 * =============================================================================
 */

// ═══════════════════════════════════════════════════════════════════════════
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
 * INTEGRATION GUIDE
 * =============================================================================
 *
 * STEP 1: Replace constants block (FOUL_MIN_FACTORS → VARIANCE_SHRINK_SPEED)
 *
 * STEP 2: Add all functions from Section 2-7 to live_props.php
 *
 * STEP 3: Update main live processing loop to call V5:
 *   OLD: $result = calcLiveProbabilityV3(...)
 *   NEW: $result = calcLiveProbabilityV5(...)
 *
 * STEP 4: Add new fields to $playerState where it is built:
 *   $playerState['is_star']          = ($expMp >= 30.0 && $starterRate >= 0.9);
 *   $playerState['usage_pct']        = floatval($pick['adv_usage'] ?? 0.20);
 *   $playerState['on_court']         = true; // from BDL lineups endpoint
 *   $playerState['is_closer']        = $playerState['is_star'];
 *   $playerState['shot_events']      = [['ts'=>time(),'made'=>true], ...];
 *   // New fields (P2 — add when lineup data available):
 *   $playerState['star_teammate_on_court']   = true;
 *   $playerState['primary_creator_on_court'] = true;
 *   $playerState['lineup_usage_share']       = 0.22;
 *   // Foul environment (P4):
 *   $playerState['opp_defender_fouls']      = 0;
 *   $playerState['rim_defender_benched']    = false;
 *   $gameState['team_in_bonus']             = false;
 *   $gameState['opp_in_bonus']              = false;
 *
 * STEP 5: Call bet selection separately AFTER projection:
 *   $betSignal = computeLiveBetSelection(
 *       $result['live_proj'], $result['prob'],
 *       $currentLine, $openingLine,
 *       $stat, $side, $liveFeatures, $gameProgress
 *   );
 *
 * STEP 6: Update buildLiveLadder calls to buildLiveLadderV5:
 *   $ladder = buildLiveLadderV5($liveProj, $postedLine, $stat,
 *                                $qPreds, $pregameProj, $gameProgress);
 *
 * STEP 7: Syntax check:
 *   php -l live_props.php
 *
 * FEATURE ROLLOUT ORDER:
 *   Sprint 1 (today):   Sections 1, 5, 6 — stat-specific trust + remainder model
 *   Sprint 2 (this wk): Section 2 — live feature vector + minute engine
 *   Sprint 3 (next wk): Section 3 — opportunity/conversion split per stat
 *   Sprint 4 (ongoing): Section 7 — bet selection separation + lineup state
 * =============================================================================
 */
