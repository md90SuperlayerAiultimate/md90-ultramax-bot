#!/usr/bin/env python3
"""Create one ZIP bundle from authorized local checkouts of MD90 repositories.

This produces one archive containing intact, clearly separated repository roots;
it does not flatten code into one file. It packages tracked files only, never
clones repositories, never extracts nested archives, and excludes secrets and
build/dependency output. Supply repositories already checked out locally with
permission to use them. No source code is executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

MAX_FILE_BYTES = 50 * 1024 * 1024
EXCLUDED_PARTS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", "dist", "build", "coverage", ".next"}
EXCLUDED_SUFFIXES = {".zip", ".7z", ".rar", ".tar", ".gz", ".tgz", ".pem", ".key", ".p12", ".pfx", ".sqlite", ".sqlite3", ".db"}
EXCLUDED_NAMES = {".env", ".env.local", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}


def list_tracked(root: Path) -> list[Path]:
    result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], check=True, capture_output=True)
    return [root / raw.decode("utf-8") for raw in result.stdout.split(b"\0") if raw]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(root: Path) -> str:
    name = root.name.strip()
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"Unsafe repository directory name: {name!r}")
    return name


def collect(repositories: list[Path], output: Path) -> tuple[list[tuple[Path, str]], list[dict[str, Any]], dict[str, int]]:
    entries: list[tuple[Path, str]] = []
    manifests: list[dict[str, Any]] = []
    omitted: dict[str, int] = {}
    resolved_output = output.resolve()
    seen: set[str] = set()
    for input_root in repositories:
        root = input_root.resolve(strict=True)
        if not (root / ".git").exists():
            raise ValueError(f"Not a Git checkout: {root}")
        repo_name = safe_name(root)
        files = []
        excluded_counts: dict[str, int] = {}
        for path in list_tracked(root):
            rel = PurePosixPath(path.relative_to(root).as_posix())
            reason = None
            if path.is_symlink() or not path.is_file():
                reason = "not_regular_file"
            elif {part.lower() for part in rel.parts} & EXCLUDED_PARTS:
                reason = "dependency_or_generated_directory"
            elif rel.name.lower() in EXCLUDED_NAMES or rel.name.lower().startswith(".env."):
                reason = "secret_or_environment_file"
            elif path.suffix.lower() in EXCLUDED_SUFFIXES:
                reason = "archive_or_sensitive_binary"
            elif path.stat().st_size > MAX_FILE_BYTES:
                reason = "file_size_limit"
            elif path.resolve() == resolved_output:
                reason = "output_archive"
            if reason:
                excluded_counts[reason] = excluded_counts.get(reason, 0) + 1
                omitted[reason] = omitted.get(reason, 0) + 1
                continue
            archive_path = f"md90-all-in-one/{repo_name}/{rel.as_posix()}"
            if archive_path in seen:
                raise ValueError(f"Duplicate archive path: {archive_path}")
            seen.add(archive_path)
            entries.append((path, archive_path))
            files.append({"path": rel.as_posix(), "size_bytes": path.stat().st_size, "sha256": file_hash(path)})
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        manifests.append({"repository": repo_name, "source_checkout": str(root), "commit": head,
                          "included_file_count": len(files), "excluded_file_counts": excluded_counts,
                          "files": files})
    entries.sort(key=lambda item: item[1])
    return entries, manifests, omitted


def create_bundle(repositories: list[Path], output: Path) -> dict[str, Any]:
    entries, repos, omitted = collect(repositories, output)
    package_manifest = {
        "schema_version": 1,
        "bundle": "md90-all-in-one-architecture",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_count": len(repos),
        "included_file_count": len(entries),
        "omitted_file_counts": omitted,
        "authority": "SOURCE_AND_DOCUMENTATION_ONLY",
        "mode": "PAPER/SHADOW; LIVE ORDER SUBMISSION NOT ENABLED",
        "repositories": repos,
        "notes": [
            "Each checkout remains under its own top-level repository directory; code is not flattened or merged blindly.",
            "Only Git-tracked files are included. Nested archives, credentials, dependency folders, generated outputs, and files over the size cap are excluded.",
            "Private repositories must be supplied by an authorized local checkout; this script does not clone or bypass access controls.",
            "No repository code or archive members are executed during packaging.",
            "Review repository licenses, duplicate modules, and security boundaries before combining or deploying components.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    fixed_time = (2024, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, arcname in entries:
            info = zipfile.ZipInfo(arcname, date_time=fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
        info = zipfile.ZipInfo("md90-all-in-one/PACKAGE-MANIFEST.json", date_time=fixed_time)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, json.dumps(package_manifest, indent=2, ensure_ascii=False) + "\n")
    return package_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", action="append", type=Path, required=True, help="Authorized local Git checkout; may be supplied multiple times")
    parser.add_argument("--output", type=Path, default=Path("md90-all-in-one-architecture.zip"))
    args = parser.parse_args()
    manifest = create_bundle(args.repo, args.output)
    print(f"Created {args.output}: {manifest['repository_count']} repositories, {manifest['included_file_count']} tracked files; live order submission remains disabled.")


if __name__ == "__main__":
    main()
