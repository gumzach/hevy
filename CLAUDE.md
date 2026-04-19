# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Gumstack MCP server wrapping the Hevy Workout App API. Gumstack is the hosting platform; Gumloop is the downstream consumer that connects MCP tools as nodes in a visual pipeline. Tool output schemas determine what gumloop can wire up downstream, so type annotations are load-bearing.

## Commands

- Install deps: `uv sync`
- Run server locally: `./run.sh` (loads `.env`, sets `PYTHONUNBUFFERED=1`) or `uv run hevy`
- Lint/fix: `uv run ruff check --fix`
- Add package: `uv add <package>`
- Run tests (both require `.env` with `ENVIRONMENT=local` and `LOCAL_API_KEY`):
  - HTTP transport: `uv run python tests/test_http.py` (spawns server subprocess on port 8000)
  - stdio transport: `uv run python tests/test_stdio.py`
- There is no `pytest` suite yet despite AGENTS.md referencing `uv run pytest`; tests are runnable scripts.

## Architecture

### Two places declare every tool
This server exposes 22 tools covering workouts, routines, exercise templates, routine folders,
exercise history, body measurements, and user info. A new tool must be added in **both**:
1. As an `async def` function inside a `hevy/tools/<domain>.py` module, appended to that
   module's `TOOLS = [...]` list. `hevy/server.py` iterates `_DOMAIN_MODULES` at import time
   and registers each entry via `mcp.tool()`.
2. `config.yaml` under `tools:` with `name` matching the function name exactly.

Gumstack only detects tools that appear in `config.yaml`. Missing the entry means the tool silently won't be exposed in the Gumstack UI.

**`config.yaml` descriptions must say *when* to call the tool, not just *what* it does.** Empirically: terse one-liners like `"Get a paginated list of X"` cause Gumloop's tool discovery to underperform — agents don't reliably pick the right tool. The fix is framing every description around the use case (e.g. `"Browse recent workouts — use when summarizing training history or finding a session to reference"`). The Python docstring separately drives LLM decisions at call time, but the `config.yaml` description is what Gumloop's discovery layer and the Gumstack tool picker see.

Every tool must: be `async def`, return a Pydantic `BaseModel` (never a raw `dict`/`list`/
scalar — Gumloop needs named output pins), use `Field(description=...)` on every parameter
and every model field, and call out through the shared `hevy.utils.client.hevy_request(...)`
(no other httpx clients).

### Entry point and dual transport
`hevy.server:main` branches on `ENVIRONMENT`:
- `local` → `mcp.run(transport="streamable-http")` (raw FastMCP)
- anything else → wraps in `GumstackHost(mcp).run(...)` for production deployment

`PORT` defaults to 8000 locally, 8080 in the Dockerfile (Knative convention). A `/health_check` custom route is wired for Knative readiness/liveness probes.

### Credentials flow
`hevy/utils/auth.py::get_credentials()` is async and returns `dict[str, str]` whose keys match `config.yaml`'s `auth.credentials[].name`. In `ENVIRONMENT=local` it reads `LOCAL_<NAME>` env vars; otherwise it delegates to `mcp.gumstack.get_credentials`, which fetches user-entered creds from the Gumstack backend. Never hardcode creds or read them directly from env in tool code — always go through this helper.

Auth type (`cred`, `oauth`, `none`) in `config.yaml` **cannot be changed after server creation** on Gumstack.

### Output schema rules (from AGENTS.md)
Return type annotations drive the schema Gumloop uses for node wiring:
- `BaseModel` (preferred) or `TypedDict` → typed schema
- `dict[str, T]` → root-level dict schema
- `list[T] | int | str | ...` → auto-wrapped as `{"result": <value>}`
- No annotation → unstructured text, breaks gumloop connections

Tool docstrings and `Field(description=...)` on parameters/model fields feed LLM tool selection — describe everything.

### Constraints
- Async tools must use `httpx` (already a dep), not `requests` — no blocking I/O.
- Don't define env vars prefixed `GUMLOOP_` or `GUMSTACK_` — reserved by the platform and will be rejected.
- Keep tools narrow: one tool per operation, for observability and per-tool restriction in Gumloop.

## Project layout

```
config.yaml          # Server metadata, auth, tool manifest (must match tools/)
hevy/
  server.py          # FastMCP instance + dynamic TOOLS registration, main()
  tools/             # Domain-split tool modules; each exports a TOOLS = [...] list
    user.py
    workouts.py      # (added by domain sub-agent)
    routines.py      # (added by domain sub-agent)
    exercises.py     # (added by domain sub-agent)
    measurements.py  # (added by domain sub-agent)
  models/            # Pydantic models per domain + common.py (SetType, RepRange, OperationStatus)
    common.py
    user.py
  utils/
    auth.py          # get_credentials() — local vs gumstack-backed
    client.py        # hevy_request() shared httpx client + HevyAPIError
tests/
  test_http.py       # Subprocess + streamable-http client
  test_stdio.py      # stdio transport client
  smoke_reads.py     # Live read-only smoke probe
  smoke_writes.py    # Gated destructive write smoke (manual cleanup required)
```

## External package index

`gumstack-mcp` is pulled from a private index declared in `pyproject.toml`:
`https://us-west1-python.pkg.dev/gumstack-public/gumstack-mcp/simple/`
