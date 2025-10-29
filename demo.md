# Model Context Protocol (MCP) Demo

This demo walks through the implementation and usage of the Model Context Protocol (MCP) using examples from the Metal Bank project. Instead of duplicating code, this guide links directly to the implementation files for reference.

## Part 1: Understanding MCP Basics

### What is MCP?

The Model Context Protocol (MCP) is a standardized protocol that enables AI models and agents to interact with external tools and services. It defines how:

- Tools are discovered and described
- Doc string are directly used to create tool descriptions.
- Data is streamed between components
- Error handling and state management work

## Part 2: Simple MCP Server with FastMCP

For a simple MCP server implementation, we use FastMCP in our Background Check Service. FastMCP provides a clean, decorator-based approach to creating MCP tools.

📁 See implementation: [src/background_check_service/main.py](src/background_check_service/main.py)

Key Features:

- Simple setup with FastMCP decorator syntax
- Pydantic models for data structures

Example Tools:

- `do_background_check`: Example of a simple tool that returns structured data

## Part 3: Low-Level MCP Server Implementation

For more complex use cases requiring fine-grained control, we implement a low-level MCP server in our Loan Service.

📁 Implementation examples:

- Main server setup: [src/loan_service/main.py](src/loan_service/main.py)
- Data models: [src/shared/models/loans.py](src/shared/models/loans.py)

Features:

1. Custom session management
2. Tool management
3. Elicitation support

### Elicitation Example

The loan service demonstrates elicitation - getting additional user input during tool execution. Check out the `cancel_loan_with_elicitation` function in [src/loan_service/main.py](src/loan_service/main.py) for an example of user confirmation flow.

## Part 4: Testing with MCP Inspector

The MCP Inspector is essential for testing and debugging MCP servers. Here's how to use it with our services:

1. Start the services using [start.sh](start.sh)

2. Open the [MCP Inspector](https://modelcontextprotocol.io/inspector/) using the command

```sh
npx @modelcontextprotocol/inspector
```

3. Connect to our services (one at a time):
   - Background Check MCP: `http://localhost:8002/mcp`
   - Loan Service MCP: `http://localhost:8003/mcp`

4. Test the tools:
   - Background Check Service:
     - `do_background_check` with entities from [background.json](src/background_check_service/background.json)
     - `calculate_loan_interest_rate` for risk-based calculations
   - Loan Service:
     - `create_loan` for new loans
     - `cancel_loan_with_elicitation` to test user confirmation flows

## Part 5: Agent-to-Agent Protocol (A2A) Implementation

This project demonstrates A2A communication between agents, with an interesting twist in how we implement access control. We'll look at both the proper A2A implementation and our custom approach.

### Standard A2A Implementation

The Men Without phases service is implemented as a standalone A2A-enabled agent:

📁 See implementation: [src/adk_menwithoutphases/agent.py](src/adk_menwithoutphases/agent.py)

Key Features:

- Implements `A2AStarletteApplication` for agent exposure
- Uses `AgentCard` for service discovery and capability description
- Uses `AgentSkills` to describe what the agent can do.
- Custom executor for request processing. Step through a request to understand how a message is processed.
- Optional: Use ADK's to_a2a method to easily convert an agent into an A2A capable agent.

## Part 6: Client Implementation with ADK

### Custom Approach: AgentTool Wrapper

The Metal Bank agent demonstrates how to consume MCP services using Google's Agent Development Kit (ADK).

In this implementation, we wrap the remote A2A agent in an AgentTool. While this is NOT the standard way to use A2A, we use it to implement a passcode check before transferring to the remote agent. This passcode check ("balar worghulis") as a thematic way to access clandestine services. It is **NOT** an implementation of an password/authentication mechanism.:

📁 See implementation: [src/adk_metalbank/agents/tools.py](src/adk_metalbank/agents/tools.py)

Key Components:

- MCP Tool Configuration: [src/adk_metalbank/agents/sub_agents/tools.py](src/adk_metalbank/agents/sub_agents/tools.py)
- Agent Implementation: [src/adk_metalbank/agents/sub_agents/metal_bank_agent.py](src/adk_metalbank/agents/sub_agents/metal_bank_agent.py)

The implementation shows:

1. MCPToolset configuration and usage
2. Integration with LLM agents

