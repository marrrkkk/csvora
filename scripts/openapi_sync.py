#!/usr/bin/env python3
"""
Export OpenAPI spec from the API (source of truth) into apps/web.

This runs inside the `api` Docker Compose service to ensure we use the same
runtime environment and import paths as production/local compose.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Sync OpenAPI spec from apps/api into apps/web.")
    p.add_argument(
        "--output",
        default="apps/web/public/openapi.json",
        help="Output path for OpenAPI JSON (default: apps/web/public/openapi.json).",
    )
    p.add_argument(
        "--compose-service",
        default="api",
        help="Docker Compose service name for the API (default: api).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate OpenAPI JSON inside the API container.
    # We explicitly json.dumps to ensure stable JSON output.
    cmd = [
        "docker",
        "compose",
        "run",
        "--rm",
        args.compose_service,
        "python",
        "-c",
        (
            "import json; "
            "from app.main import app; "
            "print(json.dumps(app.openapi(), ensure_ascii=False))"
        ),
    ]

    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    spec = json.loads(result.stdout)

    # Pretty-print for easy diffs in PRs.
    out_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote OpenAPI spec -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

