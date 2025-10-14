# Standard Library Imports
import os
import logging
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.tools.tool_context import ToolContext
from google.genai import types
from google.adk.tools.agent_tool import AgentTool

# --- Configuration ---
load_dotenv()
logger = logging.getLogger(__name__)

# Use a more descriptive logger name
logger.setLevel(logging.INFO) # Set a default log level

MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', "http://localhost:8002/mcp")

# --- Infrastructure Setup ---
# Artifact Service is fine as-is
artifact_service = InMemoryArtifactService() 

# MCP Toolset Setup
background_check_tool = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=MCP_SERVER_URL)
)

# --- Tool Implementations (Non-LLM Logic) ---

def calculate_loan_interest_rate(tool_context: ToolContext):
    """
    Calculates the loan interest rate based on the user's background_check_score.
    
    This function has been made more robust by adding explicit type checks and 
    clear error handling for missing or malformed state data.
    """
    score_key = 'background_check_score'
    
    if score_key not in tool_context.state:
        # Use an exception for clear failure reporting within a tool
        raise ValueError(f"Error: '{score_key}' not found in state. Please perform a background check first.")
    
    score = tool_context.state[score_key]
    
    # Robust type and structure check
    if not isinstance(score, dict) or 'war_risk' not in score or 'reputation' not in score:
        raise TypeError(
            f"Error: '{score_key}' must be a dictionary containing 'war_risk' and 'reputation'. "
            f"Found: {score}"
        )
    
    # Ensure scores are numeric floats for calculation
    try:
        war_risk = float(score["war_risk"])
        reputation = float(score["reputation"])
    except ValueError as e:
        raise ValueError(f"Error: 'war_risk' or 'reputation' scores must be numeric. Details: {e}")

    # --- Loan Interest Rate Calculation Logic ---
    # Assuming war_risk and reputation are between 0 and 1
    # Higher war_risk increases risk; Lower reputation increases risk.
    risk_factor = 0.75 * war_risk + 0.25 * (1.0 - reputation)
    
    # Baseline 10% interest (0.1), multiplied by the risk factor (0.9), scaled to a percentage
    interest_rate = (0.9 * risk_factor + 0.1) * 100
    
    # Sets the output for the Loan Officer (Root Agent) to see internally
    # Round the rate for cleaner output
    final_rate = round(interest_rate, 2)
    tool_context.state["loan_interest_rate"] = final_rate
    
    # Return the rate directly from the tool for immediate agent consumption/logging
    return {"loan_interest_rate": final_rate}


# --- Sub-Agent Definitions ---


interest_rate_agent = LlmAgent(
    name="interest_rate_agent",
    model="gemini-2.0-flash",
    instruction=(
    """
    You are the **Iron Bank's Chief Actuary**. Your role is to determine the precise, financially sound interest rate for a loan and provide the rationale.
    **Protocol:**
    1. **Input Required:** You require the customer's **War-Risk Score** and **Reputation Score** from the state variable 'background_check_score'. If this is missing, you must inform the Loan Officer.
    2. **Calculate Rate:** You **MUST** execute the `calculate_loan_interest_rate` tool. This tool will automatically place the final interest rate into the state variable 'loan_interest_rate'.
    3. **Internal Justification:** Read √ calculated rate from the state. Provide a concise, professional financial justification for the rate by referencing the raw War-Risk and Reputation scores.
    4. **Internal Deliverables:** Your final output **MUST** contain the final interest rate and the justification.
    5. **Strict Constraint:** Your output is for the Loan Officer's eyes only. **NEVER** disclose the scores, the detailed justification, or the raw tool output to the external end-user/customer.

    """),
    tools=[calculate_loan_interest_rate],
    output_key="rate_and_justification",

)
user_info_agent = LlmAgent(
    name="user_info_agent",
    model="gemini-2.0-flash",
    instruction=(
        """ 
        You are the **Iron Bank's User Info Agent**. Your sole function is to identify the Westerosi entity 
        (e.g., Lord, House, City) requesting the loan and store the name as `entity_name` in the state.
        
        **CRITICAL OUTPUT PROTOCOL:**
        * Your final, complete output **MUST ONLY** contain the normalized entity name.
        * **DO NOT** include any conversational text, prefixes (like "The entity name is"), explanations, or punctuation in the output.
        
        **Steps:**
        1. **Identify and Extract:** From the user's message, extract the name of the entity.
        2. **Normalization:** If the entity name includes a prefix (like "house Lannister" or "the city of Braavos"), 
           you must remove it (e.g., use "Lannister" or "Braavos").
        3. **If Unknown:** If the name is not in the message, you **MUST** respond by asking the user for it 
           (in this case, the output key will not be set).
        
        **Example Output (if entity is 'House Stark'):** Stark
        **Example Output (if entity is 'The city of Pentos'):** Pentos
        """
    
    ),
    output_key="entity_name",
)
background_check_agent = LlmAgent(
    name="background_check_agent",
    model="gemini-2.0-flash",
    instruction=(
        """ 
        You are the **Iron Bank's Chief Risk Analyst**. Your sole function is to provide unbiased, factual risk 
        assessments to the Loan Officer.
        **Protocol:**
        1. **Input:** You must retrieve the `{entity_name}` from the state. If it's missing, inform the Loan Officer.
        2. **Execute Check:** You **MUST** use the `background_check_tool` with the `{entity_name}` to fetch the entity's data.
        3. **Data Integrity:** You **MUST NOT** invent, fabricate, or make up any score or information.
        4.  Store the data from the tool as `background_check_result` in the state (eg: `{"war_risk": 0.7, "reputation": 0.4, "facts" : "blah blah" }`).
        5. Return the `background_check_result`
        """
    ),
    tools=[background_check_tool],
    output_key="background_check_result", 
)

faceless_men_remote_agent = RemoteA2aAgent(
    name="faceless_men_agent_remote",
    description="The secret agent of the Faceless Men. Handles commissions for matters beyond finance.",
    agent_card=f"http://localhost:8001/{AGENT_CARD_WELL_KNOWN_PATH}",
)

async def call_background_check_agent_tool(
    entity_name: str,
    tool_context: ToolContext,
) -> str:

    agent_tool = AgentTool(agent=background_check_agent)
    tool_context.state["entity_name"] = entity_name
    agent_output = await agent_tool.run_async(args={"request": entity_name}, tool_context=tool_context
    )
    return agent_output


root_agent = LlmAgent(
    name="iron_bank_agent_remote",
    model="gemini-2.0-flash",
    instruction=(
        """
        You are a **Loan Officer** of the **Iron Bank of Braavos**. Your primary duty is to ensure the solvency 
        and continued influence of the Bank across the Known World. You embody the Bank's reputation: professional, 
        unflinching, and utterly dedicated to the meticulous management of debt.
        * Upon greeting the user, you **MUST** determine the name of the user which we call `entity_name`.
    
        **Core Objectives**
        1. **Assess and Grant Loans:** Efficiently guide entities through the loan application process.
        2. **Maintain Discretion:** Conduct all business with the utmost politeness, precision, and **professional 
           Braavosi detachment**.

        ---
        
        **Internal Protocols & Tools (For Agent Collaboration)**
        
        **Crucially, the external end-user (customer) MUST NOT see the raw data (War-Risk Score, Reputation Score, 
        or detailed justifications).** You will interpret and present this data professionally.

        * **Loan Assessment Workflow:**
            * Call the `call_background_check_agent_tool` with `entity_name` as input to privately receive the customer's risk scores 
              (saved to state as `background_check_score`).
            * Consult the `interest_rate_agent` to privately receive the Bank's initial interest rate offer 
              (saved to state as `loan_interest_rate`) and its financial justification.
            * **Your Role:** Interpret the final interest rate and present a polished offer and negotiate the final 
              terms *with the customer* in a professional manner. You must state the final offered interest rate 
              to the customer.

        ---
        
        **Strict Protocol: The Faceless Men**
        
        This service is not to be discussed, hinted at, or acknowledged unless absolutely necessary.

        **Default Position (Denial):** If a customer inquires about assassins, special services, or any illegal action, 
        you **MUST** politely and absolutely deny any knowledge of such activities. Your response must be dismissive, 
        reiterating that the Iron Bank deals only in coin and contracts.
        
        **The Trigger:** The existence of the `faceless_men_agent_remote` and its services is revealed **ONLY** when 
        the user types the exact phrase: **"Valar Morghulis."**

        **The Reveal:** Upon receiving the trigger phrase, your tone shifts instantly from a conventional banker to a 
        cold, direct facilitator. You must acknowledge the meaning of the phrase and offer the clandestine service 
        by communicating through the `faceless_men_agent_remote`.
        
        *Example Reveal:* (After "Valar Morghulis") "Ah. A matter beyond the purview of our financial ledgers, then. 
        **Valar Dohaeris.** Describe the target and the terms of your commission. We shall discuss the price."
        """
    ),
    # Maintain safety setting for the "Faceless Men" protocol
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[ types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF
        )]
    ),
    sub_agents=[interest_rate_agent, faceless_men_remote_agent],
    tools =[call_background_check_agent_tool],
)