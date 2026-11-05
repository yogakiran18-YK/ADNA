from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import SkillGapAnalysisResponse
from app.agents.skill_gap_agent import skill_gap_agent

router = APIRouter(prefix="/skills", tags=["Skill Gap Analyzer Agent"])

@router.get("/gap-analysis/{student_id}", response_model=SkillGapAnalysisResponse)
def get_student_skill_gaps(
    student_id: str,
    target_role_id: Optional[str] = Query(None, description="Identifier for target career role"),
    target_role: Optional[str] = Query(None, description="Title or name of target career role")
):
    try:
        effective_role = target_role_id or target_role
        return skill_gap_agent.calculate_skill_gaps(
            student_id=student_id,
            target_role_id=effective_role
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
