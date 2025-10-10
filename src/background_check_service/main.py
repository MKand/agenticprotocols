import os
from fastapi.openapi.utils import get_openapi
from src.shared.models.loans import LoanRiskProfile
from starlette.responses import PlainTextResponse
from starlette.requests import Request
from fastmcp import FastMCP
import logging
import json

logging.basicConfig(level=logging.INFO)
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8081", "*"]

mcp = FastMCP("Westorosi entity stats for loans")
mcp.openapi_version = "3.0.2"

def get_stats():
    with open("./src/background_check_service/background.json") as f:
        return json.load(f)

BACKGROUND_STATS = get_stats()


@mcp.resource("resource://{entity_name}/loanprofile")
async def get_entity_stats(entity_name: str) -> LoanRiskProfile:
    if BACKGROUND_STATS is not None:
        data = BACKGROUND_STATS[entity_name]
        return LoanRiskProfile(entity_name=entity_name, war_risk=data["war_risk"], credit_trend=data["credit_trend"])

@mcp.resource("data://entities/supported")
def list_supported_entities() -> list[str]:
    """List entities with loan support."""
    return list(BACKGROUND_STATS.keys())

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


if __name__ == "__main__":
   mcp.run(transport="http", show_banner=True, host="localhost", port=int(os.environ.get("PORT", 8002)))

