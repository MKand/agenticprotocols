import logging
from dotenv import load_dotenv
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

# This defines a remote agent that handles "clandestine services".
# Instead of being defined locally, it's accessed via an HTTP endpoint where its
# AgentCard is published. This allows it to run as a separate microservice.

men_without_phases_remote_agent = RemoteA2aAgent(
    name="men_without_phases_remote_agent",
    description="Clandestine agent for the Men without Phases organization who arranges discreet services that are not directly acknowledged by the Metal Bank.",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)
