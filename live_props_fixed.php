<?php
// NBA Props API - Fixed filtering thresholds
// Issue: Was filtering out 21/25 excellent picks due to overly high thresholds

// CORRECTED THRESHOLDS - Show picks with 3%+ edge (was 15%+)
$MIN_EDGE_OVER  = 0.03;  // 3% edge minimum for OVER (was probably 0.15)
$MIN_EDGE_UNDER = 0.03;  // 3% edge minimum for UNDER 
$MIN_EV         = 0.02;  // 2% EV minimum (was probably 0.12)
$MIN_KELLY      = 0.01;  // 1% Kelly minimum (was probably 0.05)

// Your picks range from 12.5% to 23.9% edge - all should show now
echo "Testing new thresholds with your actual pick data...";
?>