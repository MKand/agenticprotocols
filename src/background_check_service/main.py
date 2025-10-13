from fastapi.openapi.utils import get_openapi
from starlette.responses import PlainTextResponse
from starlette.requests import Request
from src.shared.models.loans import LoanRiskProfile
from fastmcp import FastMCP
import logging
import json


logging.basicConfig(level=logging.INFO)
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8000", "*"]

mcp = FastMCP("Westorosi entity stats for loans")
mcp.openapi_version = "3.0.2"

def get_stats():
    with open("./src/background_check_service/background.json") as f:
        return json.load(f)

BACKGROUND_STATS = get_stats()


@mcp.tool()
# @mcp.resource("resource://{entity_name}/loanprofile")
async def get_entity_stats(entity_name: str) -> LoanRiskProfile:
    """
    Retrieves the loan risk profile for a specific entity.

    This endpoint returns the war risk and credit trend for a given entity name.
    The data is fetched from a background statistics file.

    Args:
        entity_name: The name of the entity to retrieve the loan risk profile for.

    Returns:
        A LoanRiskProfile object containing the entity's loan risk information.
    """
    if BACKGROUND_STATS is not None:
        data = BACKGROUND_STATS[entity_name]
        return LoanRiskProfile(entity_name=entity_name, war_risk=data["war_risk"], credit_trend=data["credit_trend"])
    else:
        return LoanRiskProfile(entity_name=entity_name, war_risk=0.0, credit_trend=0.0)

# @mcp.resource("resource://entities/supported")
@mcp.tool()
def list_supported_entities() -> list[str]:
    """
    Lists all entities that have loan support.

    This endpoint returns a list of entity names for which loan risk profiles
    are available.

    Returns:
        A list of strings, where each string is a supported entity name.
    """
    return list(BACKGROUND_STATS.keys())

if __name__ == "__main__":
   mcp.run(transport="streamable-http", port=8002, host="0.0.0.0")

