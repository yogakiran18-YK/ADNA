from pydantic import BaseModel, Field, ConfigDict
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
    as_of: Optional[str] = None
    is_sample_data: bool = False
    data_source: str = "ingested_sqlite"
    ingestion_summary: Optional[Dict[str, Any]] = None

# ----------------------------
# Student Profiling Models
# ----------------------------
class CourseGradeRecord(BaseModel):
    course_code: str
    semester_taken: Optional[int] = None
    grade: Optional[str] = None # A, B, C, D, F, or None/unknown
    grade_point: Optional[float] = None # e.g. 10.0, 8.0, or None if unknown
    credits: Optional[int] = None # Curriculum-derived where available
    grade_estimated: bool = False
    credits_estimated: bool = False

class StudentProfileCreate(BaseModel):
    student_id: str
    name: str = "Student"
    department: str = "CSE"
    current_semester: int = 5
    target_role: str = "AI / Machine Learning Engineer"
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
    gpa: Optional[float] = None
    profile_vector_dim: int = 384
    credits_estimated: bool = False
    gpa_estimated: bool = False
    estimated_fields: List[str] = []
    credits_breakdown: Dict[str, int] = {}
    completed_courses: List[CourseGradeRecord] = []

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
    is_role_required: bool = True
    role_relevance: str = "role_required" # "role_required", "broader_market", "unmapped"

class SkillGapAnalysisResponse(BaseModel):
    student_id: str
    target_role: str
    target_role_id: Optional[str] = None
    target_role_title: Optional[str] = None
    total_gaps_identified: int
    gaps: List[SkillGapItem] = []
    role_required_gaps: List[SkillGapItem] = []
    broader_market_gaps: List[SkillGapItem] = []
    unmapped_skills: List[str] = []
    missing_skills: List[Dict[str, float]] = []
    is_sample_data: bool = False

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
    is_estimate: bool = True

class CareerSimulationRequest(BaseModel):
    student_id: str
    target_role_override: Optional[str] = None

class CareerSimulationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    student_id: str
    simulated_trajectories: List[CareerTrajectoryItem] = []
    # Rich fields for unified frontend and contract compatibility
    target_role_id: str = ""
    role_title: str = ""
    ml_ranking_score: float = 0.0
    heuristic_fit_score: float = 0.0
    match_tier: str = "Tier 3: Emerging Trajectory"
    is_estimate: bool = True
    model_type: str = "transparent_heuristic_estimate"
    shap_explanations: Dict[str, float] = {}
    llm_narrative: str = ""
    semester_readiness: Dict[str, float] = {}
    domain_competency: Dict[str, float] = {}
    adjacent_role_scores: Dict[str, float] = {}
    critical_enablers_summary: Dict[str, Any] = {}

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
    target_role_id: Optional[str] = None
    target_role: Optional[str] = None

class RoadmapResponse(BaseModel):
    roadmap_id: str
    student_id: str
    version: int
    objective_function_score: float
    semester_plans: List[SemesterPlan]
    reason_chains: List[ReasonChainItem]
    # Compatibility with frontend RoadmapView and legacy response
    semesters: List[List[str]] = []
    estimated_time_to_completion_months: int = 16
    is_sample_data: bool = False
    curriculum_source: str = "seeded_demo" # "ingested", "seeded_demo", "empty"
    target_role: Optional[str] = None
    run_id: Optional[str] = None
    status: str = "success"
    error: Optional[str] = None
