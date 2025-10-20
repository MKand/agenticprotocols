from fastmcp import FastMCP
from typing import List, Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select
import logging


logging.basicConfig(level=logging.INFO)

class Loan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    amount: Optional[int] = 1000
    interest_rate_percent: float
    repaid_amount: int = 0
    loan_open: bool = True

sqlite_file_name = "loans.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    with Session(engine) as session:
        return session

mcp = FastMCP("Metal Bank of Braveos entity stats for loans")
mcp.openapi_version = "3.0.2"


@mcp.tool()
def create_loan(loan: Loan) -> Loan:
    """Creates a new loan in the database.

    Args:
        loan: A Loan object containing the details of the new loan to be created.

    Returns:
        The created Loan object, refreshed from the database with its new ID.
    """
    session = get_session()
    session.add(loan)
    session.commit()
    session.refresh(loan)
    return loan

@mcp.tool()
def get_all_loans() -> List[Loan]:
    """Gets a list of all loans from the database.

    Returns:
        A list of all Loan objects currently stored in the database.
        Returns an empty list if no loans are found.
    """
    session = get_session()
    loans = session.exec(select(Loan)).all()
    return loans

@mcp.tool()
def get_loans_by_name(name: str) -> List[Loan]:
    """Gets a list of all loans from the database for a specific entity name.

    Args:
        name: The name of the entity (e.g., 'stark', 'lannister') to filter loans by.

    Returns:
        A list of Loan objects matching the specified name. Returns an empty
        list if no loans are found for that name.
    """
    session = get_session()
    loans = session.exec(select(Loan).where(Loan.name == name)).all()
    return loans

if __name__ == "__main__":
    create_db_and_tables()
    mcp.run(transport="streamable-http", port=8003, host="0.0.0.0")
