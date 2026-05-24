"""Phase 13A — shared primitives for the nightly champion/challenger automation.

Used by the seven scripts under scripts/ that implement readiness checking,
challenger training, calibration, validation, promotion, orchestration, and
verification.

Hard rules (echoed in every caller):
- Never market-anchor model-only PMFs.
- Never use Phase 10D / 10D.2 TOV overlays.
- Never alter the champion outside an atomic, lock-guarded promotion.
- Never promote inside the WoO publish window (>= 14:30 UTC).
- Never fabricate outcomes, odds, calibration labels, or market comparisons.
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import errno
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]

SUPPORTED_STATS: tuple[str, ...] = (
    "pts",
    "reb",
    "ast",
    "fg3m",
    "tov",
    "stl",
    "blk",
)

CHAMPION_MODELS_DIR = REPO_ROOT / "artifacts" / "models"
REGISTRY_DIR = CHAMPION_MODELS_DIR / "registry"
CHAMPION_DIR = CHAMPION_MODELS_DIR / "champion"
CHALLENGERS_DIR = CHAMPION_MODELS_DIR / "challengers"

CHAMPION_POINTER_PATH = REGISTRY_DIR / "champion_pointer.json"
FRESH_DELIVERY_POINTER_PATH = REGISTRY_DIR / "fresh_delivery_model_pointer.json"
MODEL_REGISTRY_PATH = REGISTRY_DIR / "model_registry.json"
PROMOTION_LOG_PATH = REGISTRY_DIR / "promotion_log.csv"
PROMOTION_LOCK_PATH = REGISTRY_DIR / "promotion.lock"

NIGHTLY_TRAINING_DIR = REPO_ROOT / "artifacts" / "nightly_training"
TRAINING_READINESS_DIR = REPO_ROOT / "artifacts" / "training_readiness"

# Promotion is forbidden at or after this UTC hour:minute to protect the
# 15:00 UTC WoO monetization run.
PROMOTION_CUTOFF_HOUR = 14
PROMOTION_CUTOFF_MINUTE = 30

# Failed Phase 10D / 10D.2 overlays — must never be referenced by champion
# manifests or production deliveries.
FORBIDDEN_OVERLAY_TOKENS: tuple[str, ...] = (
    "phase10d",
    "phase10d2",
    "phase_10d",
    "phase_10d2",
    "phase10d_independent_validation",
    "phase10d2_tov_mean_preserving",
    "phase10_tov_pmf_root_cause",
)

# Phase 13AN: real overlay references that MUST fail the gate. These are
# the only key names / value patterns the scanner treats as live overlay
# usage. Anything outside this list is a documentation/safety reference
# (e.g. "phase10d_overlays_in_use=false", "no_phase10d_overlays_referenced",
# "no_phase10d_overlays_in_manifests") and is allowed.
REAL_OVERLAY_KEY_NAMES: frozenset[str] = frozenset(
    {
        "phase10d_overlay_path",
        "phase10d_minutes_overlay",
        "phase10d_calibration_overlay",
        "phase10d2_overlay_path",
        "phase10d2_minutes_overlay",
        "phase10d2_calibration_overlay",
        "phase10_tov_pmf_root_cause_overlay",
    }
)

# Path prefixes that, if present in any string value, indicate a live
# overlay artifact reference. Match is case-insensitive substring.
REAL_OVERLAY_PATH_PREFIXES: tuple[str, ...] = (
    "artifacts/phase10d/",
    "artifacts/phase10d2/",
    "phase10d_overlays/",
    "phase10d2_overlays/",
    "/phase10d/",
    "/phase10d2/",
)

# Explicit allowlist of safe gate/status strings that MAY contain
# "phase10d" without being a real overlay reference. The scanner skips
# keys/values that exactly match an entry in this set, OR that contain
# any of these substrings.
SAFE_OVERLAY_REFERENCE_STRINGS: frozenset[str] = frozenset(
    {
        "no_phase10d_overlays_referenced",
        "no_phase10d_overlays_in_manifests",
        "phase10d_overlays_in_use",
        "workflow_no_phase10d_overlays",
        "no_phase10d_overlays",
    }
)


def utcnow() -> _dt.datetime:
    return _dt.datetime.now(tz=_dt.timezone.utc)


def utcnow_iso() -> str:
    return utcnow().replace(microsecond=0).isoformat()


def parse_date(s: str) -> _dt.date:
    return _dt.date.fromisoformat(s)


def is_past_promotion_cutoff(now: _dt.datetime | None = None) -> bool:
    """Return True if the current UTC time is at or past the safe-promote window."""
    now = now or utcnow()
    return (now.hour, now.minute) >= (PROMOTION_CUTOFF_HOUR, PROMOTION_CUTOFF_MINUTE)


def git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def git_short_commit() -> str:
    sha = git_commit()
    return sha[:12] if sha and sha != "unknown" else sha


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json_atomic(path: Path, payload: dict) -> None:
    """Write JSON to ``path`` atomically (tmp file + os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_champion_pointer() -> dict:
    if not CHAMPION_POINTER_PATH.exists():
        raise FileNotFoundError(
            f"champion_pointer.json missing at {CHAMPION_POINTER_PATH}. "
            "Run scripts/promote_challenger_if_validated.py with the bootstrap path "
            "or seed via Phase 13A bootstrap."
        )
    return read_json(CHAMPION_POINTER_PATH)


def champion_model_dir() -> Path:
    """Return the directory that contains the current production model artifacts."""
    pointer = load_champion_pointer()
    rel = pointer.get("model_dir") or "artifacts/models"
    p = (REPO_ROOT / rel).resolve()
    return p


def challenger_dir(as_of_date: str) -> Path:
    return CHALLENGERS_DIR / as_of_date


def nightly_run_dir(as_of_date: str) -> Path:
    return NIGHTLY_TRAINING_DIR / as_of_date


def readiness_dir(as_of_date: str) -> Path:
    return TRAINING_READINESS_DIR / as_of_date


@contextlib.contextmanager
def promotion_lock(timeout_s: float = 0.0) -> Iterator[Path]:
    """Acquire an exclusive promotion lockfile. Delivery jobs win — promotion waits.

    The lockfile is created with O_EXCL so concurrent acquirers conflict. If
    ``timeout_s`` > 0 we retry for that long; otherwise we fail immediately.
    """
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + max(timeout_s, 0.0)
    fd: int | None = None
    while True:
        try:
            fd = os.open(
                str(PROMOTION_LOCK_PATH),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644,
            )
            break
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
            if time.monotonic() >= deadline:
                raise RuntimeError(
                    f"Could not acquire promotion lock at {PROMOTION_LOCK_PATH}. "
                    "Another promotion or delivery job may be holding it. Aborting."
                ) from exc
            time.sleep(0.5)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(
                json.dumps(
                    {
                        "pid": os.getpid(),
                        "acquired_at_utc": utcnow_iso(),
                        "host": os.uname().nodename if hasattr(os, "uname") else "",
                    }
                )
            )
        yield PROMOTION_LOCK_PATH
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(PROMOTION_LOCK_PATH)


def _is_safe_overlay_string(s: str) -> bool:
    """Return True if a string is in the explicit safe-reference allowlist.

    A string is "safe" if it equals one of the SAFE_OVERLAY_REFERENCE_STRINGS
    or contains one of them as a substring (e.g. a longer status field name
    that embeds ``no_phase10d_overlays_referenced``).
    """
    ls = s.lower()
    if ls in SAFE_OVERLAY_REFERENCE_STRINGS:
        return True
    for safe in SAFE_OVERLAY_REFERENCE_STRINGS:
        if safe in ls:
            return True
    return False


def scan_for_forbidden_overlay_tokens(payload: object) -> list[str]:
    """Phase 13AN: structural overlay scanner.

    The previous implementation grepped JSON-like structures for any
    occurrence of ``phase10d`` and used heuristic ``no_*`` / ``not_*``
    prefixes to filter out negations. That misfired on legitimate gate
    status strings like ``no_phase10d_overlays_referenced`` and
    ``no_phase10d_overlays_in_manifests`` that *announce* the absence of
    overlays. The fix below removes the substring-grep approach entirely:

        1. Walk the payload as structured JSON.
        2. Only fail on ``key`` matches that are real overlay artifact
           pointers (``REAL_OVERLAY_KEY_NAMES``).
        3. Only fail on ``string value`` matches that contain a real
           overlay artifact path prefix (``REAL_OVERLAY_PATH_PREFIXES``).
        4. Explicitly allow safe gate/status strings — anything in
           ``SAFE_OVERLAY_REFERENCE_STRINGS`` is skipped.
    """
    found: list[str] = []

    def walk(node: object, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                k_str = str(k)
                # Only fail on exact-known overlay key names. Any "phase10d"
                # appearing inside a non-overlay key (e.g. a gate name) is OK.
                if k_str.lower() in REAL_OVERLAY_KEY_NAMES:
                    found.append(f"{path}.{k_str} [overlay_key]")
                walk(v, f"{path}.{k_str}" if path else k_str)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str):
            if _is_safe_overlay_string(node):
                return
            lower = node.lower()
            for prefix in REAL_OVERLAY_PATH_PREFIXES:
                if prefix in lower:
                    found.append(f"{path}: {node}")
                    return

    walk(payload, "")
    return found


def looks_like_secret(value: str) -> bool:
    """Heuristic: catch obvious API keys / bearer tokens in manifest payloads."""
    if not isinstance(value, str):
        return False
    v = value.strip()
    if len(v) < 16:
        return False
    if v.lower().startswith(("bearer ", "sk-", "pk-")):
        return True
    if "api_key" in v.lower() or "apikey" in v.lower() or "secret" in v.lower():
        # heuristic: looks like an env-looking blob
        if "=" in v and len(v) > 40:
            return True
    return False


def scan_for_secrets(payload: object) -> list[str]:
    found: list[str] = []

    def walk(node: object, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(k, str) and any(
                    tok in k.lower() for tok in ("api_key", "apikey", "secret", "token", "password")
                ):
                    if isinstance(v, str) and v and v.lower() not in ("none", "null", "", "<redacted>"):
                        found.append(f"{path}.{k}" if path else k)
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")
        elif isinstance(node, str):
            if looks_like_secret(node):
                found.append(path)

    walk(payload, "")
    return found


def copy_tree_no_overwrite_pickles(src: Path, dst: Path, *, allow_overwrite: bool) -> list[str]:
    """Copy ``src`` directory contents into ``dst``. Returns list of copied relative paths.

    If ``allow_overwrite`` is False, raises if any destination file already exists.
    """
    copied: list[str] = []
    if not src.exists() or not src.is_dir():
        raise FileNotFoundError(f"Source dir does not exist: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    for root, _dirs, files in os.walk(src):
        rel_root = Path(root).relative_to(src)
        for fname in files:
            src_file = Path(root) / fname
            dst_file = dst / rel_root / fname
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            if dst_file.exists() and not allow_overwrite:
                raise FileExistsError(f"Refusing to overwrite {dst_file}")
            shutil.copy2(src_file, dst_file)
            copied.append(str(dst_file.relative_to(REPO_ROOT)))
    return copied


def list_supported_stats(filter_to: Iterable[str] | None = None) -> list[str]:
    if filter_to is None:
        return list(SUPPORTED_STATS)
    wanted = set(filter_to)
    bad = wanted - set(SUPPORTED_STATS)
    if bad:
        raise ValueError(f"Unsupported stats requested: {sorted(bad)}")
    return [s for s in SUPPORTED_STATS if s in wanted]


def md_table(rows: list[tuple[str, str]]) -> str:
    out = ["| Field | Value |", "| --- | --- |"]
    for k, v in rows:
        out.append(f"| {k} | {v} |")
    return "\n".join(out)
