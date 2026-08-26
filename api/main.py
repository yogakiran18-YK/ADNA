import os
import sys
import uuid
from typing import List, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import GapReport, CareerSimulationResult, StudentProfile, JobRole
from core.reason_chain import ReasonStep
from api.schemas import RoadmapRequest, RoadmapResponse, StudentMockRequest
from agents.orchestrator import ADNAOrchestrator
from core.mocks import MockE2EGraphClient # Using the mock for the demo

app = FastAPI(
    title="ADNA Academic Planning API",
    description="API for the Autonomous Degree Navigator Agent (Academic Demo)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

# In-memory store for ReasonChain logs mapped by run_id
# Note: Not production-grade. Used for academic demo viva presentation.
trace_store: Dict[str, List[ReasonStep]] = {}

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Basic Auth for academic demo.
    NOT PRODUCTION GRADE - Hardcoded credentials for viva gatekeeping.
    """
    correct_username = "admin"
    correct_password = "viva2026"
    
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Initialize global orchestrator with the mock client for demo purposes
graph_client = MockE2EGraphClient()
orchestrator = ADNAOrchestrator(graph_client)

@app.post("/students/{id}/roadmap", response_model=RoadmapResponse)
def generate_roadmap(id: str, req: RoadmapRequest, username: str = Depends(get_current_username)):
    """
    Runs the full end-to-end pipeline (Phase 7 Orchestrator).
    Returns the final RoadmapPlan and caches the full trace.
    """
    # Enforce ID matching
    req.student.student_id = id
    
    # Fallback to default mock jobs if none provided
    market_jobs = req.market_jobs or [
        {"job_id": "1", "description": "Needs Python.", "salary": 100000, "posted_date": datetime.now(timezone.utc).isoformat()}
    ]
    
    roadmap, trace = orchestrator.run_pipeline(
        curriculum_text=req.curriculum_text,
        market_jobs=market_jobs,
        student=req.student,
        role=req.target_role
    )
    
    run_id = str(uuid.uuid4())
    trace_store[run_id] = trace
    
    return RoadmapResponse(
        run_id=run_id,
        roadmap=roadmap,
        reason_chain_length=len(trace)
    )

@app.post("/students/{id}/gap-report", response_model=GapReport)
def get_gap_report(id: str, req: StudentMockRequest, username: str = Depends(get_current_username)):
    """
    Runs only the SkillGapAgent. Uses POST to safely receive the JSON profile body.
    """
    req.student.student_id = id
    gap = orchestrator.skill_gap_agent.compute_gap_report(req.student, req.target_role)
    return GapReport.model_validate(gap.model_dump())

@app.post("/students/{id}/career-simulation", response_model=CareerSimulationResult)
def get_career_simulation(id: str, req: StudentMockRequest, username: str = Depends(get_current_username)):
    """
    Runs the CareerSimulatorAgent. Uses POST to safely receive the JSON profile body.
    """
    req.student.student_id = id
    # Mocking gap report for the standalone endpoint
    gap = orchestrator.skill_gap_agent.compute_gap_report(req.student, req.target_role)
    sim = orchestrator.career_agent.simulate_career(req.student, req.target_role, gap)
    return CareerSimulationResult.model_validate(sim.model_dump())

@app.get("/reason-chain/{run_id}", response_model=List[ReasonStep])
def get_reason_chain(run_id: str, username: str = Depends(get_current_username)):
    """
    Returns the full traceable log for a given run_id.
    """
    if run_id not in trace_store:
        raise HTTPException(status_code=404, detail="Run ID not found")
    return trace_store[run_id]
