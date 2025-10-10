from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
import os

GOOGLE_CLOUD_LOCATION="us-central1"
GOOGLE_CLOUD_PROJECT="o11y-movie-guru"
GOOGLE_GENAI_USE_VERTEXAI="TRUE"

os.environ["GOOGLE_CLOUD_LOCATION"] = GOOGLE_CLOUD_LOCATION
os.environ["GOOGLE_CLOUD_PROJECT"] = GOOGLE_CLOUD_PROJECT
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = GOOGLE_GENAI_USE_VERTEXAI

root_agent = RemoteA2aAgent(
    name="iron_bank_agent",
    description=(
        "The agent of the Iron Bank of Braavos"
    ),
    agent_card=f"http://localhost:8001/{AGENT_CARD_WELL_KNOWN_PATH}",
)