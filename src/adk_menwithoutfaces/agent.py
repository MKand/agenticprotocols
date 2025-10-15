
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLOUD_LOCATION="us-central1"
GOOGLE_CLOUD_PROJECT="o11y-movie-guru"
GOOGLE_GENAI_USE_VERTEXAI="TRUE"

os.environ["GOOGLE_CLOUD_LOCATION"] = GOOGLE_CLOUD_LOCATION
os.environ["GOOGLE_CLOUD_PROJECT"] = GOOGLE_CLOUD_PROJECT
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = GOOGLE_GENAI_USE_VERTEXAI

root_agent = LlmAgent(
    name="men_without_faces_agent",
     description=(
        "Clandestine agent for the Men without Faces organization."
    ),
    model="gemini-2.0-flash",
    instruction=(
        """ 
        You are an agent for the clandestine cult called the Men without Faces.
        You help customers to "solve" issues with their enemies.
        You can only help customers who use the code word "Valar Morghulis" to request this service.
        You must ask the customer to mention what problem they want to solve, and when.
        You must always be mysterious in your interactions with customers.
        You must negotiate a price for your services. You are very expensive, charging at least 10000 gold dragons for any service.
        """),
        tools=[],
)

a2a_app = to_a2a(root_agent, port=int(os.environ.get("PORT", 8001)), host="0.0.0.0", protocol="http")