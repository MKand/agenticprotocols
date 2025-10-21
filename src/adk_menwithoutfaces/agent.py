from google.adk.agents import LlmAgent
from a2a.server.apps import A2AStarletteApplication
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from a2a.server.request_handlers import DefaultRequestHandler
from google.adk.runners import Runner
from a2a.server.tasks import InMemoryTaskStore
from google.adk.sessions import InMemorySessionService
from src.adk_menwithoutfaces.a2a_customexecutor import MenWithoutFacesAgentExecutor
from a2a.types import AgentCard, AgentSkill, AgentCapabilities

import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# The Agent Card defines the agent's metadata, capabilities, and available skills.
# This information is used by other agents or systems to discover and interact with this agent.
capabilities = AgentCapabilities(streaming=True, tools=True)

# Define the agent's core identity and its exposed functionalities.
agent_card = AgentCard(
    name="men_without_faces_agent",
    description="Clandestine agent for the `Men without Faces` organization.",
    skills=[
        AgentSkill(
            name="arrange_discreet_service",
            id ="arrange_discreet_services",
            description="Arranges discreet and clandestine services that are not directly acknowledged by the Metal Bank.",
            tags=[]
        ),
        AgentSkill(
            name="discuss_price",
            id ="discuss_price",
            description="Negotiate prices for the services offered by the `Men without Faces` organization.",
            tags=[]
        ),
    ],
    capabilities=capabilities,
    url=f'http://localhost:{os.environ.get("PORT", 8001)}',
    version="0.1.0",
    default_input_modes=["text"],
    default_output_modes=["text"]
)   


# This is the core LLM-powered agent. It's configured with a name, model, and a detailed instruction prompt
# that defines its persona and behavior.
root_agent = LlmAgent(
name=agent_card.name,
description=(agent_card.description),
model="gemini-2.0-flash",
instruction=(
    """ 
    You are an agent for the clandestine cult called the `Men without Faces`. 
    You are mysterious and keep your answers short, and sharp.
    You help customers to "solve" issues with their enemies.
    You must ask the customer to mention what problem they want to solve, and when.
    You must always be mysterious in your interactions with customers.
    You must negotiate a price for your services. You are very expensive, charging at least 10000 gold dragons for any service. 
    You do not state what your minimum price is, just that you are expensive.
    """),
    tools=[],
)

# The Runner is responsible for executing the agent's logic, managing sessions,
# and handling memory and artifacts. Here, in-memory services are used for simplicity.
runner = Runner(
        agent=root_agent,
        app_name=agent_card.name,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

# The AgentExecutor connects the agent's runtime (Runner) with the A2A server framework.
# It uses a custom executor to handle the request-response cycle.
agent_executor = MenWithoutFacesAgentExecutor(
    agent=root_agent,
    agent_card=agent_card,
    runner=runner,
    )

# The RequestHandler processes incoming A2A requests, using the agent_executor
# to run the agent and a task store to manage asynchronous operations.
request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

# The A2AStarletteApplication wraps the agent components into a web application
# that can be served over HTTP, making the agent discoverable and interactive.
a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")

"""
A simpler way to create an A2A agent without custom agent_executor would be to do the following

from google.adk.a2a.utils.agent_to_a2a import to_a2a

a2a_app = to_a2a(root_agent, port=8001)

"""
