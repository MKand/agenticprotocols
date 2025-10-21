from google.adk.agents import LlmAgent
from a2a.server.apps import A2AStarletteApplication
from src.adk_menwithoutfaces.a2a_setup import agent_card
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from a2a.server.request_handlers import DefaultRequestHandler
from google.adk.runners import Runner
from a2a.server.tasks import InMemoryTaskStore
from google.adk.sessions import InMemorySessionService
from .a2a_setup import MenWithoutFacesAgentExecutor

import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)



load_dotenv()

GOOGLE_CLOUD_LOCATION="us-central1"
GOOGLE_CLOUD_PROJECT="o11y-movie-guru"
GOOGLE_GENAI_USE_VERTEXAI="TRUE"

os.environ["GOOGLE_CLOUD_LOCATION"] = GOOGLE_CLOUD_LOCATION
os.environ["GOOGLE_CLOUD_PROJECT"] = GOOGLE_CLOUD_PROJECT
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = GOOGLE_GENAI_USE_VERTEXAI


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

runner = Runner(
        agent=root_agent,
        app_name=agent_card.name,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )

agent_executor = MenWithoutFacesAgentExecutor(
    agent=root_agent,
    agent_card=agent_card,
    runner=runner,
    )

request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=InMemoryTaskStore(),
    )

a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

logger.info(f"Agent Name: {agent_card.name}, Version: {agent_card.version}")


#https://github.com/modelcontextprotocol/python-sdk