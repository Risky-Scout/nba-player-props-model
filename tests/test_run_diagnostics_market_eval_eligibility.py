"""Regression tests for Phase 8 market-eval eligibility wiring in
``scripts/run_diagnostics.py``.

Background
----------
Controlled production-pipeline proof run 26209291095 failed with::

    EVENT_MARKET_BACKTEST_DATE_INVENTORY_PASS wrote
    artifacts/model_diagnostics/event_market_backtest_date_inventory.csv
    [ERROR] PHASE8_MARKET_EVAL_NOT_WIRED_FAIL: no
    eligible_for_event_market_backtest dates
    ##[error]Process completed with exit code 2.

The diagnostics script was invoked with both ``--require-market-eval``
*and* ``--allow-provisional-block`` (the canonical workflow path), yet
the empty-eligibility branch hard-exited 2 anyway. These tests pin the
correct wiring:

* eligible dates present → market-eval runs (the existing behavior is
  preserved structurally; the eligibility branch returns the right
  signal)
* no eligible dates + ``--allow-provisional-block`` → emit a structured
  not-proven verdict (``claim_allowed=false``,
  ``market_superiority_status=not_proven``,
  ``reason=no_eligible_event_market_backtest_dates``) and let the
  caller fall through to write the diagnostics sidecar and return 0
* no eligible dates *without* ``--allow-provisional-block`` → preserve
  the verbatim ``PHASE8_MARKET_EVAL_NOT_WIRED_FAIL`` marker that
  ``scripts/collect_run_warnings.py`` matches as a critical failure
* malformed-input strict markers
  (``MISSING_TRAINING_TABLE``,
  ``event_market_stack_failed``,
  ``n_scored_rows==0``) are not loosened
* no superiority claim is allowed on the soft path
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_diagnostics.py"
COLLECTOR_PATH = REPO_ROOT / "scripts" / "collect_run_warnings.py"


@pytest.fixture(scope="module")
def run_diagnostics_module():
    """Import ``scripts/run_diagnostics.py`` as a module without executing
    its ``main()`` (``__name__`` is the module spec name, not
    ``"__main__"``).
    """
    spec = importlib.util.spec_from_file_location(
        "run_diagnostics_under_test", str(SCRIPT_PATH)
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_soft_payload_with_provisional_block(run_diagnostics_module):
    """``allow_provisional_block=True`` → not-proven verdict.

    Covers user-spec requirement 1 (the soft contract): the payload
    must carry ``claim_allowed=false``,
    ``market_superiority_status=not_proven``,
    ``reason=no_eligible_event_market_backtest_dates``,
    ``market_eval_status=not_proven_no_eligible_dates``, and
    ``eligible_for_event_market_backtest_dates=0``. The
    ``soft_pass=True`` return value tells the caller to fall through
    to the sidecar write and return 0 (so downstream GitHub Actions
    ``needs:`` chains can proceed).
    """
    fields, marker, soft_pass = run_diagnostics_module._no_eligible_dates_payload(
        allow_provisional_block=True
    )

    assert soft_pass is True

    assert fields["market_eval_status"] == "not_proven_no_eligible_dates"
    assert fields["market_superiority_status"] == "not_proven"
    assert (
        fields["market_superiority_block_reason"]
        == "no_eligible_event_market_backtest_dates"
    )
    assert fields["eligible_for_event_market_backtest_dates"] == 0

    # User-spec requirement 2: do not misrepresent that the eval ran.
    assert fields["event_market_eval_ran"] is False
    assert fields["event_market_eval_attempted"] is True

    # User-spec requirement 7: only "success" allowed on this branch is
    # claim_allowed=false / not_proven.
    assert fields["market_superiority_claim_allowed"] is False
    assert fields["claim_allowed"] is False
    assert fields["global_market_superiority_claim_allowed"] is False
    assert fields["eligible_market_subset_superiority_claim_allowed"] is False
    assert fields["model_only_calibration_claim_allowed"] is False
    assert fields["strict_contract_result"] == "blocked_provisional"
    assert fields["promotion_status"] == "MARKET_SUPERIORITY_CONTRACT_BLOCKED"

    assert "PHASE8_MARKET_SUPERIORITY_NOT_PROVEN_NO_ELIGIBLE_DATES" in marker
    assert "reason=no_eligible_event_market_backtest_dates" in marker
    assert "claim_allowed=false" in marker
    assert "market_superiority_status=not_proven" in marker
    assert "market_eval_status=not_proven_no_eligible_dates" in marker
    assert "eligible_for_event_market_backtest_dates=0" in marker


def test_strict_payload_without_provisional_block(run_diagnostics_module):
    """``allow_provisional_block=False`` preserves the existing
    ``PHASE8_MARKET_EVAL_NOT_WIRED_FAIL`` hard-exit-2 contract.

    Covers user-spec requirement 3 (strict mode unchanged in exit
    semantics) and the user-spec requirement 2 invariant
    (``event_market_eval_ran`` must reflect that no eval ran).
    """
    fields, marker, soft_pass = run_diagnostics_module._no_eligible_dates_payload(
        allow_provisional_block=False
    )

    assert soft_pass is False
    assert fields == {
        "market_eval_status": "blocked_no_eligible_dates",
        "event_market_eval_ran": False,
        "event_market_eval_attempted": True,
        "eligible_for_event_market_backtest_dates": 0,
    }
    assert (
        marker
        == "PHASE8_MARKET_EVAL_NOT_WIRED_FAIL: "
        "no eligible_for_event_market_backtest dates"
    )


def test_soft_payload_emits_no_superiority_claim(run_diagnostics_module):
    """No claim_allowed=true / superiority-verified token may appear on
    the soft path.

    Covers user-spec requirement 5: "no market-superiority claim is
    allowed when eligible backtest data is absent".
    """
    fields, marker, _soft_pass = run_diagnostics_module._no_eligible_dates_payload(
        allow_provisional_block=True
    )

    combined = " ".join(
        [marker]
        + [f"{k}={v}" for k, v in fields.items()]
    ).lower()

    forbidden_tokens = (
        "claim_allowed=true",
        "market_superiority_verified",
        "market_superiority_status=proven",
    )
    for token in forbidden_tokens:
        assert token not in combined, (
            f"soft path leaked a superiority signal: {token!r} in {combined!r}"
        )

    for k in (
        "market_superiority_claim_allowed",
        "global_market_superiority_claim_allowed",
        "eligible_market_subset_superiority_claim_allowed",
        "model_only_calibration_claim_allowed",
    ):
        assert fields[k] is False, f"{k} must be False on soft path"


def test_strict_marker_is_not_drifted(run_diagnostics_module):
    """The verbatim strict marker matches what
    ``scripts/collect_run_warnings.py`` flags as critical.

    Prevents accidental marker drift that would silently break the
    warning-collector pipeline.
    """
    _fields, strict_marker, _soft_pass = run_diagnostics_module._no_eligible_dates_payload(
        allow_provisional_block=False
    )

    collector_src = COLLECTOR_PATH.read_text(encoding="utf-8")
    pattern = re.compile(r"PHASE8_MARKET_EVAL_NOT_WIRED_FAIL")
    assert pattern.search(collector_src), (
        "collect_run_warnings.py no longer references "
        "PHASE8_MARKET_EVAL_NOT_WIRED_FAIL — strict-marker drift suspected"
    )
    assert pattern.search(strict_marker), (
        "strict marker drift: expected 'PHASE8_MARKET_EVAL_NOT_WIRED_FAIL' "
        f"prefix, got {strict_marker!r}"
    )


def _collect_run_warnings_critical_patterns() -> list[tuple[str, str]]:
    """Dynamically extract the CRITICAL_PATTERNS list from
    ``scripts/collect_run_warnings.py`` so the regression check covers
    *every* pattern the collector uses, not just the narrow
    ``_FAIL`` one.
    """
    import ast

    src = COLLECTOR_PATH.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CRITICAL_PATTERNS":
                    if not isinstance(node.value, ast.List):
                        raise AssertionError(
                            "CRITICAL_PATTERNS shape changed; static extractor must "
                            "be updated"
                        )
                    out: list[tuple[str, str]] = []
                    for elt in node.value.elts:
                        if not isinstance(elt, ast.Tuple) or len(elt.elts) != 2:
                            raise AssertionError(
                                "CRITICAL_PATTERNS entry shape changed; "
                                "static extractor must be updated"
                            )
                        pat_node, name_node = elt.elts
                        if not (isinstance(pat_node, ast.Constant)
                                and isinstance(name_node, ast.Constant)):
                            raise AssertionError(
                                "CRITICAL_PATTERNS entry must be (str, str) literals"
                            )
                        out.append((str(pat_node.value), str(name_node.value)))
                    return out
    raise AssertionError("CRITICAL_PATTERNS not found in collect_run_warnings.py")


def test_soft_marker_is_not_flagged_as_critical(run_diagnostics_module):
    """The soft marker must not match ANY pattern in
    ``collect_run_warnings.py``'s ``CRITICAL_PATTERNS`` (matched with
    ``re.I`` per line 35 of the collector). Otherwise the warning
    collector would erroneously flag a not-proven verdict as a
    critical failure — partially defeating the soft-pass semantics.

    Bugbot regression: the prior version of this test only checked the
    narrow ``PHASE8_MARKET_EVAL_NOT_WIRED_FAIL`` pattern and missed
    the broader case-insensitive ``market_eval_not_wired`` pattern at
    line 14 of the collector.
    """
    _fields, soft_marker, soft_pass = run_diagnostics_module._no_eligible_dates_payload(
        allow_provisional_block=True
    )
    assert soft_pass is True

    patterns = _collect_run_warnings_critical_patterns()
    assert patterns, "CRITICAL_PATTERNS unexpectedly empty"

    for pat, name in patterns:
        compiled = re.compile(pat, re.I)
        match = compiled.search(soft_marker)
        assert match is None, (
            f"soft marker collides with collect_run_warnings.py critical "
            f"pattern {name!r} (regex {pat!r}, re.I): "
            f"matched substring {match.group(0)!r} in {soft_marker!r}"
        )


def test_eligible_dates_path_still_runs_market_eval():
    """User-spec test 3: when eligible dates are present, the
    market-eval path must still run normally.

    Static-content guard against accidental removal of the eligible
    branch. We assert the eligible branch (``else:`` of the
    ``n_elig == 0`` check) still:

    * invokes ``emw.run_event_market_stack(...)`` with
      ``allow_provisional_block`` plumbed through,
    * sets ``em_payload["event_market_eval_ran"] = True`` only AFTER
      ``run_event_market_stack`` actually runs,
    * sets ``em_payload["market_eval_status"] = "event_market_scored"``
      on success.
    """
    src = SCRIPT_PATH.read_text(encoding="utf-8")

    # The eligible branch must invoke the stack.
    assert "emw.run_event_market_stack(" in src, (
        "eligible path no longer invokes emw.run_event_market_stack; "
        "the market-eval pipeline has been broken"
    )
    # ``allow_provisional_block`` must still be plumbed into the stack
    # call (so the downstream verifier soft-fail also works on the
    # eligible path).
    assert "allow_provisional_block=args.allow_provisional_block" in src, (
        "allow_provisional_block is no longer plumbed into "
        "run_event_market_stack"
    )
    # ``event_market_eval_ran = True`` is the eligible-path canonical
    # marker (per the existing market_eval_status state-machine).
    assert 'em_payload["event_market_eval_ran"] = True' in src, (
        "eligible path no longer marks event_market_eval_ran=True"
    )
    # Successful scoring still emits the canonical status.
    assert 'em_payload["market_eval_status"] = "event_market_scored"' in src, (
        "eligible path no longer emits market_eval_status="
        "event_market_scored on success"
    )


def test_malformed_input_hard_fail_markers_preserved():
    """Static-content guard: the three strict markers covering
    malformed/missing-input branches remain ``sys.exit``-bound in
    ``run_diagnostics.py``.

    Covers user-spec requirements 3 and 4: malformed market-eval
    inputs / unexplained NaNs / broken artifacts / missing training
    table must still hard-fail.
    """
    src = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'MISSING_TRAINING_TABLE' in src, (
        "MISSING_TRAINING_TABLE marker was removed; missing-input contract "
        "is broken"
    )
    assert 'PHASE8_MARKET_EVAL_NOT_WIRED_FAIL event_market_stack_failed' in src, (
        "event_market_stack_failed strict marker was removed; "
        "malformed-stack contract is broken"
    )
    assert 'PHASE8_MARKET_EVAL_NOT_WIRED_FAIL: n_scored_rows==0' in src, (
        "n_scored_rows==0 strict marker was removed; "
        "insufficient-scored-rows contract is broken"
    )
    assert 'sys.exit(3)' in src, "MISSING_TRAINING_TABLE exit-3 was removed"
    # n_scored_rows==0 / event_market_stack_failed / no-eligible-strict all use
    # sys.exit(2); count the strict-fail exits to make sure none were softened.
    assert src.count('sys.exit(2)') >= 3, (
        "Expected at least 3 sys.exit(2) sites (no-eligible strict path, "
        "event_market_stack_failed, n_scored_rows==0); found "
        f"{src.count('sys.exit(2)')}"
    )
