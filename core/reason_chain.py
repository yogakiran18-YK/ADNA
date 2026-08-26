from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime

class ReasonStep(BaseModel):
    step_id: str
    agent_name: str
    input_summary: str
    decision: str
    justification: str
    score_used: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ReasonChain:
    def __init__(self):
        self.chain: List[ReasonStep] = []

    def log_step(
        self,
        step_id: str,
        agent_name: str,
        input_summary: str,
        decision: str,
        justification: str,
        score_used: Optional[float] = None
    ) -> None:
        step = ReasonStep(
            step_id=step_id,
            agent_name=agent_name,
            input_summary=input_summary,
            decision=decision,
            justification=justification,
            score_used=score_used
        )
        self.chain.append(step)

    def get_trace(self) -> List[ReasonStep]:
        return self.chain
