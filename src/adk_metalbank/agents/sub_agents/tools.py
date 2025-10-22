from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
import os

# Get MCP server URLs from environment variables, with defaults for local development.
BACKGROUND_CHECK_MCP_SERVER_URL = os.getenv('BACKGROUND_CHECK_MCP_SERVER_URL', "http://localhost:8002/mcp")
LOAN_MCP_SERVER_URL = os.getenv('LOAN_MCP_SERVER_URL', "http://localhost:8003/mcp")


# Create a toolset for the background check service.
# This toolset connects to the background check MCP server and exposes its tools to the agent.
# The `tool_filter` specifically includes only the `do_background_check` tool from that service.
background_check_tool = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=BACKGROUND_CHECK_MCP_SERVER_URL),
    tool_filter = ["do_background_check"]
)

# Create a toolset for the loan service.
# This toolset connects to the loan service MCP server and exposes all of its tools
# (create_loan, get_loans_by_name, cancel_loan_without_elicitation) to the agent.
# MCPToolset doesn't yet have elicitation support so we'll use the tool that doesn't require it.
loan_tool = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=LOAN_MCP_SERVER_URL),
    tool_filter = ["create_loan", "get_loans_by_name", "cancel_loan_without_elicitation"],

)

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
    # Higher war_risk increases risk; higher reputation decreases risk (1.0 - reputation).
    risk_factor = 0.75 * war_risk + 0.25 * (1.0 - reputation)
    
    # Baseline 10% interest (0.1), multiplied by the risk factor (0.9), scaled to a percentage
    interest_rate = (0.9 * risk_factor + 0.1) * 100
    
    # Adjust rate based on loan history.
    # Each open loan increases the rate by 5 percentage points (higher risk).
    interest_rate += nr_open_loans * 5
    # Each closed loan decreases the rate by 0.5 percentage points (lower risk).
    interest_rate -= nr_closed_loans * 0.5
    
    
    # Round the rate for cleaner output and ensure it doesn't fall below a minimum threshold.
    final_rate = round(interest_rate, 2)
    if final_rate < 1:
        final_rate = 1
    
    # Store the calculated rate in the agent's shared state for other agents/tools to access.
    tool_context.state["loan_interest_rate"] = final_rate
    
    # Return the rate directly from the tool for immediate agent consumption or logging.
    return final_rate

calculate_loan_interest_rate_tool = FunctionTool(
    func=calculate_loan_interest_rate,
    require_confirmation=False
)