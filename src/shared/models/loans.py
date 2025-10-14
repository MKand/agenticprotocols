from pydantic import BaseModel

class LoanRiskProfile(BaseModel):
    entity_name: str
    war_risk: float
    reputation: float


