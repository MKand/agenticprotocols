
import uvicorn
from src.adk_menwithoutfaces.agent import a2a_app
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PORT = os.getenv("PORT", "8000")
HOST = os.getenv("HOST", "0.0.0.0")

if __name__ == "__main__":
    logger.info(f"Starting Men without Faces Agent server on http://{HOST}:{PORT}")
    uvicorn.run(a2a_app.build(), host=HOST, port=int(PORT))
