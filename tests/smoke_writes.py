#!/usr/bin/env python3
"""Destructive live write smoke against the user's real Hevy account.

GATED: requires both --yes-really CLI flag AND HEVY_SMOKE_WRITES=1 env var.
Creates timestamped resources that CANNOT be deleted via API — you must
manually clean them up in the Hevy web app.

Usage:
    HEVY_SMOKE_WRITES=1 uv run python tests/smoke_writes.py --yes-really
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from hevy.tools.exercises import _smoke_writes as _write_exercises
from hevy.tools.measurements import _smoke_writes as _write_measurements
from hevy.tools.routines import _smoke_writes as _write_routines
from hevy.tools.workouts import _smoke_writes as _write_workouts

PACKAGE_NAME = "hevy"
SMOKE_TIMESTAMP = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
SMOKE_TAG = f"[mcp-smoke {SMOKE_TIMESTAMP}]"


def get_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root")


async def _call(session: ClientSession, name: str, args: dict | None = None) -> dict | None:
    """Call a tool, return parsed JSON or None on error."""
    try:
        result = await session.call_tool(name, args or {})
        if result.isError:
            text = result.content[0].text if result.content else "<no content>"
            print(f"  ❌ {name}: ERROR {text}")
            return None
        if not result.content:
            print(f"  ✅ {name}: OK (empty)")
            return None
        text = result.content[0].text
        try:
            payload = json.loads(text)
            print(f"  ✅ {name}: OK")
            return payload
        except json.JSONDecodeError:
            print(f"  ✅ {name}: OK ({text[:80]})")
            return None
    except Exception as e:
        print(f"  ❌ {name}: {type(e).__name__} {e}")
        return None


# ========== DOMAIN WRITE PROBES ==========
# Agents A–D append `async def _write_<domain>(session, created)` and register.


WRITE_PROBES: list = [
    _write_exercises,
    _write_routines,
    _write_workouts,
    _write_measurements,
]


async def run_writes() -> dict:
    root = Path(get_project_root())
    load_dotenv(root / ".env")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", f"{PACKAGE_NAME}.server", "--transport", "stdio"],
        env={
            **os.environ,
            "PYTHONPATH": str(root),
            "ENVIRONMENT": "local",
        },
    )
    created: dict = {}
    print("🔌 Connecting via stdio for WRITE smoke...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for probe in WRITE_PROBES:
                await probe(session, created)
    return created


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--yes-really",
        action="store_true",
        help="Required to run destructive writes",
    )
    args = parser.parse_args()
    if not args.yes_really or os.environ.get("HEVY_SMOKE_WRITES") != "1":
        print(
            "⚠️  Refusing to run. This script creates REAL data in your Hevy account\n"
            "    that cannot be deleted via API. To confirm, run:\n"
            "      HEVY_SMOKE_WRITES=1 uv run python tests/smoke_writes.py --yes-really"
        )
        sys.exit(1)

    print(f"🏷️  Smoke tag: {SMOKE_TAG}")
    created = asyncio.run(run_writes())

    print("\n" + "=" * 60)
    print("🧹 MANUAL CLEANUP REQUIRED")
    print("=" * 60)
    print("Hevy's public API does not expose DELETE endpoints.")
    print("The resources created below now live in your Hevy account.")
    print("Open https://hevy.com and remove them manually.\n")
    for k, v in created.items():
        print(f"  • {k}: {v}")
    print(f"\nSearch the app for the tag to find items: {SMOKE_TAG}")


if __name__ == "__main__":
    main()
