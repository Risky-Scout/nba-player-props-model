#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


ATOM_PMF_COLUMNS = ("pmf_active", "model_full_pmf", "pmf", "pmf_json")

SOURCE_CANDIDATES = (
    "canonical_source/player_prop_pmfs_tonight_MODEL_ONLY.parquet",
    "canonical_source/all_props_model_only.parquet",
    "wizard_of_odds/full_pmfs_outcome_level.parquet",
)

FORBIDDEN_COLUMNS = {
    "p_ge",
    "prob_ge",
    "survival",
    "survival_prob",
    "cdf",
    "ladder_prob",
    "market_implied_pmf",
    "market_pmf",
    "no_vig_pmf",
}

OUTCOME_COLS = ("outcome", "atom", "k", "x", "value", "stat_value", "result")
PROB_COLS = ("probability", "prob", "p", "model_probability", "model_prob", "pmf_prob", "atom_probability")

GROUP_COLS = (
    "player_id",
    "player_name",
    "player",
    "name",
    "team",
    "team_abbr",
    "opponent",
    "opp",
    "game_id",
    "game_date",
    "stat",
    "stat_key",
    "market",
    "prop_type",
    "role_bucket",
)


def _jsonable(v: Any) -> Any:
    if v is None:
        return None

    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:
            pass

    if hasattr(v, "tolist"):
        try:
            return _jsonable(v.tolist())
        except Exception:
            pass

    if isinstance(v, dict):
        return {str(_jsonable(k)): _jsonable(val) for k, val in v.items()}

    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]

    if isinstance(v, (str, int, float, bool)):
        return v

    return str(v)


def _safe_str(v: Any) -> str:
    v = _jsonable(v)
    if v is None:
        return ""
    return str(v)


def _parse_json_maybe(v: Any) -> Any:
    if isinstance(v, bytes):
        try:
            v = v.decode("utf-8")
        except Exception:
            return None

    if hasattr(v, "tolist"):
        try:
            v = v.tolist()
        except Exception:
            pass

    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        try:
            return json.loads(s)
        except Exception:
            return v

    return v


def _atom(v: Any) -> Optional[int]:
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except Exception:
        return None
    if not math.isfinite(f):
        return None
    if abs(f - round(f)) > 1e-9:
        return None
    k = int(round(f))
    if k < 0:
        return None
    return k


def _prob(v: Any) -> Optional[float]:
    if v is None or isinstance(v, bool):
        return None
    try:
        f = float(v)
    except Exception:
        return None
    if not math.isfinite(f) or f < 0:
        return None
    return f


def _normalize(pmf: Dict[int, float]) -> Optional[Dict[int, float]]:
    clean = {int(k): float(v) for k, v in pmf.items() if v is not None and float(v) >= 0}
    if not clean:
        return None
    total = sum(clean.values())
    if not math.isfinite(total) or total <= 0:
        return None
    return {k: v / total for k, v in sorted(clean.items())}


def _parse_pmf(v: Any) -> Optional[Dict[int, float]]:
    v = _parse_json_maybe(v)

    if v is None:
        return None

    pmf: Dict[int, float] = {}

    if isinstance(v, dict):
        keys = {str(k) for k in v.keys()}
        if FORBIDDEN_COLUMNS.intersection(keys):
            return None

        for nested in ATOM_PMF_COLUMNS:
            if nested in v:
                return _parse_pmf(v[nested])

        support_key = next((k for k in ("support", "atoms", "outcomes", "values", "x") if k in v), None)
        prob_key = next((k for k in ("probs", "probabilities", "probability", "p") if k in v), None)

        if support_key and prob_key and isinstance(v[support_key], (list, tuple)) and isinstance(v[prob_key], (list, tuple)):
            for a, p in zip(v[support_key], v[prob_key]):
                aa = _atom(a)
                pp = _prob(p)
                if aa is None or pp is None:
                    return None
                pmf[aa] = pmf.get(aa, 0.0) + pp
            return _normalize(pmf)

        for k, p in v.items():
            aa = _atom(k)
            pp = _prob(p)
            if aa is None or pp is None:
                return None
            pmf[aa] = pmf.get(aa, 0.0) + pp

        return _normalize(pmf)

    if isinstance(v, (list, tuple)):
        if not v:
            return None

        if all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v):
            for i, p in enumerate(v):
                pp = _prob(p)
                if pp is None:
                    return None
                pmf[i] = pp
            return _normalize(pmf)

        if all(isinstance(x, (list, tuple)) and len(x) == 2 for x in v):
            for a, p in v:
                aa = _atom(a)
                pp = _prob(p)
                if aa is None or pp is None:
                    return None
                pmf[aa] = pmf.get(aa, 0.0) + pp
            return _normalize(pmf)

        if all(isinstance(x, dict) for x in v):
            for item in v:
                keys = {str(k) for k in item.keys()}
                if FORBIDDEN_COLUMNS.intersection(keys):
                    return None

                a_val = None
                p_val = None

                for c in OUTCOME_COLS:
                    if c in item:
                        a_val = item[c]
                        break

                for c in PROB_COLS:
                    if c in item:
                        p_val = item[c]
                        break

                aa = _atom(a_val)
                pp = _prob(p_val)

                if aa is None or pp is None:
                    return None

                pmf[aa] = pmf.get(aa, 0.0) + pp

            return _normalize(pmf)

    return None


def _first(row: pd.Series, cols: Iterable[str], default: Any = "") -> Any:
    for c in cols:
        if c in row.index:
            v = _jsonable(row[c])
            if v is not None:
                return v
    return default


def _find_col(df: pd.DataFrame, cols: Iterable[str]) -> Optional[str]:
    for c in cols:
        if c in df.columns:
            return c
    return None


def _source_diag(path: Path) -> str:
    if not path.exists():
        return f"{path} | MISSING"
    try:
        df = pd.read_parquet(path)
        atom_cols = [c for c in ATOM_PMF_COLUMNS if c in df.columns]
        return f"{path} | rows={len(df)} | atom_cols={atom_cols} | columns={list(df.columns)}"
    except Exception as e:
        return f"{path} | READ_ERROR {type(e).__name__}: {e}"


def _load_source(root: Path, date: str) -> Tuple[Path, pd.DataFrame, str]:
    delivery_dir = root / "deliveries" / date
    checked: List[str] = []

    for rel in SOURCE_CANDIDATES:
        path = delivery_dir / rel
        checked.append(_source_diag(path))

        if not path.exists():
            continue

        df = pd.read_parquet(path)

        for c in ATOM_PMF_COLUMNS:
            if c not in df.columns:
                continue

            ok = False
            for sample in df[c].dropna().head(500).tolist():
                if _parse_pmf(sample) is not None:
                    ok = True
                    break

            if ok:
                return path, df, c

        outcome_col = _find_col(df, OUTCOME_COLS)
        prob_col = _find_col(df, PROB_COLS)

        if outcome_col and prob_col:
            forbidden = FORBIDDEN_COLUMNS.intersection(set(df.columns))
            if forbidden:
                raise SystemExit(
                    f"FATAL outcome-level atom source contains forbidden columns {sorted(forbidden)}: {path}"
                )
            return path, df, f"__outcome_level__:{outcome_col}:{prob_col}"

    raise SystemExit(
        "FATAL M8_6O_BUILD_PMF_RESEARCH_NO_ATOM_SOURCE\n"
        + "\n".join(checked)
    )


def _record(row: pd.Series, pmf: Dict[int, float], source_path: Path, pmf_col: str) -> Dict[str, Any]:
    player = _safe_str(_first(row, ("player_name", "player", "name", "athlete_name", "display_name"), ""))
    stat = _safe_str(_first(row, ("stat", "stat_key", "market", "prop_type", "category"), "")).lower()
    team = _safe_str(_first(row, ("team", "team_abbr", "player_team"), ""))
    opponent = _safe_str(_first(row, ("opponent", "opp", "opponent_abbr"), ""))

    support = [int(k) for k in sorted(pmf.keys())]
    probs = [float(pmf[k]) for k in support]
    atoms = [{"outcome": int(k), "probability": float(pmf[k])} for k in support]

    mean = sum(k * pmf[k] for k in support)
    variance = sum(((k - mean) ** 2) * pmf[k] for k in support)

    rec: Dict[str, Any] = {
        "player": player,
        "stat": stat,
        "team": team,
        "opponent": opponent,
        "source_file": str(source_path),
        "pmf_column": pmf_col,
        "atom_pmf_policy": "atom_source_only_no_ladder_fallback",
        "pmf_source_policy": "canonical_atom_pmf_only",
        "market_implied_pmf_policy": "forbidden_not_generated",
        "atom_pmf": atoms,
        "pmf": {str(k): float(pmf[k]) for k in support},
        "support": support,
        "probs": probs,
        "support_min": int(min(support)),
        "support_max": int(max(support)),
        "support_size": int(len(support)),
        "mean": float(mean),
        "variance": float(variance),
        "atom_probability_sum": float(sum(probs)),
    }

    passthrough = (
        "player_id",
        "game_id",
        "game_date",
        "stat_key",
        "role_bucket",
        "line",
        "book",
        "sportsbook",
        "model_prob_over",
        "model_prob_under",
        "fair_odds_over",
        "fair_odds_under",
        "edge_over",
        "edge_under",
        "ev_over",
        "ev_under",
    )

    for f in passthrough:
        if f in row.index:
            v = _jsonable(row[f])
            if v is not None:
                rec[f] = v

    return rec


def _records_from_wide(df: pd.DataFrame, pmf_col: str, source_path: Path) -> Tuple[List[Dict[str, Any]], int]:
    records = []
    invalid = 0

    for _, row in df.iterrows():
        pmf = _parse_pmf(row[pmf_col])
        if pmf is None:
            invalid += 1
            continue
        records.append(_record(row, pmf, source_path, pmf_col))

    return records, invalid


def _records_from_outcome(df: pd.DataFrame, source_path: Path, outcome_col: str, prob_col: str) -> Tuple[List[Dict[str, Any]], int]:
    group_cols = [c for c in GROUP_COLS if c in df.columns and c not in (outcome_col, prob_col)]

    if not group_cols:
        raise SystemExit(f"FATAL outcome-level source has no grouping columns: {source_path}")

    records = []
    invalid = 0

    for _, g in df.groupby(group_cols, dropna=False, sort=False):
        raw: Dict[int, float] = {}
        for _, row in g.iterrows():
            a = _atom(row[outcome_col])
            p = _prob(row[prob_col])
            if a is None or p is None:
                continue
            raw[a] = raw.get(a, 0.0) + p

        pmf = _normalize(raw)
        if pmf is None:
            invalid += 1
            continue

        records.append(_record(g.iloc[0], pmf, source_path, f"outcome_level:{outcome_col}:{prob_col}"))

    return records, invalid


def _group_players(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}

    for rec in records:
        key = str(rec.get("player_id") or rec.get("player") or "unknown")

        if key not in grouped:
            grouped[key] = {
                "player": rec.get("player", ""),
                "player_id": rec.get("player_id", ""),
                "team": rec.get("team", ""),
                "opponent": rec.get("opponent", ""),
                "stats": [],
                "pmfs": [],
                "props": [],
            }

        # Verifier contract:
        # players[].stats[] must contain true atom PMF fields, but must not
        # contain any forbidden reconstruction/policy tokens:
        # ladder, p_ge, survival, cdf, cumulative, reconstructed, threshold.
        stat_atom = {
            "player": rec.get("player", ""),
            "player_id": rec.get("player_id", ""),
            "stat": rec.get("stat", ""),
            "stat_key": rec.get("stat_key", rec.get("stat", "")),
            "team": rec.get("team", ""),
            "opponent": rec.get("opponent", ""),
            "role_bucket": rec.get("role_bucket", ""),
            "line": rec.get("line", None),
            "mean": rec.get("mean", None),
            "variance": rec.get("variance", None),
            "support": rec.get("support", []),
            "probs": rec.get("probs", []),
            "atom_pmf": rec.get("pmf", {}),
            "pmf": rec.get("pmf", {}),
            "support_min": rec.get("support_min", None),
            "support_max": rec.get("support_max", None),
            "support_size": rec.get("support_size", None),
            "atom_probability_sum": rec.get("atom_probability_sum", None),
        }

        prop_meta = {
            "player": rec.get("player", ""),
            "player_id": rec.get("player_id", ""),
            "stat": rec.get("stat", ""),
            "team": rec.get("team", ""),
            "opponent": rec.get("opponent", ""),
            "line": rec.get("line", None),
            "book": rec.get("book", rec.get("sportsbook", "")),
            "model_prob_over": rec.get("model_prob_over", None),
            "model_prob_under": rec.get("model_prob_under", None),
            "fair_odds_over": rec.get("fair_odds_over", None),
            "fair_odds_under": rec.get("fair_odds_under", None),
            "edge_over": rec.get("edge_over", None),
            "edge_under": rec.get("edge_under", None),
            "ev_over": rec.get("ev_over", None),
            "ev_under": rec.get("ev_under", None),
        }

        grouped[key]["stats"].append(stat_atom)
        grouped[key]["pmfs"].append(stat_atom)
        grouped[key]["props"].append(prop_meta)

    return list(grouped.values())

def _write_json(payload: Dict[str, Any], paths: Iterable[Path]) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, default=_jsonable)
    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"WROTE {p}")


def _write_html(payload: Dict[str, Any], paths: Iterable[Path]) -> None:
    data = json.dumps(payload, indent=2, sort_keys=True, default=_jsonable)
    escaped = html.escape(data)
    safe_script_json = data.replace("</", "<\\/")

    html_text = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>NBA PMF Research</title>
</head>
<body>
  <h1>NBA PMF Research</h1>
  <p>atom_pmf_policy: atom_source_only_no_ladder_fallback</p>
  <p>pmf_source_policy: canonical_atom_pmf_only</p>
  <p>market_implied_pmf_policy: forbidden_not_generated</p>

  <div id="pmf-research-root"></div>

  <h2>True atom PMF payload</h2>
  <pre id="pmf-research-json">__ESCAPED_JSON__</pre>

  <script id="pmf-research-data" type="application/json">__SCRIPT_JSON__</script>

  <script>
    const pmfResearchPayload = JSON.parse(
      document.getElementById("pmf-research-data").textContent
    );

    const root = document.getElementById("pmf-research-root");

    function renderAtomPmf(record) {
      // Verifier-required true atom field access:
      const atom_pmf = record.atom_pmf || [];
      const support = record.support || atom_pmf.map(atom => atom.outcome);
      const probs = record.probs || atom_pmf.map(atom => atom.probability);

      return `
        <section class="pmf-card">
          <h3>${record.player || ""} — ${record.stat || ""}</h3>
          <p>support: ${support.join(", ")}</p>
          <p>probs: ${probs.map(p => Number(p).toFixed(6)).join(", ")}</p>
          <pre>${JSON.stringify(atom_pmf, null, 2)}</pre>
        </section>
      `;
    }

    const records = pmfResearchPayload.pmfs || [];
    root.innerHTML = records.slice(0, 200).map(renderAtomPmf).join("\\n");
  </script>
</body>
</html>
"""

    html_text = html_text.replace("__ESCAPED_JSON__", escaped)
    html_text = html_text.replace("__SCRIPT_JSON__", safe_script_json)

    for p in paths:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html_text, encoding="utf-8")
        print(f"WROTE {p}")


PMF_RESEARCH_MODEL_PROB_PRECEDENCE: tuple[str, ...] = (
    "model_prob",
    "model_p",
    "model_probability",
    "edge_model_prob",
    "probability",
)


def _renderable_model_prob_for_pmf_record(record: Dict[str, Any]) -> Optional[float]:
    """Best-effort: return a non-null per-record ``model_prob`` for the
    PMF research payload's per-prop rows.

    The canonical builder preserves ``model_prob_over``/``model_prob_under``
    in the per-record passthrough. Renderable rows must always carry one
    of those, or a side-agnostic direct field. Returns ``None`` only when
    no probability can be derived — the caller emits
    ``PMF_RESEARCH_RENDER_CONTRACT_FAIL`` in that case.
    """
    for field in PMF_RESEARCH_MODEL_PROB_PRECEDENCE:
        v = record.get(field)
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f) and 0.0 <= f <= 1.0:
            return f
    side = str(record.get("side") or record.get("pick_side") or "").upper()
    over = record.get("model_prob_over")
    under = record.get("model_prob_under")

    def _unit(v):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        return f if (math.isfinite(f) and 0.0 <= f <= 1.0) else None

    over_f = _unit(over)
    under_f = _unit(under)
    if side == "UNDER":
        if under_f is not None:
            return under_f
        if over_f is not None:
            return 1.0 - over_f
    if side == "OVER":
        if over_f is not None:
            return over_f
        if under_f is not None:
            return 1.0 - under_f
    # Side-less PMF rows: ``model_prob_over`` is the conventional
    # canonical-PMF representative probability.
    if over_f is not None:
        return over_f
    if under_f is not None:
        return 1.0 - under_f
    return None


def assert_pmf_research_render_contract(
    payload: Dict[str, Any],
    json_paths: Iterable[Path],
) -> None:
    """Producer-side WoO render-contract check.

    Asserts the freshly-written ``pmf_research.json`` is structurally
    parseable, has non-empty ``rows``/``players``, and every renderable
    record exposes a usable ``model_prob``. Emits the structured
    success/failure markers the workflow gates on.
    """
    rows = payload.get("pmfs") or payload.get("rows") or payload.get("props") or []
    if not isinstance(rows, list):
        raise SystemExit(
            "PMF_RESEARCH_RENDER_CONTRACT_FAIL reason=rows_not_list "
            f"actual_type={type(rows).__name__}"
        )
    players = payload.get("players") or []
    if not rows:
        raise SystemExit("PMF_RESEARCH_RENDER_CONTRACT_FAIL reason=empty_rows")
    if not players:
        raise SystemExit("PMF_RESEARCH_RENDER_CONTRACT_FAIL reason=empty_players")

    # Round-trip every written path so we surface JSON corruption /
    # encoding errors here instead of at downstream verifier time.
    sample_path = None
    for p in json_paths:
        if Path(p).is_file():
            sample_path = Path(p)
            break
    if sample_path is not None:
        try:
            with open(sample_path, "r", encoding="utf-8") as fh:
                parsed = json.load(fh)
            if not isinstance(parsed, dict):
                raise SystemExit(
                    "PMF_RESEARCH_RENDER_CONTRACT_FAIL "
                    f"reason=root_not_object actual={type(parsed).__name__} "
                    f"path={sample_path}"
                )
        except (OSError, ValueError) as exc:
            raise SystemExit(
                "PMF_RESEARCH_RENDER_CONTRACT_FAIL "
                f"reason=parse_error path={sample_path} exc={type(exc).__name__}:{exc}"
            )

    non_null = 0
    unmappable: List[Dict[str, Any]] = []
    for rec in rows:
        if not isinstance(rec, dict):
            unmappable.append({"row": rec})
            continue
        mp = _renderable_model_prob_for_pmf_record(rec)
        if mp is None:
            unmappable.append({
                "player_id": rec.get("player_id"),
                "stat": rec.get("stat"),
                "line": rec.get("line"),
                "book": rec.get("book"),
                "present_keys": sorted(k for k in rec.keys() if not k.startswith("_")),
            })
            continue
        rec["model_prob"] = mp
        non_null += 1
    if unmappable:
        raise SystemExit(
            "PMF_RESEARCH_RENDER_CONTRACT_FAIL "
            f"reason=WOO_MODEL_PROB_UNMAPPABLE rows={len(rows)} "
            f"unmappable={len(unmappable)} sample={json.dumps(unmappable[:3], default=str)}"
        )
    print(
        "PMF_RESEARCH_RENDER_CONTRACT_PASS "
        f"rows={len(rows)} players={len(players)} model_prob_non_null={non_null}"
    )


def build(date: str, root: Path) -> Dict[str, Any]:
    source_path, df, pmf_col = _load_source(root, date)

    if pmf_col.startswith("__outcome_level__:"):
        _, outcome_col, prob_col = pmf_col.split(":", 2)
        records, invalid = _records_from_outcome(df, source_path, outcome_col, prob_col)
    else:
        records, invalid = _records_from_wide(df, pmf_col, source_path)

    if not records:
        raise SystemExit(
            f"FATAL M8_6O_BUILD_PMF_RESEARCH_ZERO_VALID_ATOMS source={source_path} pmf_col={pmf_col}"
        )

    players = _group_players(records)

    payload: Dict[str, Any] = {
        "schema_version": "m8_6o_pmf_research_v1",
        "date": date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "atom_pmf_policy": "atom_source_only_no_ladder_fallback",
        "pmf_source_policy": "canonical_atom_pmf_only",
        "market_implied_pmf_policy": "forbidden_not_generated",
        "source_file": str(source_path),
        "pmf_column": pmf_col,
        "source": f"deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet",
        "pmf_source": f"deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet",
        "public_pmf_source": f"deliveries/{date}/wizard_of_odds/full_pmfs_wide.parquet",
        "canonical_atom_source_file": str(source_path),
        "rows_source": int(len(df)),
        "rows_valid_atom_pmf": int(len(records)),
        "rows_invalid_atom_pmf": int(invalid),
        "player_count": int(len(players)),
        "players": players,
        "pmfs": records,
        "props": records,
    }

    json_paths = (
        root / "public_export" / "wizard_of_odds" / date / "pmf_research.json",
        root / "public_export" / "wizard_of_odds" / "latest" / "pmf_research.json",
        root / "public_export" / "wizard_of_odds" / "pmf_research.json",
        root / "predictions" / "pmf_research.json",
    )

    html_paths = (
        root / "predictions" / "nba-pmf-research.html",
        root / "public_export" / "wizard_of_odds" / date / "nba-pmf-research.html",
        root / "public_export" / "wizard_of_odds" / "latest" / "nba-pmf-research.html",
        root / "public_export" / "wizard_of_odds" / "nba-pmf-research.html",
    )

    _write_json(payload, json_paths)
    _write_html(payload, html_paths)

    print(
        "M8_6O_BUILD_PMF_RESEARCH_PASS "
        f"date={date} source={source_path} pmf_column={pmf_col} "
        f"rows_valid={len(records)} players={len(players)}"
    )

    assert_pmf_research_render_contract(payload, json_paths)

    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    build(args.date, Path(args.root).resolve())


if __name__ == "__main__":
    main()
