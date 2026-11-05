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
def get_market_trends(as_of: Optional[str] = None):
    try:
        return market_agent.get_current_demand_scores(as_of=as_of)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/postings/recent")
def get_recent_postings(limit: int = 20):
    import json
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT posting_id, title, company, posting_date, extracted_skills_json FROM market_postings ORDER BY posting_date DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        try:
            skills = json.loads(r["extracted_skills_json"])
        except Exception:
            skills = []
        result.append({
            "posting_id": r["posting_id"],
            "title": r["title"],
            "company": r["company"],
            "posting_date": r["posting_date"],
            "extracted_skills": skills
        })
    return result


@router.post("/kaggle/ingest", response_model=MarketTrendsResponse)
def ingest_kaggle_dataset(limit: int = 150):
    """
    Ingests real job postings from the connected Kaggle dataset into the Market Trends Agent,
    persisting them into SQLite and updating ChromaDB skill vector embeddings.
    """
    from data.kaggle_connector import ingest_kaggle_market_data
    try:
        return ingest_kaggle_market_data(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest Kaggle dataset: {str(e)}")

@router.get("/kaggle/status")
def get_kaggle_dataset_status():
    """
    Returns the connection and verification status of all connected Kaggle datasets.
    """
    from data.kaggle_connector import check_dataset_status
    return check_dataset_status()

