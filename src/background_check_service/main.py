from src.shared.models.loans import LoanRiskProfile
from fastmcp import FastMCP
import logging
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Define MCP server
mcp = FastMCP("Westrosi entity stats for loans")

BACKGROUND_STATS = None

def load_stats():
    with open("./src/background_check_service/background.json") as f:
        return json.load(f)

def _get_stats(entity_name: str):
    entity_name = entity_name.lower()
    global BACKGROUND_STATS
    if BACKGROUND_STATS is None:    
        BACKGROUND_STATS = load_stats()
    try:
        data = BACKGROUND_STATS[entity_name]
    except KeyError:
        return LoanRiskProfile(entity_name=entity_name, war_risk=0.5, reputation=0.0)
    return LoanRiskProfile(entity_name=entity_name, war_risk=data["war_risk"], reputation=data["reputation"])

@mcp.tool()
async def do_background_check(entity_name: str) -> LoanRiskProfile:
    """
    Retrieves the loan risk profile for a specific entity.

    This endpoint returns the war risk and credit trend for a given entity name.
    The data is fetched from a background statistics file.

    Args:
        entity_name: The name of the entity to retrieve the loan risk profile for.

    Returns:
        A LoanRiskProfile object containing the entity's loan risk information.
    """
    return _get_stats(entity_name)
    
@mcp.tool()
def list_supported_entities() -> list[str]:
    """
    Lists all entities that have loan support.

    This endpoint returns a list of entity names for which loan risk profiles
    are available.

    Returns:
        A list of strings, where each string is a supported entity name.
    """
    global BACKGROUND_STATS
    if BACKGROUND_STATS is None:    
        BACKGROUND_STATS = load_stats()
    return list(BACKGROUND_STATS.keys())

if __name__ == "__main__":
   mcp.run(transport="streamable-http", port=8002, host="0.0.0.0")

