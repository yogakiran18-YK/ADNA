from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class Prerequisite(BaseModel):
    code: str = Field(..., description="The code of the prerequisite course")
    type: str = Field(..., description="Type of prerequisite, e.g., 'hard', 'soft', 'co-requisite'")

class Course(BaseModel):
    code: str = Field(..., description="Unique code for the course")
    title: str = Field(..., description="Title of the course")
    credits: int = Field(..., description="Number of credits")
    semester: str = Field(..., description="Semester offered")
    description: Optional[str] = Field(None, description="Detailed description of the course")
    skills_provided: List[str] = Field(default_factory=list, description="List of skill IDs this course provides")
    prerequisites: List[Prerequisite] = Field(default_factory=list, description="List of prerequisites for this course")

class StudentProfile(BaseModel):
    student_id: str = Field(..., description="Unique identifier for the student")
    current_skills: List[str] = Field(default_factory=list, description="List of skills the student currently has")
    completed_courses: List[str] = Field(default_factory=list, description="List of courses the student has completed")
    target_role: Optional[str] = Field(None, description="The job role the student is aiming for")

class SkillNode(BaseModel):
    skill_id: str = Field(..., description="Unique identifier for the skill")
    name: str = Field(..., description="Name of the skill")
    category: Optional[str] = Field(None, description="Category of the skill (e.g., 'technical', 'soft')")

class JobRole(BaseModel):
    role_id: str = Field(..., description="Unique identifier for the job role")
    title: str = Field(..., description="Title of the job role")
    required_skills: List[str] = Field(default_factory=list, description="List of skills required for this role")

class GapReport(BaseModel):
    student_id: str = Field(..., description="The student this report is for")
    target_role_id: str = Field(..., description="The role the student is aiming for")
    missing_skills: List[Dict[str, float]] = Field(default_factory=list, description="Ranked list of missing skills and their gap scores (e.g. [{'Python': 0.85}])")

class CareerSimulationResult(BaseModel):
    student_id: str = Field(..., description="The student simulated")
    target_role_id: str = Field(..., description="The target role simulated")
    ml_ranking_score: float = Field(..., description="Numeric role-fit score from the ML model")
    shap_explanations: Dict[str, float] = Field(..., description="SHAP feature importances")
    llm_narrative: str = Field(..., description="Qualitative narrative from the LLM")

class RoadmapPlan(BaseModel):
    student_id: str = Field(..., description="The student this roadmap is for")
    semesters: List[List[str]] = Field(default_factory=list, description="List of semesters, where each semester is a list of course codes")
    estimated_time_to_completion_months: int = Field(..., description="Estimated time to complete the roadmap in months")
