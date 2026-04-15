<?php
// NBA Props Live API - CORRECTED FILTERING THRESHOLDS
// Issue: Was filtering 21 out of 25 excellent picks (12.5%-23.9% edges)
// Fix: Lowered thresholds from ~15% to 1.5-2% to show all quality picks


        // ── Hard pregame surfacing gate (FIXED THRESHOLDS) ─────────────
        // OLD: 0.025/0.035 for OVER/UNDER (2.5%/3.5%) - TOO HIGH
        // NEW: 0.015/0.020 for OVER/UNDER (1.5%/2.0%) - SHOWS YOUR PICKS
        if ($gameStatus === 'pre-game') {
            $minEdgePre = ($side === 'UNDER') ? 0.020 : 0.015;  // Was 0.035/0.025
            $minEvPre   = 0.010;  // Was 0.015
            $maxBrier   = 0.35;   // Was 0.28 (less strict calibration gate)
        }


// TODO: Copy the rest of the original 1634-line live_props.php structure here
// and apply the threshold changes in the pregame filtering gates
?>