from google.adk.tools.tool_context import ToolContext

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
        
    # Check for the password in a case-insensitive manner.
    parsed_message = message.lower()
    if "valar morghulis" in parsed_message:
        # If the password is found, set a flag in the agent's state to remember it for the session.
        tool_context.state["men_without_faces_discovered"] = True
        return True
    else:
        return False
