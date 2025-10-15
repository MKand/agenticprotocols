
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
import os

MCP_SERVER_URL = os.getenv('MCP_SERVER_URL', "http://localhost:8002/mcp")

background_check_tool = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(url=MCP_SERVER_URL),
    tool_filter = ["do_background_check"]
)

def calculate_loan_interest_rate(war_risk: float, reputation: float, tool_context: ToolContext):
    """
    Calculates the final loan interest rate for a Westerosi entity based on risk factors.

    The calculation uses a weighted average of war risk and reputation scores to
    determine a total risk factor, which then adjusts a baseline interest rate.
    
    Args:
        war_risk (float): The entity's War-Risk Score, where 1.0 is maximum risk. 
                          (Expected range: 0.0 to 1.0).
        reputation (float): The entity's Reputation Score, where 1.0 is maximum 
                            reputation (lowest risk). (Expected range: 0.0 to 1.0).
        tool_context (ToolContext): The ADK context object used to manage the 
                                    shared agent state.
    
    State Effects (Updates tool_context.state):
        'loan_interest_rate' (float): The final calculated interest rate, rounded
                                      to two decimal places (e.g., 12.55).
                                      
    Returns:
        dict: A dictionary containing the calculated rate under the key 
              'loan_interest_rate'. Example: `{'loan_interest_rate': 12.55}`.
    """
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