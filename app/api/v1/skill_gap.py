from fastapi import APIRouter, HTTPException
from app.models.schemas import SkillGapAnalysisResponse
from app.agents.skill_gap_agent import skill_gap_agent

router = APIRouter(prefix="/skills", tags=["Skill Gap Analyzer Agent"])

@router.get("/gap-analysis/{student_id}", response_model=SkillGapAnalysisResponse)
def get_student_skill_gaps(student_id: str):
    return skill_gap_agent.calculate_skill_gaps(student_id)
