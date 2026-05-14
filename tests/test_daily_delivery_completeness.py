"""Tests for audit_daily_delivery_completeness helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load_audit():
    p = REPO / "scripts" / "audit_daily_delivery_completeness.py"
    spec = importlib.util.spec_from_file_location("audit_daily_delivery_completeness", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_passes_allows_optional_missing():
    m = _load_audit()
    rows = [
        {"expected": "optional", "failure_reason": "optional_missing", "exists": False},
        {"expected": "required", "failure_reason": "", "exists": True, "required_columns_present": True},
    ]
    assert m._passes(rows) is True


def test_passes_fails_on_placeholder():
    m = _load_audit()
    rows = [
        {
            "expected": "required",
            "failure_reason": "",
            "exists": True,
            "required_columns_present": True,
            "placeholder_value_count": 1,
        }
    ]
    assert m._passes(rows) is False


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
