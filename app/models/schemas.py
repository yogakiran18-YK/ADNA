from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import date

# ----------------------------
# Curriculum Models
# ----------------------------
class CourseDTO(BaseModel):
    code: str
    name: str
    credits: int
    semester: int
    category: str = "Core" # Core, Elective, Humanities, Science
    prerequisites: List[str] = []
    learning_outcomes: List[str] = []
    imparts_skills: Dict[str, float] = {} # skill_id -> weight

class CurriculumIngestRequest(BaseModel):
    department: str = "CSE"
    academic_year: str = "2025-2029"
    raw_text: Optional[str] = None
    courses: Optional[List[CourseDTO]] = None

class CurriculumIngestResponse(BaseModel):
    status: str
    courses_parsed: int
    prerequisites_linked: int
    skills_mapped: int

class PrereqCheckRequest(BaseModel):
    target_course_code: str
    completed_course_codes: List[str]

class PrereqCheckResponse(BaseModel):
    target_course_code: str
    is_feasible: bool
    missing_prerequisites: List[str]
    prereq_chain_depth: int
    topological_path: List[str]

# ----------------------------
# Market Trends Models
# ----------------------------
class JobPostingDTO(BaseModel):
    posting_id: str
    title: str
    company: str
    posting_date: str # YYYY-MM-DD
    extracted_skills: List[str]

class MarketSeedRequest(BaseModel):
    postings: List[JobPostingDTO]

class SkillDemandItem(BaseModel):
    skill_id: str
    skill_name: str
    category: str
    raw_frequency: int
    recency_decay_score: float
    demand_score: float

class MarketTrendsResponse(BaseModel):
    total_postings_analyzed: int
    top_skills: List[SkillDemandItem]

# ----------------------------
# Student Profiling Models
# ----------------------------
class CourseGradeRecord(BaseModel):
    course_code: str
    semester_taken: int
    grade: str # A, B, C, D, F
    grade_point: float # e.g. 10.0, 8.0

class StudentProfileCreate(BaseModel):
    student_id: str
    name: str
    department: str = "CSE"
    current_semester: int = 5
    target_role: str = "AI/ML Engineer"
    interests: List[str] = ["Machine Learning", "Cloud Systems"]
    completed_courses: List[CourseGradeRecord] = []

class StudentProfileResponse(BaseModel):
    student_id: str
    name: str
    department: str
    current_semester: int
    target_role: str
    interests: List[str]
    total_credits_earned: int
    gpa: float
    profile_vector_dim: int

# ----------------------------
# Skill Gap Analyzer Models
# ----------------------------
class SkillGapItem(BaseModel):
    skill_id: str
    skill_name: str
    category: str
    market_demand_score: float
    semantic_similarity: float
    course_mastery_factor: float
    gap_score: float
    recommended_elective_codes: List[str]

class SkillGapAnalysisResponse(BaseModel):
    student_id: str
    target_role: str
    total_gaps_identified: int
    gaps: List[SkillGapItem]

# ----------------------------
# Career Simulator Models
# ----------------------------
class CareerTrajectoryItem(BaseModel):
    trajectory_id: str
    title: str
    description: str
    key_enabling_courses: List[str]
    llm_reasoning: str
    statistical_fit_score: float
    composite_score: float

class CareerSimulationRequest(BaseModel):
    student_id: str
    target_role_override: Optional[str] = None

class CareerSimulationResponse(BaseModel):
    student_id: str
    simulated_trajectories: List[CareerTrajectoryItem]

# ----------------------------
# Planner & Roadmap Models
# ----------------------------
class SemesterPlan(BaseModel):
    semester: int
    planned_courses: List[str]
    total_credits: int

class ReasonChainItem(BaseModel):
    course_code: str
    target_skill_id: str
    market_signal_demand: float
    prerequisite_feasibility_path: List[str]
    score_contribution: float
    explanation_prose: str

class RoadmapGenerateRequest(BaseModel):
    student_id: str
    max_credits_per_sem: int = 24

class RoadmapResponse(BaseModel):
    roadmap_id: str
    student_id: str
    version: int
    objective_function_score: float
    semester_plans: List[SemesterPlan]
    reason_chains: List[ReasonChainItem]
