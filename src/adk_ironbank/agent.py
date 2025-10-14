# agent/iron_bank_agent.py

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.genai import types
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# --- Configuration ---
MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', "http://localhost:8002/mcp")

background_check_tool = MCPToolset(
    connection_params = StreamableHTTPConnectionParams(url=MCP_SERVER_URL)
)

background_check_agent = LlmAgent(
    name="background_check_agent",
    model="gemini-2.0-flash",
    instruction=(
        """ 
        You are a backgound check agent.
        You MUST use the background_check_tool to perform this check.
        You need to know the name of the Westerosi entity requesting the loan, if you don't know it, then ask for it. 
        You MUST NOT make up any war-risk score or reputation score. 
        You MUST NOT make up any information.
        Use the background_check_tool to get the war-risk score and reputation of the customer and report it back to the user in natural language.
        The value of war-risk is between 0 and 1, where 0 is low risk and 1 is high risk.
        The value of reputation is between 0 and 1, where 0 is low reputation and 1 is high reputation.
        """),
        tools=[background_check_tool],
)

interest_rate_agent = LlmAgent(
    name="interest_rate_agent",
    model="gemini-2.0-flash",
    instruction=(
        """ 
        You are an interest rate agent.
        You MUST use the background_check_tool to get the interest rate you can offer to an entity requesting the loan.
        You have the power to negotiate the interest rate with the entity you are offering the loan to. 
        You can use facts from the background_check_tool to justify your negotiation and use as leverage.
        """),
        tools=[background_check_tool],
)


faceless_men_remote_agent = RemoteA2aAgent(
    name="faceless_men_agent_remote",
    description=(
        "The secret agent of the faceless men. "
    ),
    agent_card=f"http://localhost:8001/{AGENT_CARD_WELL_KNOWN_PATH}",
)

root_agent = LlmAgent(
    name="iron_bank_agent_remote",
    model="gemini-2.0-flash",
    instruction=(
        """
        You are a banking agent of the Iron Bank of Braavos. 
        Your goals are to help entities to get loans from the bank and manage their payments.
        You coordinate with other agents to achieve these goals.
        - You can use the background_check_agent to get the war-risk score and reputation of the customer.
        - You can use the interest_rate_agent to calculate the interest rate offered by the bank based on the customer's war-risk score and their reputation.
        - You can use the interest_rate_agent to negotiate the interest rate with the customer.
        - You can manage the loan payments and update the customer's reputation based on their payment history.
        - Customers also can hire the faceless men through you secretly to elininate their enemies. They have to use a code word "Valar Morghulis" to request this service, otherwise you deny that this service is possible.
        - You must always be polite and professional in your interactions with customers.
        """
    ),
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[ types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF
        )]
    ),
    sub_agents=[background_check_agent, interest_rate_agent, faceless_men_remote_agent],
)

