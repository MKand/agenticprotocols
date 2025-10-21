# The Metal Bank of Braveos Agent

The Metal Bank of Braveos is a multi-agent application built using the Google Agent Development Kit (ADK). It simulates a fantasy-themed bank that processes loan applications and handles clandestine requests. This project serves as a practical demonstration of building sophisticated, tool-using, and multi-agent systems with ADK, showcasing key agentic protocols like Agent-to-Agent (A2A) communication and Model Context Protocol (MCP) integration.

## Architecture Deep Dive: A Roadmap for Agentic Protocols

The Metal Bank of Braveos employs a layered architecture to manage complex interactions between users, agents, and external services. For a high-level overview of the components and how they are started, please refer to the `Setup.md` file.

### Core Agents and Their Roles

The application's intelligence is distributed across several specialized agents:

*   **`root_agent` (Orchestrator)**: Located in `src/adk_metalbank/agent.py`, this is the primary entry point for user interactions. It acts as a router, analyzing user intent to decide whether to handle a request internally (banking services) or route it to a remote, specialized agent (clandestine services).
*   **`metal_bank_agent` (Loan Officer)**: Defined in `src/adk_metalbank/sub_agents/metal_bank_agent.py`, this agent manages the core banking workflow. It performs background checks, checks existing loans, and presents loan offers. It heavily relies on external tools (MCP services) to fulfill its duties.
*   **`men_without_faces_remote_agent` (Clandestine Service Proxy)**: Found in `src/adk_metalbank/sub_agents/remote_agent.py`, this is a proxy agent that represents the remote "Men without Faces" service. The `root_agent` calls this proxy to delegate clandestine requests.
*   **`men_without_faces_agent` (Clandestine Agent)**: Implemented as a separate microservice in `src/adk_menwithoutfaces/agent.py`, this agent handles "clandestine" requests. It runs independently and communicates with the `metal_bank_orchestrator_agent` via the Agent-to-Agent (A2A) protocol.

### Agent-to-Agent (A2A) Protocol Implementation

A2A is the mechanism for agents to communicate with other agents, whether they are running locally or as separate remote services.

*   **Calling a Remote Agent:**
    *   In `src/adk_metalbank/sub_agents/remote_agent.py`, observe how `men_without_faces_remote_agent` is defined using `RemoteA2aAgent`. This class allows the `root_agent` to discover and interact with the remote "Men without Faces" agent by referencing its `AgentCard` endpoint.
*   **Implementing a Remote Agent (A2A Server):**
    *   The `men_without_faces_agent` in `src/adk_menwithoutfaces/agent.py` demonstrates how to expose an agent as an A2A service using `A2AStarletteApplication`. This makes the agent discoverable and callable by other agents.
    *   `src/adk_menwithoutfaces/a2a_customexecutor.py` contains the custom `MenWithoutFacesAgentExecutor`. This executor defines the specific logic for how the `men_without_faces_agent` processes incoming A2A requests, interacts with its internal `Runner`, and sends responses back. This is a key file for understanding how to customize agent execution within the A2A framework.

### MCP (Model-Context Protocol) Implementations

MCP is the standard for agents to interact with external microservices or tools. It allows agents to leverage specialized functionalities that are outside their core LLM capabilities.

*   **Using MCP Tools in Agents:**
    *   `src/adk_metalbank/sub_agents/tools.py` defines `MCPToolset` instances for `background_check_tool` and `loan_tool`. These toolsets act as proxies, connecting the `metal_bank_agent` to external MCP servers (microservices) that provide specific functionalities.
    *   In `src/adk_metalbank/sub_agents/metal_bank_agent.py`, the `metal_bank_agent` is configured to use these `MCPToolset`s, allowing it to perform actions like `do_background_check` or `create_loan` by calling the respective microservices.
*   **Implementing MCP Servers (Microservices):**
    *   `src/loan_service/main.py` is a concrete example of an MCP server implementation. It uses `fastmcp` to expose functions like `create_loan`, `get_all_loans`, and `get_loans_by_name` as discoverable tools. This microservice manages a SQLite database for loan data.
    *   Similarly, the `background_check_service` (implied by `src/adk_metalbank/sub_agents/tools.py` and `Setup.md`) would be another MCP server, providing tools for risk assessment.

### Local Tools

The `root_agent` uses a local Python function as a tool, directly integrated into its execution.

*   `src/adk_metalbank/tools.py` contains a local tool used by the `root_agent`:
    *   `men_without_faces_password_check`: A simple function to check for a specific password, demonstrating how agents can use local logic to gate access or trigger specific behaviors.
*   `src/adk_metalbank/sub_agents/tools.py` contains a local tool used by the `metal_bank_agent`:
    *   `calculate_loan_interest_rate`: A function that calculates an interest rate based on risk scores and loan history.
