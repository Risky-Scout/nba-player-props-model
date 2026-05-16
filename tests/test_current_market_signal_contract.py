"""Contract tests: current-market signal resolver, manifests, gates."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pd = pytest.importorskip("pandas")

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from nba_props_model.pipelines.minutes_artifact_gates import (  # noqa: E402
    require_minutes_predictions_eligible_present,
)
from nba_props_model.pipelines.player_game_eligibility import (  # noqa: E402
    build_current_market_player_signal,
    load_keyed_current_market_signal,
    merge_delivery_manifest_market_signal_fields,
)
from nba_props_model.pipelines.predict import save_all_props_snapshot  # noqa: E402


SLATE = "2026-05-15"


def test_signal_injects_slate_when_missing():
    df = pd.DataFrame(
        {
            "game_id": [100],
            "player_id": [1],
            "stat": ["pts"],
            "line": [20.5],
        }
    )
    out = build_current_market_player_signal(df, slate_date=SLATE, source_label="t")
    assert (out["slate_date"].astype(str) == SLATE).all()


def test_signal_missing_game_id_exits():
    df = pd.DataFrame({"player_id": [1], "slate_date": [SLATE], "line": [1.0]})
    with pytest.raises(SystemExit) as ei:
        build_current_market_player_signal(df, slate_date=SLATE, source_label="t")
    assert "CURRENT_MARKET_SIGNAL_SCHEMA_MISSING_KEYS" in str(ei.value)
    assert "game_id" in str(ei.value)


def test_signal_missing_player_id_exits():
    df = pd.DataFrame({"game_id": [1], "slate_date": [SLATE], "line": [1.0]})
    with pytest.raises(SystemExit) as ei:
        build_current_market_player_signal(df, slate_date=SLATE, source_label="t")
    assert "CURRENT_MARKET_SIGNAL_SCHEMA_MISSING_KEYS" in str(ei.value)


def test_signal_empty_input_contract_columns():
    out = build_current_market_player_signal(
        pd.DataFrame(), slate_date=SLATE, source_label="t"
    )
    assert list(out.columns) == [
        "slate_date",
        "game_id",
        "player_id",
        "has_current_market_line",
        "current_market_line_count",
        "quoted_stats",
    ]
    assert out.empty


def test_resolver_rejects_unkeyed_candidate(tmp_path: Path):
    woo = tmp_path / "deliveries" / SLATE / "wizard_of_odds"
    woo.mkdir(parents=True)
    p = woo / "market_comparison.parquet"
    bad = pd.DataFrame({"game_id": [None], "line": [1.5]})  # type: ignore
    bad.to_parquet(p, index=False)
    keyed, meta = load_keyed_current_market_signal(tmp_path, SLATE)
    assert keyed.empty


def test_resolver_accepts_keyed_market_comparison_injects_slate(tmp_path: Path):
    woo = tmp_path / "deliveries" / SLATE / "wizard_of_odds"
    woo.mkdir(parents=True)
    p = woo / "market_comparison.parquet"
    ts = pd.Timestamp("2026-05-15T18:30:00Z")
    framed = pd.DataFrame(
        {
            "game_id": [901],
            "player_id": [44],
            "stat": ["pts"],
            "line": [22.5],
            "book": ["dk"],
            "market_over_odds": [-110],
            "market_under_odds": [-110],
            "market_no_vig_over_prob": [0.5],
            "snapshot_time_utc": [ts],
        }
    )
    framed.to_parquet(p, index=False)
    keyed, meta = load_keyed_current_market_signal(tmp_path, SLATE)
    assert not keyed.empty and "slate_date" in keyed.columns
    assert str(keyed["slate_date"].iloc[0])[:10] == SLATE


def test_resolver_rejects_stale_secondary_woo(capfd: pytest.CaptureFixture, tmp_path: Path):
    woo = tmp_path / "deliveries" / SLATE / "wizard_of_odds"
    woo.mkdir(parents=True)
    p = woo / "market_comparison.parquet"
    ts = pd.Timestamp("2026-05-04T18:30:00Z")
    framed = pd.DataFrame(
        {
            "game_id": [901],
            "player_id": [44],
            "stat": ["pts"],
            "line": [22.5],
            "snapshot_time_utc": [ts],
        }
    )
    framed.to_parquet(p, index=False)
    capfd.readouterr()
    keyed, meta = load_keyed_current_market_signal(tmp_path, SLATE)
    assert keyed.empty
    outerr = capfd.readouterr().out + capfd.readouterr().err
    assert "CURRENT_MARKET_SIGNAL_CANDIDATE" in outerr
    lo = outerr.lower()
    assert "stale_snapshot_time_utc" in outerr or "accepted=false" in lo
    assert meta["market_superiority_claim_allowed"] is False


def test_save_all_props_emits_stable_ids_keys(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        "nba_props_model.pipelines.predict.PRED_DIR", tmp_path, raising=True
    )
    rows = [
        {
            "slate_date": SLATE,
            "player_id": 7,
            "game_id": 90001,
            "player_name": "X",
            "stat": "pts",
            "line": 22.5,
            "over_odds": -110,
            "under_odds": -112,
            "bet_vendor": "dk",
            "model_prob": 0.52,
            "pmf": {0: 0.001},
            "score": "",
        },
    ]
    save_all_props_snapshot(rows, SLATE)
    out = pd.read_parquet(tmp_path / f"all_props_{SLATE}.parquet")
    assert out["slate_date"].iloc[0] == SLATE
    assert int(out["game_id"].iloc[0]) == 90001
    assert int(out["player_id"].iloc[0]) == 7
    assert "market_over_odds" in out.columns


def test_minutes_eligible_missing_gate(tmp_path: Path):
    mp = tmp_path / "artifacts" / "minutes_predictions" / SLATE
    mp.mkdir(parents=True)
    pd.DataFrame({"x": [1]}).to_parquet(mp / "minutes_predictions.parquet", index=False)
    with pytest.raises(SystemExit, match="MINUTES_PREDICTIONS_ELIGIBLE_MISSING"):
        require_minutes_predictions_eligible_present(tmp_path, SLATE)


def test_manifest_market_claim_false_when_marker_absent(tmp_path: Path):
    manifest: dict = {"status": "passed"}
    merge_delivery_manifest_market_signal_fields(manifest, tmp_path, SLATE)
    assert manifest["market_superiority_claim_allowed"] is False
    assert manifest["market_eval_available"] is False


def test_manifest_market_claim_from_resolver_artifact(tmp_path: Path):
    art = tmp_path / "artifacts" / "current_market_signal"
    art.mkdir(parents=True)
    (art / f"{SLATE}.json").write_text(
        json.dumps(
            {
                "market_eval_available": False,
                "market_rows_keyed": True,
                "market_rows_fresh": False,
                "market_superiority_claim_allowed": False,
                "market_eval_blocker": "test_blocker",
            }
        ),
        encoding="utf-8",
    )
    manifest = {"delivery_date": SLATE}
    merge_delivery_manifest_market_signal_fields(manifest, tmp_path, SLATE)
    assert manifest["market_rows_keyed"] is True
    assert manifest["market_superiority_claim_allowed"] is False


def test_current_run_woo_skips_secondary_stale_rejection(tmp_path: Path):
    woo = tmp_path / "woo" / "mc.parquet"
    woo.parent.mkdir(parents=True)
    ts = pd.Timestamp("2026-05-01T18:30:00Z")
    framed = pd.DataFrame(
        {
            "game_id": [901],
            "player_id": [44],
            "stat": ["pts"],
            "line": [22.5],
            "snapshot_time_utc": [ts],
        }
    )
    framed.to_parquet(woo, index=False)
    _, meta = load_keyed_current_market_signal(
        tmp_path, SLATE, current_run_market_comparison_path=woo.resolve()
    )
    assert meta["current_market_signal_selected_path"] == str(woo.resolve())
    assert meta["market_superiority_claim_allowed"] is False
