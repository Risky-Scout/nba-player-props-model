"""Phase 13X Part B — Derek edge root-cause auditor.

For every Derek snapshot's market_comparison.parquet, recompute every
quantity that drives an edge from first principles and compare to the
recorded values:

    PMF integrity   : sum, p0, mean, variance, median, tail mass
    model_prob      : recomputed from PMF using push-excluded convention
    market_prob     : recomputed from American odds + no-vig
    raw_edge        : recomputed = model_prob - market_prob
    EV              : recomputed two ways — push-excluded (matches the
                       sportsbook's win-prob convention) AND push-aware
                       (the dollar-EV expectation including the chance
                       of a push)
    push_line / push_prob  : integer-line detection
    large_edge_bucket: EDGE_10_20 / EDGE_20_30 / EDGE_30_PLUS
    publishability   : WATCHLIST_NOT_CONFIRMED_LINEUP /
                       REVIEW_LARGE_EDGE / REVIEW_PUSH_LINE /
                       PUBLISH_BLOCKER / ACTIONABLE_REVIEWED
    systemic warn    : top 20 by abs(edge) skewed > 70% to one side

Pass:   PHASE13X_EDGE_ROOT_CAUSE_PASS    (no calculation bugs found)
Warn:   PHASE13X_EDGE_ROOT_CAUSE_WARN    (no bugs but review labels)
Fail:   PHASE13X_EDGE_ROOT_CAUSE_FAILED  (calculation bug found)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DELIVERIES = REPO_ROOT / "deliveries"
HEALTH = REPO_ROOT / "artifacts" / "automation_health"

# Tolerance for recomputed-vs-recorded comparisons. Display PMFs round
# probabilities and the runner stores 4-decimal model/market probs, so
# 0.005 (0.5 percentage points) is the strict but rounding-safe gate.
RECOMPUTE_TOL = 0.005
# Edge buckets.
EDGE_LARGE_THRESHOLD = 0.10
EDGE_VERY_LARGE_THRESHOLD = 0.20
EDGE_BLOCKER_THRESHOLD = 0.30


def _amer_to_prob(o):
    try:
        o = float(o)
    except Exception:
        return None
    if o > 0:
        return 100.0 / (o + 100.0)
    return (-o) / ((-o) + 100.0)


def _amer_to_payout_per_dollar(o):
    """Net profit per $1 risked at American odds."""
    try:
        o = float(o)
    except Exception:
        return None
    if o > 0:
        return o / 100.0
    return 100.0 / (-o)


def _parse_pmf(s):
    if s is None:
        return None
    if isinstance(s, dict):
        try:
            return {int(k): float(v) for k, v in s.items()}
        except Exception:
            return None
    if isinstance(s, str):
        try:
            d = json.loads(s)
            return {int(k): float(v) for k, v in d.items()}
        except Exception:
            return None
    return None


def _pmf_summary(pmf: dict[int, float] | None):
    if not pmf:
        return None
    items = sorted(pmf.items())
    s = sum(v for _, v in items)
    if s <= 0:
        return None
    p0 = pmf.get(0, 0.0)
    mean = sum(k * v for k, v in items) / s
    var = sum(((k - mean) ** 2) * v for k, v in items) / s
    # median: smallest k where cumulative >= 0.5
    cumulative = 0.0
    median = items[-1][0] if items else 0
    for k, v in items:
        cumulative += v
        if cumulative >= 0.5:
            median = k
            break
    tail_high = sum(v for k, v in items if k >= mean + 2 * (var ** 0.5))
    return {
        "sum": s, "p0": p0, "mean": mean, "variance": var,
        "median": median, "tail_high": tail_high,
        "max_k": items[-1][0] if items else 0,
        "n_support": sum(1 for _, v in items if v > 0),
    }


def _recompute_model_prob(pmf, line: float, side: str
                          ) -> tuple[float | None, float, bool, dict]:
    """Return (model_prob_pushexc, push_prob, is_integer_line, details)."""
    if not pmf:
        return None, 0.0, False, {}
    is_int = float(line).is_integer()
    line_f = float(line)
    s_under = sum(v for k, v in pmf.items() if k < line_f)
    s_over = sum(v for k, v in pmf.items() if k > line_f)
    push = pmf.get(int(line_f), 0.0) if is_int else 0.0
    total = s_under + s_over + push
    if total <= 0:
        return None, push, is_int, {}
    win_denom = max(total - push, 1e-12)
    p_under_pushexc = s_under / win_denom
    p_over_pushexc = s_over / win_denom
    side_u = (side or "").upper()
    model = p_under_pushexc if side_u == "UNDER" else p_over_pushexc
    details = {
        "p_under_pushexc": p_under_pushexc,
        "p_over_pushexc": p_over_pushexc,
        "p_under_strict": s_under,
        "p_over_strict": s_over,
        "p_push": push,
        "pmf_sum": total,
    }
    return model, push, is_int, details


def _recompute_market_prob(over_odds, under_odds, side: str
                           ) -> tuple[float | None, dict]:
    iover = _amer_to_prob(over_odds)
    iunder = _amer_to_prob(under_odds)
    if iover is None or iunder is None:
        return None, {}
    s = iover + iunder
    if s <= 0:
        return None, {}
    novig_over = iover / s
    novig_under = iunder / s
    side_u = (side or "").upper()
    market = novig_under if side_u == "UNDER" else novig_over
    return market, {
        "implied_over": iover, "implied_under": iunder,
        "novig_over": novig_over, "novig_under": novig_under,
        "vig_total": s,
    }


def _recompute_ev(model_prob_pushexc, side_odds, *,
                   p_win_strict: float | None = None,
                   p_loss_strict: float | None = None,
                   push_prob: float = 0.0):
    """Return (ev_pushexc, ev_pushinc).

    ev_pushexc — sportsbook 'win-prob' convention. Treats the bet as
    a binary win/loss; push probability is excluded from the
    denominator. EV per $1 risked = model_prob_pushexc * payout -
    (1 - model_prob_pushexc). Matches the runner's recorded EV.

    ev_pushinc — push-aware dollar EV. Push pays $0; win pays
    `payout`; loss pays $-1. Uses STRICT (push-excluded numerator)
    win/loss probabilities so ``p_win_strict + push_prob +
    p_loss_strict == 1``.
    """
    if model_prob_pushexc is None or side_odds is None:
        return None, None
    payout = _amer_to_payout_per_dollar(side_odds)
    if payout is None:
        return None, None
    ev_pushexc = float(model_prob_pushexc) * payout - (1.0 - float(model_prob_pushexc))
    if p_win_strict is None:
        p_win_strict = float(model_prob_pushexc) * (1.0 - float(push_prob))
    if p_loss_strict is None:
        p_loss_strict = max(0.0, 1.0 - float(p_win_strict) - float(push_prob))
    ev_pushinc = (
        float(p_win_strict) * payout
        + float(push_prob) * 0.0
        + float(p_loss_strict) * (-1.0)
    )
    return ev_pushexc, ev_pushinc


def _classify_publishability(*, calc_bug: bool, lineup_confirmed: bool,
                              snapshot_type: str, abs_edge: float,
                              push_prob: float, is_int: bool):
    if calc_bug:
        return "PUBLISH_BLOCKER", "calculation_bug"
    if abs_edge >= EDGE_BLOCKER_THRESHOLD:
        return "PUBLISH_BLOCKER", "abs_edge_>=_30pp_unjustified"
    if (snapshot_type == "current_live" and not lineup_confirmed):
        # Phase 13X — current_live without confirmed lineup is strictly
        # watchlist regardless of edge size.
        if abs_edge >= EDGE_VERY_LARGE_THRESHOLD:
            return ("REVIEW_LARGE_EDGE",
                    "current_live_unconfirmed_lineup_with_large_edge")
        if is_int and push_prob >= 0.05:
            return ("REVIEW_PUSH_LINE",
                    "current_live_unconfirmed_lineup_integer_line_push")
        return "WATCHLIST_NOT_CONFIRMED_LINEUP", "current_live_unconfirmed_lineup"
    if abs_edge >= EDGE_VERY_LARGE_THRESHOLD:
        return "REVIEW_LARGE_EDGE", "abs_edge_>=_20pp"
    if is_int and push_prob >= 0.05:
        return "REVIEW_PUSH_LINE", "integer_line_with_meaningful_push_mass"
    return "ACTIONABLE_REVIEWED", "passes_all_gates"


def _root_cause_label(*, abs_edge: float, push_prob: float,
                       is_int: bool, line: float, stat: str | None,
                       p0: float | None, line_vs_median,
                       lineup_confirmed: bool,
                       snapshot_type: str):
    if not lineup_confirmed and snapshot_type == "current_live":
        return "unconfirmed_lineup_baseline"
    if is_int and push_prob >= 0.05:
        return "push_line"
    if line is not None and float(line) <= 1.5 and (stat or "").lower() in (
        "blk", "stl", "fg3m"
    ):
        return "low_line_discrete_stat"
    if p0 is not None and p0 >= 0.40:
        return "p0_or_low_stat_mass"
    if line_vs_median is not None and abs(float(line_vs_median)) >= 1.5:
        return "line_vs_median_gap"
    return "market_prob_disagreement"


def _audit_snapshot(snap_dir: Path) -> dict:
    out: dict = {"snap_dir": str(snap_dir.relative_to(REPO_ROOT))}
    mc = snap_dir / "market_comparison.parquet"
    manifest = snap_dir / "snapshot_manifest.json"
    if not mc.exists():
        out["error"] = "market_comparison.parquet missing"
        return out
    try:
        m = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else {}
    except Exception:
        m = {}
    snapshot_type = m.get("snapshot_type")
    lineup_confirmed = bool(m.get("lineup_confirmed"))

    import pandas as pd
    df = pd.read_parquet(mc)
    issues: list[str] = []
    rows: list[dict] = []
    for _, r in df.iterrows():
        line = r.get("line")
        side = r.get("side")
        stat = r.get("stat")
        if line is None or pd.isna(line):
            continue
        try:
            line_f = float(line)
        except Exception:
            continue
        pmf = _parse_pmf(r.get("pmf"))
        psum = _pmf_summary(pmf)
        # PMF integrity check.
        if psum is None:
            issues.append(
                f"row {r.get('player_name')!r}/{stat}/{side}/{line}: "
                "pmf empty / unparseable"
            )
            continue
        if abs(psum["sum"] - 1.0) > 0.005:
            issues.append(
                f"row {r.get('player_name')!r}/{stat}/{side}/{line}: "
                f"pmf_sum={psum['sum']:.4f} drift > 0.005"
            )
        model_recomputed, push_prob, is_int, details = _recompute_model_prob(
            pmf, line_f, str(side or "")
        )
        market_recomputed, mkt_details = _recompute_market_prob(
            r.get("over_odds"), r.get("under_odds"), str(side or "")
        )
        model_recorded = float(r.get("model_prob")) if pd.notna(r.get("model_prob")) else None
        market_recorded = float(r.get("market_prob")) if pd.notna(r.get("market_prob")) else None
        edge_recorded = float(r.get("raw_edge")) if pd.notna(r.get("raw_edge")) else None
        ev_recorded = float(r.get("ev")) if pd.notna(r.get("ev")) else None
        side_odds = (
            r.get("under_odds") if str(side or "").upper() == "UNDER"
            else r.get("over_odds")
        )
        # Recompute EV both conventions. We pass STRICT (pre-push-
        # normalization) win/loss probabilities so the push-inclusive
        # dollar EV is honest.
        side_u = (side or "").upper()
        if side_u == "UNDER":
            p_win_strict = details.get("p_under_strict")
            p_loss_strict = details.get("p_over_strict")
        else:
            p_win_strict = details.get("p_over_strict")
            p_loss_strict = details.get("p_under_strict")
        ev_pushexc, ev_pushinc = _recompute_ev(
            model_recomputed, side_odds,
            p_win_strict=p_win_strict, p_loss_strict=p_loss_strict,
            push_prob=push_prob,
        )
        edge_recomputed = (
            (model_recomputed - market_recomputed)
            if (model_recomputed is not None
                and market_recomputed is not None)
            else None
        )
        row_issues: list[str] = []
        if model_recomputed is not None and model_recorded is not None:
            if abs(model_recomputed - model_recorded) > RECOMPUTE_TOL:
                row_issues.append(
                    f"model_prob mismatch recomputed={model_recomputed:.4f} "
                    f"recorded={model_recorded:.4f}"
                )
        if market_recomputed is not None and market_recorded is not None:
            if abs(market_recomputed - market_recorded) > RECOMPUTE_TOL:
                row_issues.append(
                    f"market_prob mismatch recomputed={market_recomputed:.4f} "
                    f"recorded={market_recorded:.4f}"
                )
        if edge_recomputed is not None and edge_recorded is not None:
            if abs(edge_recomputed - edge_recorded) > RECOMPUTE_TOL:
                row_issues.append(
                    f"raw_edge mismatch recomputed={edge_recomputed:+.4f} "
                    f"recorded={edge_recorded:+.4f}"
                )
        if (ev_pushexc is not None and ev_recorded is not None
            and abs(ev_pushexc - ev_recorded) > RECOMPUTE_TOL):
            # ev_pushexc is the convention the runner uses; mismatch
            # against that is the calc-bug signal. ev_pushinc is the
            # honest dollar-EV; we ALSO record it but don't fail on it.
            row_issues.append(
                f"ev mismatch recomputed_pushexc={ev_pushexc:+.4f} "
                f"recorded={ev_recorded:+.4f}"
            )

        abs_edge_recorded = abs(edge_recorded or 0.0)
        if abs_edge_recorded >= EDGE_VERY_LARGE_THRESHOLD:
            bucket = (
                "EDGE_30_PLUS" if abs_edge_recorded >= 0.30
                else "EDGE_20_30"
            )
        elif abs_edge_recorded >= EDGE_LARGE_THRESHOLD:
            bucket = "EDGE_10_20"
        else:
            bucket = "EDGE_LT_10"

        publish_status, publish_reason = _classify_publishability(
            calc_bug=bool(row_issues),
            lineup_confirmed=lineup_confirmed,
            snapshot_type=snapshot_type or "",
            abs_edge=abs_edge_recorded,
            push_prob=push_prob,
            is_int=is_int,
        )
        root_cause = _root_cause_label(
            abs_edge=abs_edge_recorded, push_prob=push_prob,
            is_int=is_int, line=line_f, stat=stat,
            p0=psum.get("p0"),
            line_vs_median=r.get("line_vs_median"),
            lineup_confirmed=lineup_confirmed,
            snapshot_type=snapshot_type or "",
        )

        rec = {
            "player_name": r.get("player_name"),
            "stat": stat, "side": side, "line": line_f,
            "book": r.get("bet_vendor") or r.get("book"),
            "over_odds": r.get("over_odds"),
            "under_odds": r.get("under_odds"),
            "model_prob": model_recorded,
            "model_prob_recomputed": model_recomputed,
            "market_prob": market_recorded,
            "market_prob_recomputed": market_recomputed,
            "raw_edge": edge_recorded,
            "raw_edge_recomputed": edge_recomputed,
            "ev": ev_recorded,
            "ev_recomputed_pushexc": ev_pushexc,
            "ev_recomputed_pushinc": ev_pushinc,
            "push_line": is_int,
            "push_prob": push_prob,
            "p0": psum.get("p0"),
            "pmf_sum": psum.get("sum"),
            "pmf_mean": psum.get("mean"),
            "pmf_variance": psum.get("variance"),
            "pmf_median": psum.get("median"),
            "pmf_max_k": psum.get("max_k"),
            "pmf_n_support": psum.get("n_support"),
            "line_vs_median": r.get("line_vs_median"),
            "issues": row_issues,
            "abs_edge_recorded": abs_edge_recorded,
            "large_edge_bucket": bucket,
            "edge_publish_status": publish_status,
            "edge_publish_reason": publish_reason,
            "root_cause_label": root_cause,
            "lineup_confirmed": lineup_confirmed,
            "snapshot_type": snapshot_type,
        }
        rows.append(rec)
        if row_issues:
            for ri in row_issues:
                issues.append(
                    f"{r.get('player_name')!r}/{stat}/{side}/{line}: {ri}"
                )

    out["row_count"] = len(rows)
    out["issues"] = issues
    out["rows"] = rows
    out["snapshot_type"] = snapshot_type
    out["lineup_confirmed"] = lineup_confirmed

    # Top edges + systemic side/stat skew.
    rows_sorted = sorted(rows, key=lambda x: x.get("abs_edge_recorded") or 0.0,
                         reverse=True)
    top25 = rows_sorted[:25]
    out["top_25_edges"] = top25
    top20 = rows_sorted[:20]
    if top20:
        side_counts: dict = {}
        stat_counts: dict = {}
        for r in top20:
            side_counts[r["side"]] = side_counts.get(r["side"], 0) + 1
            stat_counts[r["stat"]] = stat_counts.get(r["stat"], 0) + 1
        out["top20_side_counts"] = side_counts
        out["top20_stat_counts"] = stat_counts
        max_side_share = max(side_counts.values()) / 20.0
        out["top20_max_side_share"] = max_side_share
        if max_side_share > 0.70:
            out["systemic_directional_warning"] = (
                f"top 20 edges {max(side_counts, key=side_counts.get)}-"
                f"skewed share={max_side_share:.0%}"
            )

    # Bucket counts.
    bucket_counts: dict = {}
    publish_counts: dict = {}
    for r in rows:
        bucket_counts[r["large_edge_bucket"]] = (
            bucket_counts.get(r["large_edge_bucket"], 0) + 1
        )
        publish_counts[r["edge_publish_status"]] = (
            publish_counts.get(r["edge_publish_status"], 0) + 1
        )
    out["bucket_counts"] = bucket_counts
    out["publish_status_counts"] = publish_counts
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--delivery-date", required=True)
    args = p.parse_args(argv)

    HEALTH.mkdir(parents=True, exist_ok=True)
    base = DELIVERIES / args.delivery_date / "derek_game_snapshots"
    payload: dict = {
        "schema_version": "1.0",
        "delivery_date": args.delivery_date,
        "snapshots": [],
    }
    if not base.exists():
        payload["outcome"] = "pending"
        payload["reason"] = "no derek_game_snapshots dir"
        (HEALTH / f"derek_edge_root_cause_{args.delivery_date}.json").write_text(
            json.dumps(payload, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )
        print("PHASE13X_EDGE_ROOT_CAUSE_WARN")
        print(f"  reason={payload['reason']}")
        return 0

    total_issues: list[str] = []
    review_or_blocker = 0
    for game_dir in sorted(base.iterdir()):
        if not game_dir.is_dir():
            continue
        for snap_type in ("current_live", "t_minus_25", "close_lock"):
            sd = game_dir / snap_type
            if not (sd / "snapshot_manifest.json").exists():
                continue
            audit = _audit_snapshot(sd)
            audit["game_id"] = game_dir.name
            audit["snapshot_type_dir"] = snap_type
            payload["snapshots"].append(audit)
            total_issues.extend(audit.get("issues") or [])
            for s, n in (audit.get("publish_status_counts") or {}).items():
                if s != "ACTIONABLE_REVIEWED":
                    review_or_blocker += n

    out_json = HEALTH / f"derek_edge_root_cause_{args.delivery_date}.json"
    out_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )

    # Markdown report — per snapshot, top 25 edges + status table.
    md = [
        f"# Derek edge root-cause audit — {args.delivery_date}",
        "",
        f"- snapshots audited: **{len(payload['snapshots'])}**",
        f"- total calculation issues: **{len(total_issues)}**",
        f"- non-actionable rows: **{review_or_blocker}**",
        "",
        "## Headline finding",
        "",
    ]
    if total_issues:
        md.append(
            "**Calculation bug found.** See per-row issues below — these "
            "are recompute mismatches > 0.5 percentage points."
        )
    else:
        md.append(
            "**No calculation bug.** Every row's model_prob, market_prob, "
            "raw_edge, and EV recomputed within 0.5 percentage points "
            "of the recorded values, using the **push-excluded** "
            "convention for integer lines (consistent with the "
            "sportsbook win-probability standard)."
        )
    md.append("")
    for a in payload["snapshots"]:
        sd = a.get("snap_dir")
        md.append(f"## {sd}")
        md.append("")
        md.append(
            f"- snapshot_type: `{a.get('snapshot_type')}`  "
            f"lineup_confirmed: **{a.get('lineup_confirmed')}**"
        )
        md.append(f"- row_count: {a.get('row_count')}")
        md.append(f"- bucket_counts: {a.get('bucket_counts')}")
        md.append(f"- publish_status_counts: {a.get('publish_status_counts')}")
        if a.get("systemic_directional_warning"):
            md.append(
                f"- ⚠️ {a['systemic_directional_warning']}"
            )
        md.append("")
        md.append("### Top 25 largest edges (by |raw_edge|)")
        md.append("")
        md.append(
            "| player | stat | side | line | model | model_re | market | "
            "market_re | edge | edge_re | ev | ev_pushexc | ev_pushinc | "
            "push? | push_p | p0 | mean | bucket | publish_status | "
            "root_cause | calc_ok |"
        )
        md.append("| " + " | ".join(["---"] * 21) + " |")
        for r in a.get("top_25_edges") or []:
            calc_ok = "yes" if not r.get("issues") else "**NO**"
            md.append(
                f"| {r.get('player_name')} | {r.get('stat')} | "
                f"{r.get('side')} | {r.get('line')} | "
                f"{(r.get('model_prob') or 0.0):.3f} | "
                f"{(r.get('model_prob_recomputed') or 0.0):.3f} | "
                f"{(r.get('market_prob') or 0.0):.3f} | "
                f"{(r.get('market_prob_recomputed') or 0.0):.3f} | "
                f"{(r.get('raw_edge') or 0.0):+.3f} | "
                f"{(r.get('raw_edge_recomputed') or 0.0):+.3f} | "
                f"{(r.get('ev') or 0.0):+.3f} | "
                f"{(r.get('ev_recomputed_pushexc') or 0.0):+.3f} | "
                f"{(r.get('ev_recomputed_pushinc') or 0.0):+.3f} | "
                f"{r.get('push_line')} | "
                f"{(r.get('push_prob') or 0.0):.3f} | "
                f"{(r.get('p0') or 0.0):.3f} | "
                f"{(r.get('pmf_mean') or 0.0):.2f} | "
                f"{r.get('large_edge_bucket')} | "
                f"{r.get('edge_publish_status')} | "
                f"{r.get('root_cause_label')} | {calc_ok} |"
            )
        md.append("")
    out_md = HEALTH / f"derek_edge_root_cause_{args.delivery_date}.md"
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    # Phase 13X — explicit per-axis pass lines.
    push_line_issue_count = sum(
        1 for a in payload["snapshots"] for r in a.get("rows", [])
        if r.get("push_line") and r.get("issues")
    )
    if total_issues:
        print("PHASE13X_EDGE_ROOT_CAUSE_FAILED", file=sys.stderr)
        for i in total_issues[:20]:
            print(f"  - {i}", file=sys.stderr)
        return 1
    # Calculation pass — every recompute matched within 0.5 pp.
    print("PHASE13X_EDGE_CALCULATION_PASS")
    if push_line_issue_count == 0:
        print("PHASE13X_PUSH_LINE_AUDIT_PASS")
    else:
        print("PHASE13X_PUSH_LINE_AUDIT_FAILED", file=sys.stderr)
    if review_or_blocker > 0:
        print("PHASE13X_EDGE_ROOT_CAUSE_WARN")
        print(
            f"  no calculation bug; {review_or_blocker} rows are review "
            "or publish-blocker (current_live unconfirmed lineup, large "
            "edges, or push-line)"
        )
        return 0
    print("PHASE13X_EDGE_ROOT_CAUSE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
