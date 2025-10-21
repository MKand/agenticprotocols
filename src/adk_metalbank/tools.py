
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
import os

BACKGROUND_CHECK_MCP_SERVER_URL = os.getenv('BACKGROUND_CHECK_MCP_SERVER_URL', "http://localhost:8002/mcp")
LOAN_MCP_SERVER_URL = os.getenv('LOAN_MCP_SERVER_URL', "http://localhost:8003/mcp")


background_check_tool = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=BACKGROUND_CHECK_MCP_SERVER_URL),
    tool_filter = ["do_background_check"]
)

loan_tool = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=LOAN_MCP_SERVER_URL),
)

def men_without_faces_password_check(message: str, tool_context: ToolContext) -> bool:
    """
    Check to see if the user's message contains the password for the Metal Bank.

    Args:
        message (str): The user's message that may contain the password.
        tool_context (ToolContext): The ADK context object used to manage the
                                    shared agent state.
    State Effects (Updates tool_context.state):
        'men_without_faces_discovered' (bool): Set to true if the password matches which indicates that the user can speak to the men without faces agent without needing to give the password again.

    Returns:
        bool: True if the password matches, False otherwise.

    """
        
    parsed_message = message.lower()
    if "valar morghulis" in parsed_message:
        tool_context.state["men_without_faces_discovered"] = True
        return True
    else:
        return False


def calculate_loan_interest_rate(war_risk: float, reputation: float, nr_open_loans: int, nr_closed_loans: int, tool_context: ToolContext) -> float:
    """
    Calculates the loan interest rate based on risk and loan history.

    The calculation uses a weighted average of war risk and reputation to
    determine a base risk factor. This rate is then adjusted based on the
    entity's history of open and closed loans. Each open loan increases the
    rate, while each closed loan decreases it.

    Args:
        war_risk (float): The entity's War-Risk Score, where 1.0 is maximum risk.
                          (Expected range: 0.0 to 1.0).
        reputation (float): The entity's Reputation Score, where 1.0 is maximum
                            reputation (lowest risk). (Expected range: 0.0 to 1.0).
        nr_open_loans (int): The number of existing open loans the entity currently has.
        nr_closed_loans (int): The number of loans the entity has successfully paid off.
        tool_context (ToolContext): The ADK context object used to manage the
                                    shared agent state.

    State Effects (Updates tool_context.state):
        'loan_interest_rate' (float): The final calculated interest rate, rounded
                                      to two decimal places (e.g., 12.55).

    Returns:
        float: The final calculated interest rate (e.g., 12.55).
    """
    if nr_closed_loans is None:
        nr_closed_loans = 0
    if nr_open_loans is None:
        nr_open_loans = 0
        
    # --- Loan Interest Rate Calculation Logic ---
    # Assuming war_risk and reputation are between 0 and 1
    # Higher war_risk increases risk; Lower reputation increases risk.
    risk_factor = 0.75 * war_risk + 0.25 * (1.0 - reputation)
    
    # Baseline 10% interest (0.1), multiplied by the risk factor (0.9), scaled to a percentage
    interest_rate = (0.9 * risk_factor + 0.1) * 100
    
    # Adjust rate based on loan history.
    # Each open loan increases the rate by 5 percentage points (higher risk).
    interest_rate += nr_open_loans * 5
    # Each closed loan decreases the rate by 0.5 percentage points (lower risk).
    interest_rate -= nr_closed_loans * 0.5
    
    
    # Sets the output for the Loan Officer (Root Agent) to see internally
    # Round the rate for cleaner output
    final_rate = round(interest_rate, 2)
    if final_rate < 1:
        final_rate = 1
    
    tool_context.state["loan_interest_rate"] = final_rate
    
    # Return the rate directly from the tool for immediate agent consumption/logging
    return final_rate