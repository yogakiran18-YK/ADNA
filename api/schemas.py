from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from core.schemas import StudentProfile, JobRole, RoadmapPlan
from core.reason_chain import ReasonStep

class RoadmapRequest(BaseModel):
    student: StudentProfile
    target_role: JobRole
    curriculum_text: Optional[str] = Field(
        default="CS101 Intro to Programming (3 credits, Fall).", 
        description="Optional curriculum text to override/append to the mock ingestion."
    )
    market_jobs: Optional[List[Dict]] = Field(
        default_factory=list,
        description="Optional job postings to override the mock market."
    )

class RoadmapResponse(BaseModel):
    run_id: str
    roadmap: RoadmapPlan
    reason_chain_length: int

class StudentMockRequest(BaseModel):
    student: StudentProfile
    target_role: JobRole
