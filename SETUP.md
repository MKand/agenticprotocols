# The Metal Bank of Braveos Agent

The Metal Bank of Braveos is a multi-agent application built using the Google Agent Development Kit (ADK). It simulates a fantasy-themed bank that processes loan applications and handles clandestine requests. The system uses a main orchestrator agent to route user requests to specialized sub-agents and microservices, demonstrating a robust, tool-using, multi-agent architecture.

The core of the application is a `root_agent` that acts as an orchestrator. Based on user input, it can route to:

*   The `metal_bank_agent` for handling loan applications, which in turn uses tools to perform background checks, calculate interest rates, and manage loan data.
*   The `men_without_faces_remote_agent` for "clandestine services" if the user provides the correct password.
*   The `background_check_mcp` and `loan_service_mcp`

This document provides instructions on how to set up and run the Metal Bank of Braveos Agent application.

## Getting Started

### Prerequisites

Make sure you have the following installed on your system:

*   Python 3
*   pip
*   You need to have Vertex AI User role in your Google Cloud Project.

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/MKand/AgenticProtocols_demo.git bank_of_braveos
    cd bank_of_braveos
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r src/requirements.txt
    ```

### Running the Application

1.  **Create a `.env` file:**

    Create a file named `.env` in the root of the project with the following content:

    ```bash
    GOOGLE_CLOUD_PROJECT=<PROJECT_ID>
    GOOGLE_CLOUD_LOCATION=<REGION>
    GOOGLE_GENAI_USE_VERTEXAI=TRUE
    ```

2.  **Run the startup script:**

    The `start.sh` script is provided to start all the services of the application. It loads the environment variables from the `.env` file and starts the dependant services in the background. Namely,
    1. **The Background Check MCP server (port 8002):** A microservice that provides tools for performing "background checks." It returns a risk profile (War-Risk and Reputation scores) for a given entity based on a predefined JSON file.
    2. **The Loan Service MCP server (port 8003):** A microservice that manages a loan database (using SQLite). It provides tools to create new loans and retrieve existing loan data for entities.
    3. **The Men without Faces Remote Agent (port 8001):** A separate, remote agent that handles "clandestine" requests. It is invoked by the main orchestrator agent only when a specific password ("valar morghulis") is detected.

    ```bash
     ./start.sh
    ```

This will start the Background Check MCP on port 8002, the Loan Service MCP on port 8003, and the Men Without Faces Remote Agent on port 8001, and the agent itself on port 8000.

4.  **Stopping the Services:**

    When you are finished, you can run the `teardown.sh` script to stop all the background services that were started by `start.sh`.

    ```bash
    ./teardown.sh
    ```

    Press `Ctrl+C` on the terminal with the ADK web server to stop it.