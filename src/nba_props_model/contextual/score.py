"""Phase 13R — contextual scoring helper.

Loads the Phase 13Q contextual challenger artifacts (Ridge adjustment
models + saved feature lists) from a challenger directory and exposes
``ContextualEngine.score_row(feature_row)`` which returns a dict of
trained per-target deltas:

    {
        "minutes_delta":   float,              # additive on mp_mean_last10
        "rate_delta_pts":  float,              # additive on pts_rate_mean_last10
        "rate_delta_reb":  float,
        ...
    }

The engine is **read-only** — it does not mutate champion_pointer or any
on-disk file. Consumers (Derek live snapshot, verifiers) are responsible
for using the deltas to adjust ``exp_mp`` / per-stat lambdas, recompute
PMF means, and write the per-snapshot decomposition.

The feature row ``build_context_feature_row()`` emits is a strict union
of the saved feature lists (it never fabricates columns the model
wasn't trained on, and it never adds columns the model wasn't given —
the engine only reads exactly the columns recorded in
``phase13q_<stat>_adjustment_features.pkl``).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple


# Stable ID stamped by the Phase 13Q trainer; verifiers cross-check this.
CONTEXTUAL_FEATURE_SET_ID = "phase13q_contextual_pmf_engine_v1"

ADJUSTMENT_TARGETS = ("minutes", "pts", "reb", "ast", "tov", "stl", "blk", "fg3m")


# ── Feature-row builder ──────────────────────────────────────────────


def _safe_float(v, default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        return float(v)
    except Exception:
        return default


def _safe_bool(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return 1.0 if float(v) != 0.0 else 0.0
    s = str(v).strip().lower()
    return 1.0 if s in ("true", "1", "yes", "y") else 0.0


def _hash_opponent(opponent_team_id) -> float:
    if opponent_team_id in (None, "", 0):
        return 0.0
    try:
        return float(int(opponent_team_id) % 16)
    except Exception:
        return 0.0


def build_context_feature_row(row: Mapping, *,
                               feature_columns: Iterable[str]) -> List[float]:
    """Project a (potentially noisy) per-player prediction row into the
    exact ordered feature vector the trained Phase 13Q model expects.

    Honest fallbacks: missing columns return 0.0 with the convention that
    every saved feature list carries a ``*_features_missing`` indicator
    so the model can learn to discount missing context. We never fabricate
    confirmed lineup signal — if ``lineup_confirmed`` is not set on the
    row, we write 0.0 for ``starter_proxy_lagged`` only when no lagged
    minutes are present; otherwise we use the lagged proxy value.
    """
    out: List[float] = []
    for c in feature_columns:
        if c == "is_actionable":
            v = row.get("is_actionable")
            out.append(1.0 if v is None else _safe_bool(v))
        elif c == "is_confirmed_out":
            out.append(_safe_bool(row.get("is_confirmed_out")))
        elif c == "is_inactive":
            out.append(_safe_bool(row.get("is_inactive")))
        elif c == "is_doubtful":
            out.append(_safe_bool(row.get("is_doubtful")))
        elif c == "is_questionable":
            out.append(_safe_bool(row.get("is_questionable")))
        elif c == "is_probable":
            out.append(_safe_bool(row.get("is_probable")))
        elif c == "injury_status_encoded":
            out.append(_safe_float(row.get("injury_status_encoded"), 0.0))
        elif c == "availability_status_encoded":
            out.append(_safe_float(row.get("availability_status_encoded"), 0.0))
        elif c == "injury_features_missing":
            v = row.get("injury_features_missing")
            out.append(_safe_float(v, 1.0))
        elif c == "vacated_features_missing":
            v = row.get("vacated_features_missing")
            out.append(_safe_float(v, 1.0))
        elif c == "num_teammates_out_total":
            out.append(_safe_float(row.get("num_teammates_out_total"), 0.0))
        elif c == "num_teammates_out_guard":
            out.append(_safe_float(row.get("num_teammates_out_guard"), 0.0))
        elif c == "num_teammates_out_wing":
            out.append(_safe_float(row.get("num_teammates_out_wing"), 0.0))
        elif c == "num_teammates_out_big":
            out.append(_safe_float(row.get("num_teammates_out_big"), 0.0))
        elif c == "vacated_minutes_total":
            out.append(_safe_float(row.get("vacated_minutes_total"), 0.0))
        elif c == "vacated_minutes_guard":
            out.append(_safe_float(row.get("vacated_minutes_guard"), 0.0))
        elif c == "vacated_minutes_wing":
            out.append(_safe_float(row.get("vacated_minutes_wing"), 0.0))
        elif c == "vacated_minutes_big":
            out.append(_safe_float(row.get("vacated_minutes_big"), 0.0))
        elif c == "vacated_fga_total":
            out.append(_safe_float(row.get("vacated_fga_total"), 0.0))
        elif c == "starter_proxy_lagged":
            # Use the lagged proxy when present; otherwise infer from
            # exp_mp >= 24.0 (mirrors the trainer's threshold). When the
            # row carries a confirmed_starter signal we DO NOT promote
            # it into starter_proxy_lagged — the trained model wasn't
            # given live confirmation; that signal is recorded
            # separately on the snapshot for downstream consumers.
            v = row.get("starter_proxy_lagged")
            if v is not None:
                out.append(_safe_float(v, 0.0))
            else:
                emp = row.get("exp_mp")
                out.append(1.0 if (_safe_float(emp, 0.0) >= 24.0) else 0.0)
        elif c == "is_home":
            out.append(_safe_bool(row.get("is_home")))
        elif c == "rest_days":
            v = row.get("rest_days")
            out.append(_safe_float(v if v is not None else 5.0, 5.0))
        elif c == "is_back_to_back":
            out.append(_safe_bool(row.get("is_back_to_back")))
        elif c == "is_three_in_four":
            out.append(_safe_bool(row.get("is_three_in_four")))
        elif c == "season_game_number":
            out.append(_safe_float(row.get("season_game_number"), 41.0))
        elif c == "season_game_number_norm":
            sgn = row.get("season_game_number_norm")
            if sgn is None:
                sgn = _safe_float(row.get("season_game_number"), 41.0) / 82.0
            out.append(_safe_float(sgn, 0.5))
        elif c == "opponent_team_id_hash":
            v = row.get("opponent_team_id_hash")
            if v is None:
                v = _hash_opponent(row.get("opponent_team_id"))
            out.append(_safe_float(v, 0.0))
        else:
            # Unknown column from a future feature_set_id: zero-fill
            # rather than raise. Verifier flags any unknowns.
            out.append(_safe_float(row.get(c), 0.0))
    return out


# ── Engine ───────────────────────────────────────────────────────────


@dataclass
class ContextualEngine:
    challenger_dir: Path
    feature_set_id: str
    feature_lists: Dict[str, List[str]] = field(default_factory=dict)
    models: Dict[str, "object"] = field(default_factory=dict)
    feature_list_hashes: Dict[str, str] = field(default_factory=dict)
    fitted_targets: List[str] = field(default_factory=list)
    model_manifest: Dict = field(default_factory=dict)
    train_manifest: Dict = field(default_factory=dict)

    def score_row(self, row: Mapping) -> Dict[str, float]:
        """Apply each fitted Ridge model to the row and return a dict
        of deltas. Missing models produce no entry."""
        import numpy as np

        out: Dict[str, float] = {}
        for stat, model in self.models.items():
            cols = self.feature_lists.get(stat) or []
            vec = build_context_feature_row(row, feature_columns=cols)
            if not vec:
                continue
            try:
                delta = float(model.predict(np.array([vec], dtype=float))[0])
            except Exception:
                continue
            if stat == "minutes":
                out["minutes_delta"] = delta
            else:
                out[f"rate_delta_{stat}"] = delta
        return out

    def score_rows(self, rows: Iterable[Mapping]) -> List[Dict[str, float]]:
        return [self.score_row(r) for r in rows]

    def to_metadata(self) -> Dict:
        return {
            "feature_set_id": self.feature_set_id,
            "challenger_dir": str(self.challenger_dir),
            "fitted_targets": list(self.fitted_targets),
            "feature_list_hashes": dict(self.feature_list_hashes),
            "feature_columns": self.feature_lists.get("minutes")
                                or next(iter(self.feature_lists.values()), []),
            "model_manifest_promoted_at_utc": self.model_manifest.get("promoted_at_utc"),
            "trained_through_date": self.train_manifest.get("trained_through_date"),
            "calibrated_through_date": self.train_manifest.get("calibrated_through_date"),
        }


def _hash_columns(cols: Iterable[str]) -> str:
    payload = "|".join(sorted(cols))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def load_contextual_engine(challenger_dir: Path,
                            *, prefix: str = "phase13q",
                            require_minutes: bool = True) -> ContextualEngine:
    """Load all available Phase 13Q adjustment models from ``challenger_dir``.

    Raises ``FileNotFoundError`` if the manifest is missing or no fitted
    targets can be loaded.
    """
    import joblib  # local import to keep top-level light

    challenger_dir = Path(challenger_dir)
    train_manifest_path = challenger_dir / "train_manifest.json"
    model_manifest_path = challenger_dir / "model_manifest.json"
    if not train_manifest_path.exists():
        raise FileNotFoundError(f"missing {train_manifest_path}")
    train_manifest = json.loads(train_manifest_path.read_text(encoding="utf-8"))
    feature_set_id = train_manifest.get("feature_set_id") or CONTEXTUAL_FEATURE_SET_ID
    fitted_targets: List[str] = list(train_manifest.get("fitted_targets") or [])
    model_manifest = {}
    if model_manifest_path.exists():
        try:
            model_manifest = json.loads(model_manifest_path.read_text(encoding="utf-8"))
        except Exception:
            model_manifest = {}

    feature_lists: Dict[str, List[str]] = {}
    models: Dict[str, "object"] = {}
    feat_hashes: Dict[str, str] = {}

    for stat in ADJUSTMENT_TARGETS:
        feat_pkl = challenger_dir / f"{prefix}_{stat}_adjustment_features.pkl"
        model_pkl = challenger_dir / f"{prefix}_{stat}_adjustment_model.pkl"
        if not (feat_pkl.exists() and model_pkl.exists()):
            continue
        try:
            cols = list(joblib.load(feat_pkl))
            mdl = joblib.load(model_pkl)
        except Exception as exc:
            raise RuntimeError(
                f"failed to load {prefix}_{stat}_adjustment artifacts: {exc}"
            ) from exc
        feature_lists[stat] = cols
        models[stat] = mdl
        feat_hashes[stat] = _hash_columns(cols)

    if require_minutes and "minutes" not in models:
        raise FileNotFoundError(
            f"contextual minutes model missing in {challenger_dir} "
            f"({prefix}_minutes_adjustment_model.pkl)"
        )

    return ContextualEngine(
        challenger_dir=challenger_dir,
        feature_set_id=feature_set_id,
        feature_lists=feature_lists,
        models=models,
        feature_list_hashes=feat_hashes,
        fitted_targets=fitted_targets or list(models.keys()),
        model_manifest=model_manifest,
        train_manifest=train_manifest,
    )


def resolve_contextual_challenger_dir(repo_root: Path,
                                       champion_pointer: Optional[Mapping] = None
                                       ) -> Tuple[Optional[Path], str]:
    """Resolve which contextual challenger directory the active champion
    references. Returns ``(path_or_none, reason)``.

    The reason string is the **exact blocker** when no contextual
    challenger is wired — verifiers and the Derek runner surface this
    verbatim so the operator sees why a snapshot is non-contextual."""
    if champion_pointer is None:
        pointer_path = (
            repo_root / "artifacts" / "models" / "registry"
            / "champion_pointer.json"
        )
        if not pointer_path.exists():
            return None, "champion_pointer.json missing"
        try:
            champion_pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return None, f"cannot parse champion_pointer.json: {exc}"

    fs_id = (champion_pointer or {}).get("feature_set_id") or ""
    contextual_dir = (champion_pointer or {}).get("contextual_challenger_dir")
    if contextual_dir:
        p = repo_root / contextual_dir if not Path(contextual_dir).is_absolute() else Path(contextual_dir)
        if p.exists():
            return p, "ok"
        return None, f"contextual_challenger_dir referenced but missing: {contextual_dir}"

    # Fallback: scan challengers/<date>_contextual. We always fall back
    # so verifiers can exercise the trained artifacts before promotion;
    # the returned reason carries the non-contextual pointer state so
    # callers (Derek runner) can refuse to claim contextual when the
    # active champion has not yet been promoted.
    challengers_root = repo_root / "artifacts" / "models" / "challengers"
    candidates: list[Path] = []
    if challengers_root.exists():
        candidates = sorted(
            d for d in challengers_root.iterdir()
            if d.is_dir() and d.name.endswith("_contextual")
        )
    if not fs_id.startswith("phase13q_") and not fs_id.startswith("phase13r_"):
        if candidates:
            return candidates[-1], (
                f"contextual artifacts present at {candidates[-1].name} "
                f"but champion_pointer.feature_set_id={fs_id!r} is not a "
                "contextual feature set — promote the contextual challenger "
                "before claiming contextual_pmf_engine in production"
            )
        return None, (
            f"champion_pointer.feature_set_id={fs_id!r} is not a contextual "
            "feature set and no <date>_contextual challenger directory found"
        )
    if candidates:
        return candidates[-1], "ok"
    return None, "no <date>_contextual challenger directory found"
