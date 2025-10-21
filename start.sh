#!/bin/bash

# Get the absolute path of the directory where the script is located
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export PYTHONPATH=$PYTHONPATH:$SCRIPT_DIR/src

echo "PYTHONPATH is set to ${PYTHONPATH}"


echo "Loading environment variables from .env file..."
source .env

# Start Background Check MCP
echo "Starting Background Check MCP..."
PORT=8002 .venv/bin/python3 -m src.background_check_service.main &

# Start Loan Service MCP
echo "Starting Loan Service MCP..."
PORT=8003 .venv/bin/python3 -m src.loan_service.main &

# Start Men Without Faces Remote Agent
echo "Starting Men Without Faces Remote Agent..."
PORT=8001 .venv/bin/python3 -m uvicorn src.adk_menwithoutfaces:app --reload --port 8001 --host localhost &

# Start Metal Bank Agent
echo "Starting Metal Bank Agent..."
PORT=8000 .venv/bin/python3 -m uvicorn src.adk_metalbank:app --reload --port 8000 --host localhost &

echo "Startup script finished."
