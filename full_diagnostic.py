#!/usr/bin/env python3
"""Full model diagnostic — pregame + live performance"""
import csv, glob, json, warnings, numpy as np
from collections import defaultdict
from pathlib import Path
warnings.filterwarnings('ignore')

print("=" * 70)
print("NBA PROPS MODEL v14 — FULL PERFORMANCE DIAGNOSTIC")
print("2026-03-26 | Pre-Game + Live Model")
print("=" * 70)

# ── Load all graded data ───────────────────────────────────────────────────
all_rows = []
for f in sorted(glob.glob('graded/graded_2026-*.csv')):
    for r in csv.DictReader(open(f)):
        try:
            actual_str = r.get('actual','')
            actual = float(actual_str) if actual_str != '' else None
            result = str(r.get('result','')).strip().upper()
            outcome = 1 if result in ('HIT','WIN') else (0 if result in ('MISS','LOSS') else None)
            prob = float(r.get('model_prob') or 0)
            all_rows.append({
                'date':       r.get('grade_date',''),
                'player':     r.get('player_name',''),
                'stat':       r.get('stat','').lower(),
                'side':       r.get('side','').upper(),
                'line':       float(r.get('line') or 0),
                'q50':        float(r.get('q50') or 0),
                'actual':     actual,
                'prob':       prob,
                'outcome':    outcome,
                'result':     result,
                'clv':        float(r.get('clv_proxy') or 0),
                'mp_bucket':  str(r.get('mp_bucket','')).strip(),
                'ev':         float(r.get('ev') or 0),
                'kelly':      float(r.get('kelly_units') or 0),
            })
        except: pass

graded = [r for r in all_rows if r['outcome'] is not None]
print(f"\nTotal rows: {len(all_rows)} | Graded: {len(graded)}")
print(f"Date range: {min(r['date'] for r in all_rows)} → {max(r['date'] for r in all_rows)}")
print(f"Unique players: {len(set(r['player'] for r in all_rows))}")

# ── SECTION 1: OVERALL PERFORMANCE ────────────────────────────────────────
print("\n" + "=" * 70)
print("SECTION 1: OVERALL PERFORMANCE SUMMARY")
print("=" * 70)

def perf(rows):
    if not rows: return {}
    hits = [r['outcome'] for r in rows]
    clvs = [r['clv'] for r in rows]
    probs = [r['prob'] for r in rows]
    evs   = [r['ev'] for r in rows]
    kellys = [r['kelly'] for r in rows]
    brier = np.mean([(p - h)**2 for p,h in zip(probs,hits)])
    roi = (sum(hits) - len(hits)*0.952) / len(hits)  # vs -110 juice
    # Max drawdown
    cumulative = 0; peak = 0; dd = 0
    for h in hits:
        cumulative += (h - 0.952)
        peak = max(peak, cumulative)
        dd = max(dd, peak - cumulative)
    return {
        'n': len(rows),
        'hit_rt': np.mean(hits),
        'clv_mean': np.mean(clvs),
        'clv_pos_pct': np.mean([c > 0 for c in clvs]),
        'brier': brier,
        'roi': roi,
        'max_dd': dd,
        'avg_prob': np.mean(probs),
        'avg_ev': np.mean(evs),
    }

# Split into pre-filter (before Mar 20) and post-filter (after Mar 20)
pre  = [r for r in graded if r['date'] < '2026-03-20']
post = [r for r in graded if r['date'] >= '2026-03-20']

def print_perf(label, rows):
    p = perf(rows)
    if not p: return
    print(f"\n  {label} (n={p['n']}):")
    print(f"    Hit Rate:     {p['hit_rt']:.3f}  (break-even at -110: 0.524)")
    print(f"    ROI:          {p['roi']:+.3f}")
    print(f"    Mean CLV:     {p['clv_mean']:+.4f}")
    print(f"    CLV+ %:       {p['clv_pos_pct']:.1%}")
    print(f"    Brier Score:  {p['brier']:.4f}  (target: <0.230)")
    print(f"    Max Drawdown: {p['max_dd']:.2f} units")
    print(f"    Avg Prob:     {p['avg_prob']:.3f}")
    print(f"    Avg EV:       {p['avg_ev']:+.3f}")

print_perf("PRE-FILTER ERA (Mar 9-19, loose gates)", pre)
print_perf("POST-FILTER ERA (Mar 20-25, v14 gates)", post)
print_perf("ALL TIME", graded)

# ── SECTION 2: BY STAT ────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SECTION 2: PERFORMANCE BY STAT × SIDE")
print("=" * 70)
print(f"  {'stat':<8} {'side':<6} {'n':>5} {'hit_rt':>8} {'CLV':>9} {'CLV+%':>7} {'Brier':>8} {'deploy?':>9}")
print("  " + "-"*65)

for stat in ['pts','reb','ast','fg3m','blk','stl']:
    for side in ['OVER','UNDER']:
        rows = [r for r in graded if r['stat']==stat and r['side']==side]
        if len(rows) < 5: continue
        p = perf(rows)
        should = "ACTIVE" if (p['clv_mean'] > 0 and p['hit_rt'] > 0.45) else "SUPPRESS"
        if (stat,side) in [('blk','OVER'),('stl','OVER'),('fg3m','UNDER'),
                            ('reb','UNDER'),('stl','UNDER')]:
            should = "BANNED"
        print(f"  {stat:<8} {side:<6} {p['n']:>5} {p['hit_rt']:>8.3f} {p['clv_mean']:>+9.4f} "
              f"{p['clv_pos_pct']:>7.1%} {p['brier']:>8.4f} {should:>9}")

# ── SECTION 3: CALIBRATION ────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SECTION 3: CALIBRATION (model prob vs actual hit rate)")
print("=" * 70)
print(f"  {'bucket':<12} {'n':>5} {'pred':>8} {'actual':>8} {'error':>8} {'status':>8}")
print("  " + "-"*55)

for lo, hi in [(0.50,0.55),(0.55,0.60),(0.60,0.65),(0.65,0.70),(0.70,0.75),(0.75,0.80)]:
    rows = [r for r in graded if lo <= r['prob'] < hi]
    if len(rows) < 10: continue
    pred = np.mean([r['prob'] for r in rows])
    act  = np.mean([r['outcome'] for r in rows])
    err  = pred - act
    status = "✓" if abs(err) < 0.05 else "⚠"
    print(f"  {lo:.0%}-{hi:.0%}      {len(rows):>5} {pred:>8.3f} {act:>8.3f} {err:>+8.3f} {status:>8}")

# ── SECTION 4: CLV TREND ──────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SECTION 4: CLV TREND BY DATE (post-filter only)")
print("=" * 70)
print(f"  {'date':<12} {'n':>5} {'hit_rt':>8} {'CLV':>9} {'CLV+%':>8} {'Brier':>8}")
print("  " + "-"*55)

by_date = defaultdict(list)
for r in graded:
    by_date[r['date']].append(r)

for date in sorted(by_date.keys()):
    if date < '2026-03-20': continue
    rows = by_date[date]
    p = perf(rows)
    print(f"  {date:<12} {p['n']:>5} {p['hit_rt']:>8.3f} {p['clv_mean']:>+9.4f} "
          f"{p['clv_pos_pct']:>8.1%} {p['brier']:>8.4f}")

# ── SECTION 5: MINUTES MODEL VALIDATION ───────────────────────────────────
print("\n" + "=" * 70)
print("SECTION 5: MINUTES MODEL × PROJECTION ACCURACY")
print("=" * 70)
print(f"  {'mp_bucket':<12} {'stat':<6} {'n':>5} {'med(act-q50)':>14} {'hit_rt':>8} {'CLV':>8}")
print("  " + "-"*60)

buck = defaultdict(list)
for r in all_rows:
    if r['actual'] is not None and r['q50'] > 0:
        buck[(r['mp_bucket'], r['stat'])].append(r)

for bucket in sorted(set(b for b,_ in buck)):
    for stat in ['pts','reb','ast']:
        rows = buck[(bucket,stat)]
        if len(rows) < 8: continue
        resids  = [r['actual'] - r['q50'] for r in rows]
        graded_r = [r for r in rows if r['outcome'] is not None]
        hr  = np.mean([r['outcome'] for r in graded_r]) if graded_r else 0
        clv = np.mean([r['clv'] for r in graded_r]) if graded_r else 0
        print(f"  {bucket:<12} {stat:<6} {len(rows):>5} {np.median(resids):>+14.3f} "
              f"{hr:>8.3f} {clv:>+8.4f}")

# ── SECTION 6: LIVE MODEL STATUS ──────────────────────────────────────────
print("\n" + "=" * 70)
print("SECTION 6: LIVE IN-PLAY MODEL STATUS")
print("=" * 70)

live_files = sorted(glob.glob('predictions/singles_2026-*.json'))
live_picks = []
for f in live_files[-7:]:
    try:
        d = json.loads(open(f).read())
        for p in d.get('picks',[]):
            live_picks.append({
                'date': d.get('date',''),
                'player': p.get('player_name',''),
                'stat': p.get('stat',''),
                'side': p.get('side',''),
                'line': p.get('line',0),
                'q50':  p.get('q50',0),
                'prob': p.get('model_prob',0),
                'ev':   p.get('ev',0),
            })
    except: pass

if live_picks:
    stat_dist = defaultdict(int)
    for p in live_picks:
        stat_dist[f"{p['stat']}_{p['side']}"] += 1
    print(f"\n  Picks in last 7 prediction files: {len(live_picks)}")
    print(f"  Stat distribution:")
    for k,v in sorted(stat_dist.items(), key=lambda x:-x[1]):
        print(f"    {k}: {v}")
    print(f"\n  Avg model prob: {np.mean([p['prob'] for p in live_picks]):.3f}")
    print(f"  Avg EV: {np.mean([p['ev'] for p in live_picks]):+.3f}")
    print(f"  Avg line: {np.mean([p['line'] for p in live_picks]):.1f}")
    print(f"  Avg Q50: {np.mean([p['q50'] for p in live_picks]):.1f}")

print(f"\n  Live engine status:")
live_api = 'https://dev.wizardofodds.com/tools/odds-scanner/predictions/api/live_props.php'
print(f"  API: {live_api}")
print(f"  BDL webhook: ACTIVE (confirmed 2026-03-19)")
print(f"  Live pricing: PHP fallback (Python pricer path needs verification)")
print(f"  Live CLV tracking: quote_archive.php (cron job pending)")

# ── SECTION 7: MODEL ARCHITECTURE SUMMARY ─────────────────────────────────
print("\n" + "=" * 70)
print("SECTION 7: MODEL ARCHITECTURE SUMMARY (v14)")
print("=" * 70)

try:
    import joblib
    model_files = list(Path('model_cache').glob('*.pkl'))
    centerer_files = list(Path('model_cache').glob('residual_centerer_*.pkl'))
    platt_files = list(Path('model_cache').glob('platt_*.pkl'))
    corr_file = Path('model_cache/minutes_bucket_corrections.json')
    print(f"\n  Model files in model_cache/: {len(model_files)}")
    print(f"  Platt calibrators: {len(platt_files)}")
    print(f"  Residual centerers: {len(centerer_files)}")
    print(f"  Minutes corrections: {'✓' if corr_file.exists() else '✗'}")
except: pass

print(f"""
  Projection layer:
    LightGBM quantile ensemble (11 quantiles × 12 stats)
    XGBoost + RF + GB + Neural Net with Bayesian Ridge meta-learner
    Bias corrections: pts=+1.135, ast=+0.190, reb=+0.010, fg3m=-0.010
    Minutes bucket corrections: buckets 1+2 only, 50% application

  Calibration layer:
    12 stat×side Platt calibrators (out-of-fold fitted)
    Global OVER/UNDER fallback calibrators
    ECE: 7/8 stat×side buckets below 0.05 gate

  Deployment layer:
    OVER: prob ≥ 0.56-0.60 (stat-specific), EV ≥ 2.5%
    UNDER: prob ≥ 0.67-0.74 (stat-specific), EV ≥ 5-7%
    Bad-line filter: line > q50 × 1.75
    Alt-line guard: pts q50 < 17 and line > q50 × 1.5
    Min Q50: pts ≥ 12, reb ≥ 3.5, ast ≥ 2.5
    Portfolio: max 25/day, 2/player, 4/game, 1/player/stat
    MIN_GAMES_SEASON: 20
    BANNED: BLK OVER, STL OVER, REB UNDER, FG3M UNDER, STL UNDER

  SGP layer:
    Gaussian copula with within-player correlation engine
    Cap: 6 singles/game, 60 total candidates
""")

print("=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)
