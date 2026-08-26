from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import RoadmapGenerateRequest, RoadmapResponse, ReasonChainItem
from app.agents.planner_agent import planner_agent

router = APIRouter(prefix="/roadmap", tags=["Planner Agent"])

@router.post("/generate", response_model=RoadmapResponse)
def generate_student_roadmap(request: RoadmapGenerateRequest):
    return planner_agent.generate_roadmap(
        student_id=request.student_id,
        max_credits_per_sem=request.max_credits_per_sem
    )

@router.get("/{student_id}/trace", response_model=List[ReasonChainItem])
def get_roadmap_traceability_reasons(student_id: str):
    reasons = planner_agent.get_roadmap_trace(student_id)
    if not reasons:
        raise HTTPException(status_code=404, detail=f"No roadmap trace found for student {student_id}.")
    return reasons

@router.post("/full-refresh", response_model=RoadmapResponse)
def full_pipeline_closed_loop_refresh(request: RoadmapGenerateRequest):
    """
    Triggers full closed-loop multi-agent refresh:
    Student Profile -> Market Trends -> Skill Gap Analysis -> Neo4j Graph Feasibility -> Planner Optimization.
    """
    return planner_agent.generate_roadmap(
        student_id=request.student_id,
        max_credits_per_sem=request.max_credits_per_sem
    )

