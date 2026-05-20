"""BDL lineups endpoint contract tests.

Covers the regression fixed in:
  scripts/fetch_bdl_game_lineups.py
  src/nba_props_model/data/bdl_client.py (get_lineups / get_lineups_status)

Background
----------
The previous implementation called ``https://api.balldontlie.io/nba/v2/lineups``
which BDL responds to with ``404 Route not found``.  The 404 was swallowed
by a bare ``except`` in ``get_lineups`` and the calling script then
emitted ``BDL_LINEUPS_FETCH_PASS`` even though every game had effectively
failed.  These tests pin down the corrected behavior end-to-end.

All tests mock :mod:`requests.get` so the suite is hermetic and does not
require network access or a valid ``BDL_API_KEY``.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from unittest import mock

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
SCRIPTS = REPO_ROOT / "scripts"

# Make the package importable without installing.
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_bdl_client_standalone():
    """Load ``bdl_client.py`` without triggering ``nba_props_model.__init__``.

    The package init runs ``_install_legacy_aliases()`` which cascade-imports
    pandas/pyarrow heavyweights.  On Python 3.9 + macOS that cascade can
    segfault in the sandbox.  These BDL tests only need the ``bdl_client``
    module symbols, so we load the file directly via importlib and register
    fake parent packages so ``from nba_props_model.data.bdl_client import
    ...`` (used by the fetcher script) resolves to the same instance.
    """
    # Stub parent packages so the dotted import path resolves.
    if "nba_props_model" not in sys.modules:
        pkg = types.ModuleType("nba_props_model")
        pkg.__path__ = [str(SRC / "nba_props_model")]
        sys.modules["nba_props_model"] = pkg
    if "nba_props_model.data" not in sys.modules:
        data_pkg = types.ModuleType("nba_props_model.data")
        data_pkg.__path__ = [str(SRC / "nba_props_model" / "data")]
        sys.modules["nba_props_model.data"] = data_pkg

    spec = importlib.util.spec_from_file_location(
        "nba_props_model.data.bdl_client",
        SRC / "nba_props_model" / "data" / "bdl_client.py",
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["nba_props_model.data.bdl_client"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


# Inline source assertions (cheap, no imports) ────────────────────────────


def test_endpoint_url_is_v1_lineups_in_module_source():
    """Module source must reference the v1 endpoint (not nba/v2)."""
    src = (SRC / "nba_props_model" / "data" / "bdl_client.py").read_text()
    assert "https://api.balldontlie.io/v1/lineups" in src
    # The legacy /nba/v2/lineups path must not be used for the get_lineups
    # helpers any more.  (We still allow BASE_V2 as a constant for other
    # endpoints — assert specifically that the lineups route is v1.)
    assert "/nba/v2/lineups" not in src, (
        "lineups endpoint must NOT use /nba/v2/lineups (BDL returns 404 there)"
    )


def test_array_param_game_ids_used_in_source():
    """Source must use the ``game_ids[]`` repeated-array query param."""
    src = (SRC / "nba_props_model" / "data" / "bdl_client.py").read_text()
    assert '"game_ids[]"' in src or "'game_ids[]'" in src, (
        "get_lineups_status must use the game_ids[] array param per BDL spec"
    )


# get_lineups_status — mocked HTTP outcomes ──────────────────────────────


@pytest.fixture
def bdl_client(monkeypatch):
    """Import bdl_client with a fake BDL_API_KEY so module-level imports work."""
    monkeypatch.setenv("BDL_API_KEY", "test-key-for-tests")
    # Drop any cached import so the fixture is hermetic, then load the
    # module directly from disk to bypass the package init.  ``monkeypatch``
    # is used so the ``sys.modules`` entry is restored to its prior value
    # at fixture teardown (otherwise the fresh standalone-loaded module
    # would leak into later tests).
    monkeypatch.delitem(sys.modules, "nba_props_model.data.bdl_client", raising=False)
    return _load_bdl_client_standalone()


def _make_response(status_code: int, json_body: dict | None = None, text: str = ""):
    resp = mock.MagicMock()
    resp.status_code = status_code
    if json_body is not None:
        resp.json.return_value = json_body
    else:
        resp.json.side_effect = ValueError("no json")
    resp.text = text
    return resp


def test_get_lineups_status_uses_array_param(bdl_client):
    """``params`` kwarg passed to requests.get must use the array form."""
    captured = {}

    def fake_get(url, headers=None, params=None, timeout=None):  # noqa: ARG001
        captured["url"] = url
        captured["params"] = params
        return _make_response(200, {"data": [], "meta": {"per_page": 25}})

    with mock.patch.object(bdl_client.requests, "get", side_effect=fake_get):
        bdl_client.get_lineups_status([21707977, 21709238])

    assert captured["url"] == "https://api.balldontlie.io/v1/lineups"
    # requests is given a list of 2-tuples so the URL serializes as
    # ?game_ids[]=21707977&game_ids[]=21709238 — exactly what BDL spec wants.
    assert captured["params"] == [
        ("game_ids[]", 21707977),
        ("game_ids[]", 21709238),
    ]


def test_get_lineups_status_200_empty_is_not_available_yet(bdl_client):
    with mock.patch.object(
        bdl_client.requests,
        "get",
        return_value=_make_response(200, {"data": [], "meta": {"per_page": 25}}),
    ):
        result = bdl_client.get_lineups_status([21707977])
    assert result["status"] == "confirmed_lineups_not_available_yet"
    assert result["http_status"] == 200
    assert result["rows"] == []
    assert result["error"] is None


def test_get_lineups_status_200_with_rows_is_available(bdl_client):
    sample_row = {
        "starter": True,
        "position": "G",
        "player": {"id": 1, "first_name": "Test", "last_name": "Player"},
        "team": {"id": 1, "abbreviation": "TST"},
    }
    with mock.patch.object(
        bdl_client.requests,
        "get",
        return_value=_make_response(200, {"data": [sample_row]}),
    ):
        result = bdl_client.get_lineups_status([21707977])
    assert result["status"] == "lineups_available"
    assert result["http_status"] == 200
    assert result["rows"] == [sample_row]


def test_get_lineups_status_404_is_endpoint_misconfigured(bdl_client):
    with mock.patch.object(
        bdl_client.requests,
        "get",
        return_value=_make_response(404, text='{"error":"Route not found"}'),
    ):
        result = bdl_client.get_lineups_status([21707977])
    assert result["status"] == "endpoint_misconfigured"
    assert result["http_status"] == 404
    assert "Route not found" in (result["error"] or "")


def test_get_lineups_status_401_is_auth_failed(bdl_client):
    with mock.patch.object(
        bdl_client.requests,
        "get",
        return_value=_make_response(401, text="unauthorized"),
    ):
        result = bdl_client.get_lineups_status([21707977])
    assert result["status"] == "auth_failed"
    assert result["http_status"] == 401


def test_get_lineups_status_403_is_auth_failed(bdl_client):
    with mock.patch.object(
        bdl_client.requests,
        "get",
        return_value=_make_response(403, text="forbidden"),
    ):
        result = bdl_client.get_lineups_status([21707977])
    assert result["status"] == "auth_failed"
    assert result["http_status"] == 403


def test_get_lineups_status_network_exception_is_request_failed(bdl_client):
    import requests as _req

    def boom(*_a, **_k):
        raise _req.exceptions.ConnectionError("dns failure")

    with mock.patch.object(bdl_client.requests, "get", side_effect=boom):
        result = bdl_client.get_lineups_status([21707977])
    assert result["status"] == "request_failed"
    assert result["http_status"] is None
    assert "ConnectionError" in (result["error"] or "")


# fetch_bdl_game_lineups.main() — end-to-end with mocked HTTP ────────────


@pytest.fixture
def fetcher(monkeypatch, tmp_path):
    """Import the fetcher script with a tmp artifacts dir and fake BDL key.

    The fetcher script does ``from nba_props_model.data.bdl_client import
    get_lineups, get_lineups_status``.  We pre-load a standalone bdl_client
    into ``sys.modules`` under that exact dotted path so the script's
    import resolves without triggering the heavy ``nba_props_model``
    package init (which segfaults locally on Py3.9 + pandas).

    The fetcher also does a lazy ``import pandas`` inside ``fetch_one`` to
    write normalized CSV/Parquet artifacts.  On Python 3.9 + macOS,
    ``import pandas`` itself segfaults in this sandbox (SIGSEGV cannot be
    caught by ``except Exception``), so we pre-poison ``sys.modules`` with
    a sentinel that turns the import into a catchable ``ImportError``.
    The fetcher already handles that case by skipping the CSV/Parquet
    write — JSON + status remain authoritative.  CI workers with healthy
    pandas exercise the real path.
    """
    monkeypatch.setenv("BDL_API_KEY", "test-key-for-tests")
    # All ``sys.modules`` mutations go through ``monkeypatch`` so the
    # state is restored at fixture teardown.  This is critical for the
    # ``pandas`` entry below: without monkeypatch, the ``None`` sentinel
    # we install to make ``import pandas`` raise ``ImportError`` would
    # persist for the rest of the pytest process and any later test
    # that tried to import pandas (directly or via a module that
    # top-level imports pandas, e.g. ``audit_injury_lineup_run_modes``
    # loaded by ``test_demote_injury_lineup_failures``) would crash with
    # ``ModuleNotFoundError: import of pandas halted; None in sys.modules``.
    monkeypatch.delitem(sys.modules, "nba_props_model.data.bdl_client", raising=False)
    monkeypatch.delitem(sys.modules, "fetch_bdl_game_lineups", raising=False)
    monkeypatch.setitem(sys.modules, "pandas", None)  # type: ignore[arg-type]
    _load_bdl_client_standalone()

    import fetch_bdl_game_lineups as fetcher_module  # noqa: WPS433
    # Redirect on-disk artifacts to the test's tmp_path so we don't pollute
    # the repo's real artifacts/live_lineups/ tree.
    monkeypatch.setattr(fetcher_module, "LIVE_LINEUPS_DIR", tmp_path / "live_lineups")
    return fetcher_module


def _patch_requests(fetcher_module, response):
    """Patch the bdl_client.requests.get under the fetcher's import chain."""
    bdl_client = sys.modules["nba_props_model.data.bdl_client"]
    return mock.patch.object(bdl_client.requests, "get", return_value=response)


def test_main_pass_on_200_empty(fetcher, capsys):
    """HTTP 200 + empty data => exit 0 with PASS line and not_available_yet."""
    resp = _make_response(200, {"data": [], "meta": {"per_page": 25}})
    with _patch_requests(fetcher, resp):
        rc = fetcher.main(
            [
                "--delivery-date",
                "2026-05-15",
                "--game-ids",
                "21707977,21709238",
            ]
        )
    out = capsys.readouterr()
    assert rc == 0
    assert "BDL_LINEUPS_FETCH_PASS" in out.out
    assert "BDL_LINEUPS_FETCH_FAILED" not in out.err
    # On-disk status JSON must show the canonical token.
    status_path = (
        fetcher.LIVE_LINEUPS_DIR
        / "2026-05-15"
        / "21707977"
        / "lineup_status.json"
    )
    payload = json.loads(status_path.read_text())
    assert payload["bdl_fetch_status"] == "confirmed_lineups_not_available_yet"
    assert payload["lineup_confirmed"] is False
    assert payload["lineup_blocker"] == "confirmed_lineups_not_available_yet"


def test_main_pass_on_200_with_rows(fetcher, capsys):
    """HTTP 200 + rows => exit 0 with PASS line and lineups_available."""
    # Provide a minimally-valid 2-team / 5-starters-each payload so the
    # legacy ``_classify`` happy-path also marks the lineup confirmed.
    rows: list[dict] = []
    for tid, abbr in ((1, "AAA"), (2, "BBB")):
        for i, name in enumerate(["P1", "P2", "P3", "P4", "P5", "B1", "B2"]):
            rows.append(
                {
                    "starter": i < 5,
                    "position": "G",
                    "player": {
                        "id": tid * 100 + i,
                        "first_name": f"{name}",
                        "last_name": abbr,
                    },
                    "team": {"id": tid, "abbreviation": abbr},
                }
            )
    resp = _make_response(200, {"data": rows})
    with _patch_requests(fetcher, resp):
        rc = fetcher.main(
            [
                "--delivery-date",
                "2026-05-15",
                "--game-id",
                "21707977",
            ]
        )
    out = capsys.readouterr()
    assert rc == 0
    assert "BDL_LINEUPS_FETCH_PASS" in out.out
    status_path = (
        fetcher.LIVE_LINEUPS_DIR
        / "2026-05-15"
        / "21707977"
        / "lineup_status.json"
    )
    payload = json.loads(status_path.read_text())
    assert payload["bdl_fetch_status"] == "lineups_available"


def test_main_fail_on_404(fetcher, capsys):
    """HTTP 404 => exit 1 with FAILED, status=endpoint_misconfigured."""
    resp = _make_response(404, text='{"error":"Route not found"}')
    with _patch_requests(fetcher, resp):
        rc = fetcher.main(
            [
                "--delivery-date",
                "2026-05-15",
                "--game-id",
                "21707977",
            ]
        )
    out = capsys.readouterr()
    assert rc == 1
    assert "BDL_LINEUPS_FETCH_FAILED" in out.err
    assert "BDL_LINEUPS_FETCH_PASS" not in out.out
    status_path = (
        fetcher.LIVE_LINEUPS_DIR
        / "2026-05-15"
        / "21707977"
        / "lineup_status.json"
    )
    payload = json.loads(status_path.read_text())
    assert payload["bdl_fetch_status"] == "endpoint_misconfigured"
    assert payload["bdl_http_status"] == 404
    assert "HTTP 404" in payload["lineup_blocker"]


def test_main_fail_on_401(fetcher, capsys):
    resp = _make_response(401, text="unauthorized")
    with _patch_requests(fetcher, resp):
        rc = fetcher.main(
            [
                "--delivery-date",
                "2026-05-15",
                "--game-id",
                "21707977",
            ]
        )
    out = capsys.readouterr()
    assert rc == 1
    assert "BDL_LINEUPS_FETCH_FAILED" in out.err
    status_path = (
        fetcher.LIVE_LINEUPS_DIR
        / "2026-05-15"
        / "21707977"
        / "lineup_status.json"
    )
    payload = json.loads(status_path.read_text())
    assert payload["bdl_fetch_status"] == "auth_failed"
    assert payload["bdl_http_status"] == 401


def test_main_fail_on_network_exception(fetcher, capsys):
    import requests as _req

    def boom(*_a, **_k):
        raise _req.exceptions.ConnectionError("dns failure")

    bdl_client = sys.modules["nba_props_model.data.bdl_client"]
    with mock.patch.object(bdl_client.requests, "get", side_effect=boom):
        rc = fetcher.main(
            [
                "--delivery-date",
                "2026-05-15",
                "--game-id",
                "21707977",
            ]
        )
    out = capsys.readouterr()
    assert rc == 1
    assert "BDL_LINEUPS_FETCH_FAILED" in out.err
    status_path = (
        fetcher.LIVE_LINEUPS_DIR
        / "2026-05-15"
        / "21707977"
        / "lineup_status.json"
    )
    payload = json.loads(status_path.read_text())
    assert payload["bdl_fetch_status"] == "request_failed"
    assert payload["bdl_http_status"] is None
    assert "request_failed" in payload["lineup_blocker"]
