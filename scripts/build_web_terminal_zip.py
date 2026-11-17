#!/usr/bin/env python3
"""Package this repository's tracked Web Terminal architecture into one ZIP.

The repository layout is preserved. No nested archives or executable payloads
are included, and the script never executes project code.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "md90-web-terminal-paper-bot"
ALLOWED_SUFFIXES = {
    ".py", ".pyi", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
    ".html", ".css", ".scss", ".json", ".jsonc", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".md", ".mdx", ".txt", ".sh", ".sql",
    ".svg", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".woff", ".woff2",
}
BLOCKED_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".next", "dist", "build", "coverage"}
BLOCKED_SUFFIXES = {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".db", ".sqlite", ".sqlite3", ".pyc", ".pem", ".key", ".p12", ".pfx"}
BLOCKED_NAMES = {".env", ".env.local", "credentials.json", "secrets.json", "id_rsa", "id_ed25519"}
MAX_FILE_SIZE = 50 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    output = Path("dist/md90-web-terminal-paper-bot.zip")
    output.parent.mkdir(parents=True, exist_ok=True)
    names = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], check=True, capture_output=True).stdout.split(b"\0")
    included: list[tuple[Path, str]] = []
    skipped: dict[str, int] = {}
    for raw in names:
        if not raw:
            continue
        path = ROOT / raw.decode("utf-8")
        relative = PurePosixPath(path.relative_to(ROOT).as_posix())
        reason = None
        if path.is_symlink() or not path.is_file():
            reason = "not_regular_file"
        elif {part.lower() for part in relative.parts} & BLOCKED_DIRS:
            reason = "generated_or_dependency_directory"
        elif relative.name.lower() in BLOCKED_NAMES or relative.name.lower().startswith(".env."):
            reason = "credential_or_environment_file"
        elif path.suffix.lower() in BLOCKED_SUFFIXES:
            reason = "nested_archive_or_sensitive_binary"
        elif path.suffix.lower() not in ALLOWED_SUFFIXES:
            reason = "non_source_or_unreviewed_binary"
        elif path.stat().st_size > MAX_FILE_SIZE:
            reason = "file_size_limit"
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        included.append((path, relative.as_posix()))
    included.sort(key=lambda item: item[1])
    manifest = {
        "schema_version": 1,
        "package": PREFIX,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(),
        "included_file_count": len(included),
        "skipped_file_counts": skipped,
        "authority": "PAPER_SHADOW_ONLY",
        "live_order_route": "DISABLED",
        "files": [{"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256(path)} for path, relative in included],
        "notice": "Source bundle only. No project code or nested ZIP contents were executed or extracted. Review source/license and configure secrets outside this archive.",
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as archive:
        for path, relative in included:
            archive.write(path, f"{PREFIX}/{relative}")
        archive.writestr(f"{PREFIX}/PACKAGE-MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"Built {output}: {len(included)} source/documentation files; live order route DISABLED.")


if __name__ == "__main__":
    main()
