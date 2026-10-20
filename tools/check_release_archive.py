"""Reject private, generated, or unsafe files in a Crystal Guild release ZIP.

Usage: python tools/check_release_archive.py path/to/Bot.zip

This is a read-only preflight: it never edits an archive or deletes runtime state.
"""
from __future__ import annotations

import argparse
import stat
import sys
import zipfile
from pathlib import PurePosixPath


def violations(path: str) -> list[str]:
    findings: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for entry in archive.infolist():
            raw = entry.filename.replace("\\", "/")
            parts = PurePosixPath(raw).parts
            if not parts:
                continue
            lowered = [piece.lower() for piece in parts]
            name = lowered[-1]
            reason = ""
            if raw.startswith("/") or ".." in parts or (len(parts[0]) > 1 and parts[0][1] == ":"):
                reason = "unsafe archive path"
            elif stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFLNK:
                reason = "symlink entry"
            elif any(piece == "__pycache__" for piece in lowered) or name.endswith(".pyc"):
                reason = "compiled Python cache"
            elif name == ".env" or (name.startswith(".env.") and name != ".env.example"):
                reason = "private environment configuration"
            elif name.endswith((".db", ".db-shm", ".db-wal", ".sqlite", ".sqlite3", ".sqlite-wal", ".sqlite-shm")):
                reason = "database/runtime data"
            elif name in {"state.json", "state.json.tmp"} and len(lowered) >= 2 and lowered[-2] == "overlay":
                reason = "live overlay state"
            elif name in {".tio.tokens.json", "twitch_tokens.json", "oauth_tokens.json"}:
                reason = "private tokens"
            elif "logs" in lowered[:-1] and not entry.is_dir():
                reason = "runtime log"
            if reason:
                findings.append(f"{entry.filename}: {reason}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", help="Release ZIP to validate, without modifying it")
    args = parser.parse_args(argv)
    try:
        findings = violations(args.archive)
    except (OSError, zipfile.BadZipFile) as exc:
        print(f"Could not inspect release ZIP: {exc}", file=sys.stderr)
        return 2
    if findings:
        print(f"FAIL — {len(findings)} unsafe release entries found:")
        for finding in findings:
            print(f"  {finding}")
        print("Rebuild the distribution excluding these files; preserve live persistent state separately.")
        return 1
    print("PASS — no private or generated runtime entries found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
