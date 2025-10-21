from typing import List, Optional, Any
from sqlmodel import Field, Session, SQLModel, create_engine, select
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import mcp.types as types
from mcp.server.lowlevel import Server
from pydantic import BaseModel
from google.adk.tools.mcp_tool.conversion_utils import adk_to_mcp_tool_type
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.streamable_http import EventStore
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
import uvicorn
from google.adk.tools.function_tool import FunctionTool

logging.basicConfig(level=logging.INFO)

sqlite_file_name = "loans.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

class Loan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, description="ID of the loan")
    name: str = Field(index=True, description="Name of the entity that recieved the loan")
    amount: float = Field(description="The loan amount. Expressed in a currency called dragons")
    interest_rate_percent: float = Field(description="The interest percent applied on the loan")
    repaid_amount: float = Field(description="The loan amount already repaid. Expressed in a currency called dragons")
    loan_open: bool = Field(description="True if the loan still needs to be repaid.")

# Pass lifespan to server
app = Server("loan-management-server")

session_manager = StreamableHTTPSessionManager(
        app=app,
        json_response=False,
    )

engine = create_engine(sqlite_url, echo=True)
SQLModel.metadata.create_all(engine)

def create_session():
    with Session(engine) as session:
        return session

def do_get_loans_by_name(name: str):
    # ctx = app.request_context
    # session = ctx.lifespan_context["session"]
    session = create_session()
    loans = session.exec(select(Loan).where(Loan.name == name.lower())).all()
    return loans


@asynccontextmanager
async def server_lifespan(app: Server) -> AsyncIterator[None]:
    """Manage server startup and shutdown lifecycle."""
    # Initialize resources on startup
    engine = create_engine(sqlite_url, echo=True)
    SQLModel.metadata.create_all(engine)
    async with session_manager.run():
        yield

def create_loan(name: str, amount: float, interest_rate_percent: float) -> int:
    """Creates a new loan in the database.

    Args:
        loan: A Loan object containing the details of the new loan to be created.

    Returns:
        The loan ID.
    """
    # Access lifespan context
    # ctx = app.request_context
    # session = ctx.lifespan_context["session"]
    loan = Loan(name=name.lower(), amount=amount, interest_rate_percent=interest_rate_percent, repaid_amount=0, loan_open=True)
    session = create_session()
    session.add(loan)
    session.commit()
    session.refresh(loan)
    return loan.id

def get_all_loans(method_name:str) -> List[Loan]:
    """Gets a list of all loans from the database.

    Returns:
        A list of all Loan objects currently stored in the database.
        Returns an empty list if no loans are found.
    """
    # ctx = app.request_context
    # session = ctx.lifespan_context["session"]
    session = create_session()
    loans = session.exec(select(Loan)).all()
    return loans


def get_loans_by_name(name: str) -> List[Loan]:
    """Gets a list of all loans from the database for a specific entity name.

    Args:
        name: The name of the entity (e.g., 'stork', 'clannister') to filter loans by.

    Returns:
        A list of Loan objects matching the specified name. Returns an empty
        list if no loans are found for that name.
    """
    loans = do_get_loans_by_name(name)
    return loans


async def cancel_loan(name: str) -> bool:
    """Allows user to cancel a loan.

    Args:
        name: The name of the entity (e.g., 'stork', 'clannister') to filter loans by.

    Returns:
        True if the loan was cancelled, False otherwise.
    """
    loans = do_get_loans_by_name(name)
    open_loans = [loan for loan in loans if loan.loan_open]
    if len(open_loans) == 0:
        return True
    
    ctx = app.request_context
    result = await ctx.elicit(
            message=(f"Are you sure you want to cancel {len(open_loans)}? Defaulting on a loan granted by The Metal Bank of Braveos has had dire consequences to people in the past "),
        )
    if result.action == "accept":
        # session = ctx.lifespan_context["session"]
        # delete loans
        session = create_session()
        for loan in open_loans:
            session.delete(loan)
        session.commit()    
        return True
    return False

@app.call_tool()
async def call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "cancel_loan":
        result = await cancel_loan(arguments["name"])
        return [types.TextContent(type="text", text=str(result))]
    if name == "create_loan":   
       result = create_loan(arguments["name"], arguments["amount"], arguments["interest_rate_percent"])
       return [types.TextContent(type="text", text=str(result))]
    if name == "get_loans_by_name":
        result = get_loans_by_name(arguments["name"])
        return [types.TextContent(type="text", text=str(result))]
    else:
        raise ValueError(f"Tool not found: {name}")

cancel_loan_tool = adk_to_mcp_tool_type(FunctionTool(func=cancel_loan, require_confirmation=False))
create_loan_tool = adk_to_mcp_tool_type(FunctionTool(func=create_loan, require_confirmation=False))
get_loans_by_name_tool = adk_to_mcp_tool_type(FunctionTool(func=get_loans_by_name, require_confirmation=False))

tools = [
    create_loan_tool,
    get_loans_by_name_tool,
    cancel_loan_tool
]

# Sanity check: ensure every input schema is an object
for i, t in enumerate(tools):
    sch = t.inputSchema
    assert isinstance(sch, dict), f"Tool {i} inputSchema must be a dict"
    assert sch.get("type") == "object", f"Tool {i} inputSchema.type must be 'object', got {sch.get('type')}"


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools."""
    return tools

async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    await session_manager.handle_request(scope, receive, send)

starlette_app = Starlette(
        debug=True,
        routes=[
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=server_lifespan,
    )

starlette_app = CORSMiddleware(
        starlette_app,
        allow_origins=["*"],  # Allow all origins - adjust as needed for production
        allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
    )
if __name__ == "__main__":
    uvicorn.run(starlette_app, port=8003, host="0.0.0.0")
