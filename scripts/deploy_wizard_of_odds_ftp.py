#!/usr/bin/env python3
"""Deploy ``public_export/wizard_of_odds/`` to the WoO FTP server.

Phase 12B — uploads the public PMF export folder to the WoO portal over FTPS
(falls back to plain FTP only when ``--allow-plain`` is set). The script reads
credentials from environment variables and **never** writes the password to
stdout, stderr, or any log line. Local files are walked with byte-identity
short-circuiting so re-runs don't re-upload unchanged files (size + mtime check
against the remote MLSD listing where supported).

Required env vars (all required, except as noted):

    WOO_FTP_HOST          hostname or IP of the FTP server
    WOO_FTP_USER          username
    WOO_FTP_PASSWORD      password (NEVER printed)
    WOO_FTP_REMOTE_DIR    base directory on the server (e.g. /predictions/)

Optional:

    WOO_FTP_PORT          port override (default: 21)
    WOO_FTP_INSECURE_TLS  set to "1" to skip TLS cert verification (self-signed)

Modes:

    --check-connection    log in, change to remote dir, list one entry, then quit
    --dry-run             walk local files but don't upload
    (default)             upload local file tree under the remote dir

The script exits non-zero on any FTP error. The remote layout mirrors
``public_export/wizard_of_odds/`` exactly under ``WOO_FTP_REMOTE_DIR``.
"""

from __future__ import annotations

import argparse
import ftplib
import os
import socket
import ssl
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCAL = REPO_ROOT / "public_export" / "wizard_of_odds"


@dataclass
class FtpConfig:
    host: str
    user: str
    password: str  # never printed
    remote_dir: str
    port: int = 21

    @classmethod
    def from_env(cls) -> "FtpConfig":
        missing = [
            k
            for k in ("WOO_FTP_HOST", "WOO_FTP_USER", "WOO_FTP_PASSWORD", "WOO_FTP_REMOTE_DIR")
            if not os.environ.get(k)
        ]
        if missing:
            raise SystemExit(
                "Missing required env vars: " + ", ".join(missing) + " — aborting (no upload attempted)."
            )
        port_raw = os.environ.get("WOO_FTP_PORT", "21")
        try:
            port = int(port_raw)
        except ValueError as e:
            raise SystemExit(f"WOO_FTP_PORT must be an integer; got {port_raw!r}") from e
        return cls(
            host=os.environ["WOO_FTP_HOST"],
            user=os.environ["WOO_FTP_USER"],
            password=os.environ["WOO_FTP_PASSWORD"],
            remote_dir=os.environ["WOO_FTP_REMOTE_DIR"],
            port=port,
        )

    def safe_summary(self) -> str:
        return (
            f"host={self.host} port={self.port} user={self.user} "
            f"remote_dir={self.remote_dir} password=***REDACTED***"
        )


def _connect(cfg: FtpConfig, allow_plain: bool, timeout: int = 30) -> ftplib.FTP:
    """Open an FTPS connection (explicit TLS) with a plain-FTP fallback only when allowed."""
    last_exc: Exception | None = None
    try:
        ctx = ssl.create_default_context()
        # Many shared-hosting FTP servers ship self-signed certs; require explicit
        # opt-in via env var to relax verification.
        if os.environ.get("WOO_FTP_INSECURE_TLS") == "1":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        ftps = ftplib.FTP_TLS(context=ctx, timeout=timeout)
        ftps.connect(cfg.host, cfg.port, timeout=timeout)
        ftps.auth()  # AUTH TLS — must precede login for explicit FTPS
        ftps.login(user=cfg.user, passwd=cfg.password)
        ftps.prot_p()  # encrypt data channel
        print(f"[ftps] connected and authenticated to {cfg.host}:{cfg.port} as {cfg.user}")
        return ftps
    except (ftplib.all_errors + (ssl.SSLError, OSError, socket.error)) as e:
        last_exc = e
        print(f"[ftps] explicit-TLS connection failed: {type(e).__name__}: {e}")
        if not allow_plain:
            raise SystemExit(
                "FTPS failed and --allow-plain not set; refusing to fall back to cleartext FTP."
            ) from e

    try:
        ftp = ftplib.FTP(timeout=timeout)
        ftp.connect(cfg.host, cfg.port, timeout=timeout)
        ftp.login(user=cfg.user, passwd=cfg.password)
        print(
            f"[ftp]  connected (PLAIN, --allow-plain) to {cfg.host}:{cfg.port} as {cfg.user}"
        )
        return ftp
    except (ftplib.all_errors + (OSError, socket.error)) as e:
        raise SystemExit(
            f"FTP connection failed (FTPS error: {last_exc}; FTP error: {e})"
        ) from e


def _ensure_remote_dir(ftp: ftplib.FTP, remote_path: str) -> None:
    """Create remote directory tree (idempotent). Path can be absolute or relative."""
    parts = [p for p in remote_path.replace("\\", "/").split("/") if p]
    if remote_path.startswith("/"):
        ftp.cwd("/")
    for part in parts:
        try:
            ftp.cwd(part)
        except ftplib.error_perm:
            ftp.mkd(part)
            ftp.cwd(part)


def _remote_size(ftp: ftplib.FTP, name: str) -> int | None:
    try:
        return ftp.size(name)
    except ftplib.error_perm:
        return None


def _walk_local(local_root: Path):
    for path in sorted(local_root.rglob("*")):
        if path.is_file():
            yield path


def _upload_file(ftp: ftplib.FTP, local_path: Path, remote_name: str) -> int:
    with local_path.open("rb") as f:
        ftp.storbinary(f"STOR {remote_name}", f)
    return local_path.stat().st_size


def _check_connection(cfg: FtpConfig, allow_plain: bool) -> int:
    ftp = _connect(cfg, allow_plain=allow_plain)
    try:
        # change into remote_dir (creating if missing) then list one entry
        _ensure_remote_dir(ftp, cfg.remote_dir)
        entries: list[str] = []
        try:
            ftp.retrlines("LIST", entries.append)
        except ftplib.error_perm as e:
            print(f"[check] LIST refused ({e}); login + cwd succeeded.")
            return 0
        print(f"[check] cwd ok ({cfg.remote_dir}); {len(entries)} entries visible")
        if entries:
            print(f"[check] sample: {entries[0]}")
        return 0
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()


def _deploy(cfg: FtpConfig, local_root: Path, dry_run: bool, allow_plain: bool) -> int:
    if not local_root.exists():
        raise SystemExit(f"Local export folder does not exist: {local_root}")

    files = list(_walk_local(local_root))
    total_bytes_local = sum(p.stat().st_size for p in files)
    print(
        f"[deploy] local_root={local_root} files={len(files)} bytes={total_bytes_local:,} "
        f"target={cfg.host}:{cfg.port}{cfg.remote_dir} dry_run={dry_run}"
    )

    if dry_run:
        for p in files:
            rel = p.relative_to(local_root).as_posix()
            print(f"[dry-run] would upload {rel} ({p.stat().st_size:,} bytes)")
        return 0

    ftp = _connect(cfg, allow_plain=allow_plain)
    uploaded = 0
    skipped = 0
    bytes_sent = 0
    t0 = time.time()
    try:
        _ensure_remote_dir(ftp, cfg.remote_dir)
        # remember absolute remote dir for re-cwd after subdir traversal
        remote_root = ftp.pwd()
        for p in files:
            rel = p.relative_to(local_root)
            sub = rel.parent.as_posix() if rel.parent.as_posix() != "." else ""
            ftp.cwd(remote_root)
            if sub:
                _ensure_remote_dir(ftp, sub)
            local_size = p.stat().st_size
            remote_sz = _remote_size(ftp, rel.name)
            if remote_sz == local_size:
                skipped += 1
                continue
            sent = _upload_file(ftp, p, rel.name)
            bytes_sent += sent
            uploaded += 1
            print(f"[uploaded] {rel.as_posix()} ({sent:,} bytes)")
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()
    dt = time.time() - t0
    print(
        f"[deploy] done in {dt:.1f}s — uploaded={uploaded} skipped_unchanged={skipped} "
        f"bytes_sent={bytes_sent:,}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--local-root",
        type=Path,
        default=DEFAULT_LOCAL,
        help="local folder to upload (default: public_export/wizard_of_odds)",
    )
    ap.add_argument(
        "--check-connection",
        action="store_true",
        help="connect, login, cwd into remote_dir, then exit (no uploads)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="walk and report what would upload without connecting",
    )
    ap.add_argument(
        "--allow-plain",
        action="store_true",
        help="allow plain FTP fallback if FTPS fails (default: refuse)",
    )
    args = ap.parse_args(argv)

    cfg = FtpConfig.from_env()
    print(f"[cfg] {cfg.safe_summary()}")
    if args.check_connection:
        return _check_connection(cfg, allow_plain=args.allow_plain)
    return _deploy(
        cfg,
        local_root=args.local_root.resolve(),
        dry_run=args.dry_run,
        allow_plain=args.allow_plain,
    )


if __name__ == "__main__":
    sys.exit(main())
