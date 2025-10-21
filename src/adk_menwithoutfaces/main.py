import uvicorn
from src.adk_menwithoutfaces.agent import a2a_app
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Load environment variables from a .env file for configuration.
load_dotenv()

# Quit if required env variables are absent
if not all(os.getenv(var) for var in ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION", "GOOGLE_GENAI_USE_VERTEXAI"]):
    logger.error("Missing one or more environment variables: GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, GOOGLE_GENAI_USE_VERTEXAI")
    exit(1)

PORT = os.getenv("PORT", "8000")
HOST = os.getenv("HOST", "0.0.0.0")

if __name__ == "__main__":
    logger.info(f"Starting Men without Faces Agent server on http://{HOST}:{PORT}")
    uvicorn.run(a2a_app.build(), host=HOST, port=int(PORT))
