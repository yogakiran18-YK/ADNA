from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import (
    CurriculumIngestRequest, CurriculumIngestResponse,
    PrereqCheckRequest, PrereqCheckResponse, CourseDTO
)
from app.agents.curriculum_agent import curriculum_agent

router = APIRouter(prefix="/curriculum", tags=["Curriculum Agent"])

@router.post("/ingest", response_model=CurriculumIngestResponse)
def ingest_curriculum(request: CurriculumIngestRequest):
    parsed_courses: List[CourseDTO] = []
    
    if request.courses:
        parsed_courses.extend(request.courses)
    
    if request.raw_text:
        extracted = curriculum_agent.parse_syllabus_text(request.raw_text)
        parsed_courses.extend(extracted)
        
    if not parsed_courses:
        raise HTTPException(status_code=400, detail="No course data or parseable raw_text provided.")
        
    return curriculum_agent.ingest_curriculum(parsed_courses)

@router.post("/prereq-check", response_model=PrereqCheckResponse)
def check_prerequisites(request: PrereqCheckRequest):
    return curriculum_agent.check_prerequisite_feasibility(
        target_code=request.target_course_code,
        completed_codes=request.completed_course_codes
    )
