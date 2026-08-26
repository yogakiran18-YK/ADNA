from fastapi import APIRouter, HTTPException
from app.models.schemas import CareerSimulationRequest, CareerSimulationResponse
from app.agents.simulator_agent import simulator_agent

router = APIRouter(prefix="/career", tags=["Career Simulator Agent"])

@router.post("/simulate", response_model=CareerSimulationResponse)
def simulate_career_trajectories(request: CareerSimulationRequest):
    return simulator_agent.simulate_career_trajectories(
        student_id=request.student_id,
        target_role_override=request.target_role_override
    )
