from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.models.schemas import MarketSeedRequest, MarketTrendsResponse, JobPostingDTO
from app.agents.market_agent import market_agent, SKILL_TAXONOMY
from app.database.sqlite_db import get_sqlite_connection

router = APIRouter(prefix="/market", tags=["Market Trends Agent"])

# Default Seed Postings for AI/ML and CSE Roles
DEFAULT_SEED_POSTINGS = [
    JobPostingDTO(
        posting_id="job_001",
        title="Senior AI/ML Engineer",
        company="TechCorp AI",
        posting_date="2026-08-01",
        extracted_skills=["skill_pytorch", "skill_python", "skill_nlp", "skill_docker"]
    ),
    JobPostingDTO(
        posting_id="job_002",
        title="MLOps & Backend Specialist",
        company="DataScale Inc",
        posting_date="2026-08-02",
        extracted_skills=["skill_python", "skill_mlops", "skill_fastapi", "skill_aws", "skill_docker"]
    ),
    JobPostingDTO(
        posting_id="job_003",
        title="Data Engineer & SQL Expert",
        company="CloudData Systems",
        posting_date="2026-07-15", # Older posting (demonstrates recency decay)
        extracted_skills=["skill_sql", "skill_python", "skill_aws"]
    ),
    JobPostingDTO(
        posting_id="job_004",
        title="Junior Software Engineer - AI",
        company="Innovate AI",
        posting_date="2026-08-03",
        extracted_skills=["skill_python", "skill_dsa", "skill_pytorch", "skill_fastapi"]
    )
]

@router.post("/seed", response_model=MarketTrendsResponse)
def seed_market_postings(request: Optional[MarketSeedRequest] = None):
    postings = request.postings if request and request.postings else DEFAULT_SEED_POSTINGS
    return market_agent.process_job_postings(postings)

@router.get("/trends", response_model=MarketTrendsResponse)
def get_market_trends():
    # If no postings processed yet, process default seed postings
    return market_agent.process_job_postings(DEFAULT_SEED_POSTINGS)
