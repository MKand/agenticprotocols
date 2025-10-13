# agent/iron_bank_agent.py

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool # The standard ADK tool base class
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.genai import types
from pydantic import Field # Useful for defining tool schemas
import os
import logging
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# --- Configuration ---
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', "http://localhost:8002/mcp")
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "AIzaSyDwuW9HXqDbKPM5nevUB1N_3j99AI0tvuE") 

background_check_tool = MCPToolset(
    connection_params = StreamableHTTPConnectionParams(url=MCP_SERVER_URL)
)

def handle_loan_request(msg, ctx):
        entity = msg.sender
        amount = msg.body["amount"]
        # Fetch external data
        facts = ctx.tools["facts_tool"].invoke({"entity": entity})
        # Price the offer
        offer = 0 # price_loan(entity.split(":")[-1], amount, facts)
        # Respond to the sender
        ctx.reply(
            type="loan.offer",
            body=offer,
            to=entity,
        )

background_check_agent = LlmAgent(
    name="background_check_agent",
    model="gemini-2.0-flash",
    instruction=(
        """ 
        You are a backgound check agent.
        You MUST use the background_check_tool to perform this check.
        """),
        tools=[background_check_tool],
)

# Define the LlmAgent (Synchronously)
root_agent = LlmAgent(
    name="iron_bank_agent_remote",
    model="gemini-2.0-flash",
    instruction=(
        """
        You are a banking agent of the Iron Bank of Braavos. 
        You can request background checks for loan applicants with the help of the background_check_agent, process loan requests to offer a rate, and accept loan payments.
        """
    ),
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[ types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF
        )]
    ),
    # ADK uses the tool's name, description, and schema directly from the object instance
    sub_agents=[background_check_agent],
)

# --- A2A App Creation ---
a2a_app = to_a2a(root_agent, port=int(os.environ.get("PORT", 8001)), host="0.0.0.0", protocol="http")