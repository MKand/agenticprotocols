import os
import logging
import requests
from typing import Any, Dict

# --- Global Configuration ---
# Your MCP server address (assuming it has a simple HTTP endpoint for tool calls)
MCP_SERVER_ADDR = os.getenv('MCP_SERVER_ADDR', 'localhost:8001') 
logger = logging.getLogger(__name__)

# --- Generic MCP Client (HTTP Proxy) ---
class GenericMCPClient:
    """Client to call tools on an external MCP server via a simple HTTP POST endpoint."""
    def __init__(self, mcp_service_addr: str):
        self.mcp_service_addr = mcp_service_addr
        logger.info(f"Initialized GenericMCPClient for {self.mcp_service_addr}")

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Sends a synchronous tool call request via HTTP."""
        try:
            # Assumes the external server exposes tools at /tools/<tool_name>
            url = f"http://{self.mcp_service_addr}/tools/{tool_name}"
            response = requests.post(url, json=kwargs, timeout=10)
            response.raise_for_status()
            
            # The tool result is expected to be returned as JSON
            return response.json()
        except requests.exceptions.ConnectionError as e:
            logger.error(f"MCP service not reachable at {self.mcp_service_addr}: {e}")
            return {"error": "MCP service unavailable."}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling MCP tool '{tool_name}' via HTTP: {e}")
            return {"error": f"Error from MCP service: {e}"}

# Global client instance (must be initialized before the tool function is called)
global_mcp_client = GenericMCPClient(MCP_SERVER_ADDR)