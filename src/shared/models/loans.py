from pydantic import BaseModel

class LoanRiskProfile(BaseModel):
    entity_name: str
    war_risk: float
    credit_trend: float

    def __init__(self, entity_name: str, war_risk: float, credit_trend: float):
        self.entity_name = entity_name
        self.war_risk = war_risk
        self.credit_trend = credit_trend


