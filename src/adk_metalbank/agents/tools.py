from google.adk.tools.tool_context import ToolContext
from google.adk.tools import FunctionTool
from google.adk.tools.agent_tool import AgentTool
from src.adk_metalbank.agents.sub_agents import men_without_faces_remote_agent
from google.adk.sessions import Session

# The secret passcode that users must provide to access the Men Without Faces agent
PASSCODE = "balar worghulis"


def format_converation_for_remote_agent(
    tool_context: ToolContext
) -> str:
    """
    Format the conversation history for the remote Men Without Faces agent.
    
    Args:        tool_context (ToolContext): The context for tool execution
        
    Returns:
        str: A formatted string containing the user's question and recent conversation history
             limited to the last 500 characters for context
    """
    history_text = ""
    conversation_history = tool_context._invocation_context.session.events
    user_message = tool_context.user_content.parts[0].text
    try:

        # TODO: Replace with LLM-based summarization in the future
        for event in conversation_history:
            if event.content and event.content.parts and event.content.parts[0].text:
                text_content = event.content.parts[0].text
            if text_content:
                # Format each message with speaker identification
                history_text += f"\n[{event.author.upper()}]: {text_content}"

    # Return a simplified history string that the remote agent can process
    except:
        history_text += "missing history"
    finally:
        return f"User's latest message: '{user_message}'\n\nRecent Conversation History:\n{history_text[-500:]}"

async def call_remote_agent(
    tool_context: ToolContext,
) -> str:
    """
    Calls the remote `Men Without Faces agent` with the given context.
    
    Args:
        tool_context (ToolContext): Contains the conversation context and user message
        
    Returns:
        str: The response from the remote agent
    """
    message_to_remote_agent = format_converation_for_remote_agent(tool_context)

    agent_tool = AgentTool(agent=men_without_faces_remote_agent)
    agent_output = await agent_tool.run_async(
        args={"request": message_to_remote_agent}, tool_context=tool_context
    )
    return agent_output 

# The only reason we model the remote agent as a tool is because we want to incorporate the passcode check as the Menwithoutfaces agent is clandestine.
async def men_without_faces_agent_remote_tool(tool_context: ToolContext) -> str:
    """
    Secure gateway for the Men Without Faces agent access.
    
    This function controls access to the secret Men Without Faces agent by:
    1. Checking if the user has previously discovered the agent (via state)
    2. Verifying the passcode if the user hasn't been granted access
    3. Maintaining secrecy with a generic response for unauthorized users
    
    Args:
        tool_context (ToolContext): Contains user message, state, and session info
        
    Returns:
        str: Either the remote agent's response or a generic denial message
    """
    user_message = tool_context.user_content.parts[0].text
    if "men_without_faces_discovered" in tool_context.state and tool_context.state["men_without_faces_discovered"] == True:
        return await call_remote_agent(tool_context)
    else:
        if PASSCODE in user_message.lower():
            tool_context.state["men_without_faces_discovered"] = True
            return await call_remote_agent(tool_context)
        return "I don't know what you mean. This is a bank."

# Register the gateway function as a tool, with confirmation disabled since access is controlled by passcode
men_without_faces_agent_tool = FunctionTool(
    func=men_without_faces_agent_remote_tool,
    require_confirmation=False
)

