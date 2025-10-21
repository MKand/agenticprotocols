#!/bin/bash

echo "Stopping background services..."

# Function to stop a process on a given port
stop_service() {
  PORT=$1
  SERVICE_NAME=$2
  
  # lsof -t -i:PORT returns the PID of the process listening on that port
  PID=$(lsof -t -i:$PORT)
  
  if [ -n "$PID" ]; then
    echo "Stopping $SERVICE_NAME (PID: $PID) on port $PORT..."
    # Kill the process
    kill $PID
    echo "$SERVICE_NAME stopped."
  else
    echo "$SERVICE_NAME not found on port $PORT."
  fi
}

# Stop the services by port number
stop_service 8000 "Metal Bank Agent"
stop_service 8001 "Men Without Faces Remote Agent"
stop_service 8002 "Background Check MCP"
stop_service 8003 "Loan Service MCP"

echo "Teardown script finished."