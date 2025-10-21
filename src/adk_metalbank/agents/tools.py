from google.adk.tools.tool_context import ToolContext
from google.adk.tools import FunctionTool

def men_without_faces_password_check(password: str, tool_context: ToolContext) -> bool:
    """
    Checks if the provided password matches the secret password for the Men without Faces.
    """
    if password.lower() == "valar morghulis":
        tool_context.state["men_without_faces_discovered"] = True
        return True
    return False

men_without_faces_password_check_tool = FunctionTool(
    func=men_without_faces_password_check,
    require_confirmation=False
)