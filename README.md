# The Metal Bank of Braveos Agent

The Metal Bank of Braveos Agent is a loan application processing system that uses multiple agents to automate the workflow. It includes services for background checks and identity verification to process loan applications efficiently.

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
    git clone <repository-url>
    cd bank_of_braavos
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
    1. The Background Check MCP server
    2. The Men without Faces Remote Agent

    ```bash
    bash start.sh
    ```

This will start the Loan Stats MCP on port 8002 and the Men Without Faces Remote Agent on port 8001.

3.  **Run the Metal Bank of Braveos Agent application:**

    ```bash
    cd src
    adk web
    ```


https://codelabs.developers.google.com/instavibe-adk-multi-agents/instructions#10