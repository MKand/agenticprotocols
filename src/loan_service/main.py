from typing import List, Optional, Any
from sqlmodel import Field, Session, SQLModel, create_engine, select
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import mcp.types as types
from mcp.server.lowlevel import Server
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
import uvicorn
from google.adk.tools.function_tool import FunctionTool
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)

sqlite_file_name = "loans.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

class LoanCancelConfimation(BaseModel):
    """
    Schema for collecting user confirmation when cancelling a loan.
    
    This model is used in the elicitation flow where we need explicit user
    confirmation before cancelling a loan, demonstrating MCP's elicitation capabilities.
    """
    confirmed: bool = Field(
        description="Are you willing to accept the risks of cancelling a loan with the Metal Bank?"
    )

class Loan(SQLModel, table=True):
    """
    Core loan data model that maps to the database schema.
    
    This model uses SQLModel which combines SQLAlchemy's ORM features
    with Pydantic's data validation. This enables:
    1. Automatic schema generation
    2. Type validation
    3. Database table mapping
    4. OpenAPI documentation generation
    """
    id: Optional[int] = Field(
        default=None, 
        primary_key=True, 
        description="ID of the loan"
    )
    name: str = Field(
        index=True, 
        description="Name of the entity that recieved the loan"
    )
    amount: float = Field(
        description="The loan amount. Expressed in a currency called dragons"
    )
    interest_rate_percent: float = Field(
        description="The interest percent applied on the loan"
    )
    repaid_amount: float = Field(
        description="The loan amount already repaid. Expressed in a currency called dragons"
    )
    loan_open: bool = Field(
        description="True if the loan still needs to be repaid."
    )

# --- Server Setup ---

# Initialize the low-level MCP server
# This gives us more control over request handling and streaming responses
mcp_server = Server("loan-management-server")

# Set up the StreamableHTTPSessionManager for handling Server-Sent Events (SSE)
# json_response=False allows us to stream raw data instead of wrapping in JSON
session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=False,  # Enable raw streaming mode
    )

# --- Database Setup ---

# Initialize SQLite engine and create tables
engine = create_engine(sqlite_url, echo=True)  # echo=True enables SQL logging
SQLModel.metadata.create_all(engine)  # Create tables if they don't exist

def create_db_session():
    """
    Creates a new database session using a context manager.
    
    Using a context manager ensures the session is properly closed
    even if an error occurs, preventing resource leaks.
    
    Returns:
        Session: A new SQLAlchemy session for database operations.
    """
    with Session(engine) as db_session:
        return db_session


# --- Database Operations ---

def do_get_loans_by_name(db_session: Session, name: str) -> List[Loan]:
    """
    Retrieves all loans for a specific entity from the database.
    
    Args:
        db_session: Active database session
        name: Name of the entity (case-insensitive)
        
    Returns:
        List[Loan]: All loans associated with the entity
    """
    loans = db_session.exec(select(Loan).where(Loan.name == name.lower())).all()
    return loans

# --- Server Lifecycle Management ---

@asynccontextmanager
async def server_lifespan(app: Server) -> AsyncIterator[None]:
    """
    Manages the MCP server's lifecycle using async context management.
    
    This function:
    1. Sets up the StreamableHTTP session manager
    2. Handles graceful shutdown when the server stops
    
    The session_manager.run() context ensures all streaming connections
    are properly closed when the server shuts down.
    
    Args:
        app: The MCP Server instance to manage
        
    Yields:
        None: Control back to the server while it runs
    """
    # Run the session manager for handling streaming connections
    async with session_manager.run():
        yield  # Server runs here

# --- Core Business Logic ---

def create_loan(name: str, amount: float, interest_rate_percent: float) -> int:
    """
    Creates a new loan in the database.

    This function demonstrates basic CRUD operations with SQLModel/SQLAlchemy:
    1. Create a new Loan instance
    2. Add it to the session
    3. Commit the transaction
    4. Refresh to get the generated ID
    
    Args:
        name: Entity name (converted to lowercase for consistency)
        amount: Loan amount in dragons (the currency unit)
        interest_rate_percent: Annual interest rate as a percentage
        
    Returns:
        int: The ID of the newly created loan
        
    Note:
        All new loans start with:
        - repaid_amount = 0
        - loan_open = True
    """
    loan = Loan(
        name=name.lower(), 
        amount=amount, 
        interest_rate_percent=interest_rate_percent, 
        repaid_amount=0, 
        loan_open=True
    )
    db_session = create_db_session()
    db_session.add(loan)
    db_session.commit()
    db_session.refresh(loan)
    return loan.id

def get_all_loans() -> List[Loan]:
    """
    Retrieves all loans from the database.

    This function demonstrates a simple SELECT query using SQLModel.
    Unlike get_loans_by_name, this has no filters and returns all records.
    
    Returns:
        List[Loan]: All loan records in the database.
        Returns an empty list if no loans exist.
        
    Note:
        In a production system, you might want to add pagination
        to handle large numbers of loans efficiently.
    """
    db_session = create_db_session()
    loans = db_session.exec(select(Loan)).all()
    return loans


def get_loans_by_name(name: str) -> List[Loan]:
    """
    Retrieves all loans for a specific entity.

    This function provides a high-level interface to loan queries,
    abstracting away the session management from the caller.
    
    Args:
        name: The entity name to search for (e.g., 'stork', 'clannister')
             Case-insensitive due to lowercase conversion
             
    Returns:
        List[Loan]: All loans for the specified entity.
                   Empty list if no loans found.
                   
    Example:
        >>> loans = get_loans_by_name('stork')
        >>> for loan in loans:
        ...     print(f"Amount: {loan.amount} dragons")
    """
    db_session = create_db_session()
    loans = do_get_loans_by_name(db_session, name)
    return loans


async def cancel_loan_with_elicitation(name: str) -> bool:
    """
    Cancels loans with user confirmation using MCP's elicitation feature.
    
    This function demonstrates several advanced MCP features:
    1. Streaming HTTP for real-time interaction
    2. Elicitation for user confirmation
    3. Schema validation of user responses
    4. Stateful transaction handling
    
    The elicitation flow:
    1. Find all open loans for the entity
    2. If any exist, ask for confirmation
    3. If confirmed, delete the loans
    4. If denied or error, leave loans unchanged
    
    Args:
        name: Entity whose loans should be cancelled
        
    Returns:
        bool: True if loans were cancelled (or none existed)
              False if cancellation was denied
              
    Note:
        This function uses MCP's streamable-http transport to maintain
        an open connection during the elicitation flow, enabling
        real-time interaction with the user.
    """
    # Get open loans for the entity
    db_session = create_db_session()
    loans = do_get_loans_by_name(db_session, name)
    open_loans = [loan for loan in loans if loan.loan_open]
    
    # If no open loans, nothing to cancel
    if len(open_loans) == 0:
        return True
    
    # Get the MCP request context for elicitation
    request_ctx = mcp_server.request_context
    
    # Elicit confirmation from user with a schema-validated response
    result = await request_ctx.session.elicit(
            message=(f"Are you sure you want to cancel {len(open_loans)}? "
                    "Defaulting on a loan granted by The Metal Bank of Braveos "
                    "has had dire consequences to people in the past "),
            requestedSchema=LoanCancelConfimation.model_json_schema(),
        )
    
    # Process the user's response
    if result.action == "accept":
        # Delete all open loans in a single transaction
        for loan in open_loans:
            db_session.delete(loan)
        db_session.commit()    
        return True
    
    return False

async def cancel_loan_without_elicitation(name: str) -> bool:
    """
    Direct loan cancellation without user confirmation.
    
    This is a simpler version of loan cancellation that doesn't use
    elicitation. It's useful for MCP clients that do not support elicitation.
    
    Args:
        name: Entity whose loans should be cancelled
        
    Returns:
        bool: True if loans were cancelled or none existed
        
    Note:
        This function performs the same database operations as
        cancel_loan_with_elicitation but without the interactive
        confirmation step.
    """
    db_session = create_db_session()
    loans = do_get_loans_by_name(db_session, name)
    open_loans = [loan for loan in loans if loan.loan_open]
    
    if len(open_loans) == 0:
        return True
        
    for loan in open_loans:
        db_session.delete(loan)
    db_session.commit()    
    return True

# --- MCP Tool Handling ---

@mcp_server.call_tool()
async def call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Central handler for all MCP tool calls.
    
    This function demonstrates how to:
    1. Route tool calls to their implementations
    2. Handle arguments consistently
    3. Format responses for the MCP protocol
    4. Support multiple response types (text, image, embedded)
    
    The function uses streamable-http transport, allowing for:
    - Long-running operations
    - Streaming responses
    - Interactive elicitation
    - Real-time updates
    
    Args:
        name: The name of the tool to call
        arguments: Dictionary of tool-specific arguments
        
    Returns:
        list: List of MCP content types (Text, Image, or Embedded)
        
    Raises:
        ValueError: If the requested tool doesn't exist
        
    Note:
        All responses are wrapped in MCP content types to ensure
        proper protocol compliance and streaming support.
    """
    # Route to appropriate tool and wrap response
    if name == "cancel_loan_with_elicitation":
        result = await cancel_loan_with_elicitation(arguments["name"])
        return [types.TextContent(type="text", text=str(result))]
    elif name == "cancel_loan_without_elicitation":
        result = await cancel_loan_without_elicitation(arguments["name"])
        return [types.TextContent(type="text", text=str(result))]
    elif name == "create_loan":   
       result = create_loan(arguments["name"], arguments["amount"], 
                          arguments["interest_rate_percent"])
       return [types.TextContent(type="text", text=str(result))]
    elif name == "get_loans_by_name":
        result = get_loans_by_name(arguments["name"])
        return [types.TextContent(type="text", text=str(result))]
    else:
        raise ValueError(f"Tool not found: {name}")

# --- Tool Registration ---

# Convert our functions to MCP tools
# The adk_to_mcp_tool_type converter handles:
# 1. Function signature analysis
# 2. Parameter validation
# 3. Return type conversion
# 4. OpenAPI schema generation

cancel_loan_with_elicitation_tool = adk_to_mcp_tool_type(
    FunctionTool(
        func=cancel_loan_with_elicitation, 
        require_confirmation=False 
    )
)

cancel_loan_without_elicitation_tool = adk_to_mcp_tool_type(
    FunctionTool(
        func=cancel_loan_without_elicitation, 
        require_confirmation=False
    )
)

create_loan_tool = adk_to_mcp_tool_type(
    FunctionTool(
        func=create_loan, 
        require_confirmation=False
    )
)

get_loans_by_name_tool = adk_to_mcp_tool_type(
    FunctionTool(
        func=get_loans_by_name, 
        require_confirmation=False
    )
)

# List of all available tools
tools = [
    create_loan_tool,
    get_loans_by_name_tool,
    cancel_loan_with_elicitation_tool,
    cancel_loan_without_elicitation_tool
]

@mcp_server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    Implements the MCP tool discovery endpoint.
    
    This function enables:
    1. Dynamic tool discovery
    2. Tool capability inspection
    3. OpenAPI schema generation
    4. Client-side code generation
    
    Returns:
        list[types.Tool]: List of available MCP tools and their metadata
    """
    return tools

async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    await session_manager.handle_request(scope, receive, send)

# The ASGI interface definition
starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=server_lifespan,
    )

starlette_app = CORSMiddleware(
        starlette_app,
        allow_origins=["*"],  # Allow all origins
        allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
    )

if __name__ == "__main__":
    uvicorn.run(starlette_app, port=8003, host="0.0.0.0")
