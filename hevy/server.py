import importlib
import logging
import os

from dotenv import load_dotenv
from mcp.gumstack import GumstackHost
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PORT = int(os.environ.get("PORT", 8000))
mcp = FastMCP("hevy", host="0.0.0.0", port=PORT)


@mcp.custom_route("/health_check", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


_DOMAIN_MODULES = [
    "hevy.tools.user",
    "hevy.tools.workouts",
    "hevy.tools.routines",
    "hevy.tools.exercises",
    "hevy.tools.measurements",
]


def _register_tools() -> None:
    registered = 0
    for mod_path in _DOMAIN_MODULES:
        try:
            module = importlib.import_module(mod_path)
        except ImportError as exc:
            logger.warning("Could not import %s: %s (skipping)", mod_path, exc)
            continue
        tools = getattr(module, "TOOLS", [])
        for fn in tools:
            mcp.tool()(fn)
            registered += 1
        logger.info("Registered %d tools from %s", len(tools), mod_path)
    logger.info("Total tools registered: %d", registered)


_register_tools()


def main():
    load_dotenv()
    if os.environ.get("ENVIRONMENT") != "local":
        host = GumstackHost(mcp)
        host.run(host="0.0.0.0", port=PORT)
    else:
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
