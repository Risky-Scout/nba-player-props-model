"""Tests for the derek_near_lineup → derek_pre_tipoff_refresh rename.

The rename is backward-compatible:

  - The new canonical mode is ``derek_pre_tipoff_refresh``.
  - The legacy mode name ``derek_near_lineup`` is still accepted by the
    workflow dispatch input, the pipeline mode dispatcher, and the
    LEGACY_MODE_TO_RUN_STAMP map so existing crons / dispatches do not
    break during the transition.
  - The Python function ``run_derek_near_lineup`` is preserved as a thin
    backward-compat shim that delegates to
    ``run_derek_pre_tipoff_refresh``.
  - The contract verifier writes BOTH
    ``derek_pre_tipoff_refresh_contract_<date>.json`` and the legacy
    ``derek_near_lineup_contract_<date>.json`` so downstream readers do
    not break.

These tests are text-only (no dynamic module imports) so they are safe
to run inside any environment without the project's full dependency
tree loaded.
"""
from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "daily_pmf_delivery.yml"


class WorkflowRenameTest(unittest.TestCase):
    """daily_pmf_delivery.yml carries both the new job ID and the
    legacy mode alias."""

    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_new_canonical_job_id_present(self) -> None:
        self.assertIn(
            "derek_pre_tipoff_refresh:",
            self.text,
            "Renamed job ID missing from daily_pmf_delivery.yml.",
        )

    def test_default_dispatch_value_is_new_name(self) -> None:
        self.assertIn(
            "default: derek_pre_tipoff_refresh",
            self.text,
            "Default workflow_dispatch mode should be the new name.",
        )

    def test_legacy_mode_still_accepted_as_dispatch_input(self) -> None:
        self.assertIn(
            "- derek_near_lineup",
            self.text,
            "Legacy mode option must remain so existing dispatches "
            "keep working.",
        )

    def test_if_condition_accepts_both_modes(self) -> None:
        self.assertIn(
            "github.event.inputs.mode == 'derek_pre_tipoff_refresh' "
            "|| github.event.inputs.mode == 'derek_near_lineup'",
            self.text,
            "The derek_pre_tipoff_refresh job must fire on either "
            "mode name (canonical or legacy alias).",
        )

    def test_schedule_bridge_accepts_both_modes(self) -> None:
        self.assertIn(
            "github.event.inputs.mode == 'derek_pre_tipoff_refresh' || "
            "github.event.inputs.mode == 'derek_near_lineup'",
            self.text,
            "derek_schedule_bridge must accept either mode name.",
        )


class PipelineModeDispatchTest(unittest.TestCase):
    """run_daily_delivery_pipeline.py canonicalises and dispatches
    both mode names."""

    def setUp(self) -> None:
        self.text = (SCRIPTS / "run_daily_delivery_pipeline.py").read_text(
            encoding="utf-8"
        )

    def test_canonical_mode_in_run_stamp_map(self) -> None:
        self.assertIn(
            '"derek_pre_tipoff_refresh": "t25"',
            self.text,
            "Canonical mode missing from LEGACY_MODE_TO_RUN_STAMP.",
        )

    def test_legacy_mode_still_in_run_stamp_map(self) -> None:
        self.assertIn(
            '"derek_near_lineup": "t25"',
            self.text,
            "Legacy mode alias missing from LEGACY_MODE_TO_RUN_STAMP "
            "(must still map to t25 so the run stamp stays consistent "
            "regardless of which name the caller uses).",
        )

    def test_canonical_function_exists(self) -> None:
        self.assertIn(
            "def run_derek_pre_tipoff_refresh(",
            self.text,
            "Canonical Python function missing.",
        )

    def test_legacy_shim_function_exists(self) -> None:
        self.assertIn(
            "def run_derek_near_lineup(",
            self.text,
            "Legacy shim function missing.",
        )
        self.assertIn(
            "return run_derek_pre_tipoff_refresh(",
            self.text,
            "Legacy shim must delegate to the canonical function.",
        )

    def test_dispatch_elif_accepts_both_modes(self) -> None:
        # Robust to whitespace inside the set literal.
        # All three of these must appear in the dispatch elif clause:
        snippet = (
            'elif internal in {"derek_pre_tipoff_refresh", '
            '"derek_near_lineup", "pre_close"}:'
        )
        self.assertIn(
            snippet,
            self.text,
            "Pipeline dispatch elif clause must accept the canonical "
            "name, the legacy alias, and the pre_close alias.",
        )


class DeliveryContractRenameTest(unittest.TestCase):
    """PIPELINE_MODE_BY_RUN_MODE points T25 at the new canonical name."""

    def test_run_mode_t25_maps_to_new_pipeline_name(self) -> None:
        text = (
            REPO_ROOT
            / "src"
            / "nba_props_model"
            / "delivery"
            / "delivery_contract.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            'RunMode.T25: "derek_pre_tipoff_refresh",',
            text,
            "RunMode.T25 must canonically map to the new pipeline name.",
        )


class ContractVerifierDualWriteTest(unittest.TestCase):
    """verify_derek_near_lineup_contract.py writes BOTH filenames."""

    def setUp(self) -> None:
        self.text = (SCRIPTS / "verify_derek_near_lineup_contract.py").read_text(
            encoding="utf-8"
        )

    def test_writes_new_canonical_filename(self) -> None:
        self.assertIn(
            "derek_pre_tipoff_refresh_contract_",
            self.text,
            "Verifier must write the new canonical filename.",
        )

    def test_still_writes_legacy_filename(self) -> None:
        self.assertIn(
            "derek_near_lineup_contract_",
            self.text,
            "Verifier must keep writing the legacy filename so "
            "downstream readers do not break.",
        )


if __name__ == "__main__":
    unittest.main()
