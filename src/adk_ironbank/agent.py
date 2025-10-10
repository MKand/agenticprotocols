# agent/iron_bank_agent.py

# https://a2aprotocol.ai/blog/adk-a2a-guide

from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.genai import types
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset
from src.shared.utils.utils import fetch_openapi, sample_spec_string
import json 
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
import os

from dotenv import load_dotenv
load_dotenv()

os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


mcp_connection = StreamableHTTPConnectionParams(
        url=os.getenv('MCP_SERVER_URL', "http://localhost:8002/mcp"),
    )


background_check_mcp = MCPToolset(
    connection_params=mcp_connection,
)

payments_endpoint_spec = json.loads(sample_spec_string) #fetch_openapi("http://localhost:8081/payments/openapi.json")
payments_check_tool = OpenAPIToolset(
   spec_dict=payments_endpoint_spec,
   spec_str_type="json"
)

class IronBankAgent(Agent):
    def __init__(self,  **kwargs):
        super().__init__( **kwargs)

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

    def handle_loan_accept(msg, ctx):
        tx = ctx.tools["app_payments"].invoke({
            "from": "agent:bank:ironbank",
            "to": msg.sender,
            "amount": msg.body["amount"],
        })
        ctx.reply(
            type="settlement.confirmed",
            body=tx,
            to=msg.sender,
        )


iron_bank_agent = IronBankAgent(
    name="iron_bank_agent",
    model="gemini-2.0-flash",
    instruction=(
        "You are the agent of the Iron Bank of Braavos. "
        "You evaluate and approve loans from Westerosi houses and entities. "
        "Use the facts tool to assess risk and the payments tool to settle approved loans."
    ),
    tools=[ background_check_mcp],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[ types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF
        )]
    ),
)

a2a_app = to_a2a(iron_bank_agent, port=int(os.environ.get("PORT", 8001)), host="0.0.0.0", protocol="http")

