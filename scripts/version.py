#!/usr/bin/env python3
"""Bump semantic version in pyproject.toml and optionally create git release artifacts."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


VERSION_RE = re.compile(r'(?m)^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"\s*$')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bump project semantic version.")
    parser.add_argument("part", choices=["major", "minor", "patch"], help="Version part to bump.")
    parser.add_argument("--dry-run", action="store_true", help="Print next version without writing.")
    parser.add_argument(
        "--git",
        action="store_true",
        help="Create release commit and annotated tag after bump.",
    )
    parser.add_argument(
        "--pyproject",
        default="apps/api/pyproject.toml",
        help="Path to pyproject.toml (default: apps/api/pyproject.toml).",
    )
    return parser.parse_args()


def bump_version(current: tuple[int, int, int], part: str) -> tuple[int, int, int]:
    major, minor, patch = current
    if part == "major":
        return (major + 1, 0, 0)
    if part == "minor":
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def run_git(args: list[str]) -> None:
    subprocess.run(["git", *args], check=True)


def main() -> int:
    args = parse_args()
    pyproject_path = Path(args.pyproject)
    text = pyproject_path.read_text(encoding="utf-8")

    match = VERSION_RE.search(text)
    if not match:
        raise SystemExit("Could not find [project].version in pyproject.toml")

    current = tuple(int(part) for part in match.groups())
    next_version_tuple = bump_version(current, args.part)
    current_str = ".".join(str(p) for p in current)
    next_str = ".".join(str(p) for p in next_version_tuple)

    print(f"Current version: {current_str}")
    print(f"Next version:    {next_str}")

    if args.dry_run:
        return 0

    updated = VERSION_RE.sub(f'version = "{next_str}"', text, count=1)
    pyproject_path.write_text(updated, encoding="utf-8")
    print(f"Updated {pyproject_path} -> {next_str}")

    if args.git:
        tag = f"v{next_str}"
        run_git(["add", str(pyproject_path)])
        run_git(["commit", "-m", f"release: {tag}"])
        run_git(["tag", "-a", tag, "-m", f"Release {tag}"])
        print(f"Created git commit and tag: {tag}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

