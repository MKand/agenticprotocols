#!/bin/bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

echo "Loading environment variables from .env file..."
source .env

# Start Loan Stats MCP
echo "Starting Loan Stats MCP..."
PORT=8002 .venv/bin/python3 -m src.background_check_service.main &

# Start Men Without Faces Remote Agent
echo "Starting Men Without Faces Remote Agent..."
PORT=8001 .venv/bin/python3 -m uvicorn src.adk_menwithoutfaces.agent:a2a_app --reload --port 8001 --host localhost &

echo "Startup script finished."
