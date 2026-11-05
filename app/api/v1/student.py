from fastapi import APIRouter, HTTPException
from app.models.schemas import StudentProfileCreate, StudentProfileResponse
from app.agents.profiling_agent import profiling_agent

router = APIRouter(prefix="/student", tags=["Student Profiling Agent"])

@router.post("/profile", response_model=StudentProfileResponse)
def create_or_update_student_profile(profile: StudentProfileCreate):
    return profiling_agent.create_or_update_profile(profile)

@router.get("/{student_id}/profile", response_model=StudentProfileResponse)
@router.get("/profile/{student_id}", response_model=StudentProfileResponse)
def get_student_profile(student_id: str):
    profile = profiling_agent.get_profile(student_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Student profile for {student_id} not found.")
    return profile
