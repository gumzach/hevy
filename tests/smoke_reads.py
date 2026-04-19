#!/usr/bin/env python3
"""Live read-only smoke probe against a running Hevy MCP server.

Spawns the server via stdio with ENVIRONMENT=local + LOCAL_API_KEY from .env,
calls every read tool with safe defaults, and threads IDs harvested from list
responses into singular-get calls.

Usage:
    uv run python tests/smoke_reads.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from hevy.tools.exercises import _smoke_reads as _probe_exercises
from hevy.tools.measurements import _smoke_reads as _probe_measurements
from hevy.tools.routines import _smoke_reads as _probe_routines
from hevy.tools.workouts import _smoke_reads as _probe_workouts

PACKAGE_NAME = "hevy"


def get_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root")


def load_env() -> Path:
    root = get_project_root()
    env_file = root / ".env"
    if not env_file.exists():
        raise FileNotFoundError(f".env not found at {env_file}")
    load_dotenv(env_file)
    return root


async def _call(session: ClientSession, name: str, args: dict | None = None) -> dict | None:
    """Call a tool, return parsed JSON from the first content block, or raise."""
    try:
        result = await session.call_tool(name, args or {})
        if result.isError:
            text = result.content[0].text if result.content else "<no content>"
            print(f"  ❌ {name}: ERROR {text}")
            return None
        # The first content block is the BaseModel serialized as JSON text
        if not result.content:
            print(f"  ✅ {name}: OK (empty)")
            return None
        text = result.content[0].text
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            print(f"  ✅ {name}: OK (non-JSON: {text[:80]})")
            return None
        print(f"  ✅ {name}: OK")
        return payload
    except Exception as e:
        print(f"  ❌ {name}: {type(e).__name__} {e}")
        return None


async def _probe_user(session: ClientSession, ctx: dict) -> None:
    print("\n── user ──")
    await _call(session, "get_user_info")


# ========== DOMAIN PROBES ==========
# Sub-agents A–D append their own `async def _probe_<domain>` blocks below and
# register them in the PROBES list.


PROBES = [
    _probe_user,
    _probe_workouts,
    _probe_routines,
    _probe_exercises,
    _probe_measurements,
]


async def main() -> None:
    root = load_env()
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", f"{PACKAGE_NAME}.server", "--transport", "stdio"],
        env={
            **os.environ,
            "PYTHONPATH": str(root),
            "ENVIRONMENT": "local",
        },
    )
    print("🔌 Connecting to Hevy MCP server via stdio...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            print(f"📋 Server advertises {len(tools_response.tools)} tools")
            ctx: dict = {}
            for probe in PROBES:
                await probe(session, ctx)
            print("\n✨ Smoke reads done.")


if __name__ == "__main__":
    asyncio.run(main())
