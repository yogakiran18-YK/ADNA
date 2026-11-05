import pytest
from datetime import datetime, timezone
from app.agents.market_agent import market_agent
from app.models.schemas import JobPostingDTO
from data.kaggle_connector import load_kaggle_market_postings, check_dataset_status
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_invalid_as_of_date_raises_value_error():
    # Calling market agent with malformed as_of date raises ValueError
    with pytest.raises(ValueError, match="Invalid as_of date"):
        market_agent.calculate_recency_decay(as_of="2026-99-99")

    with pytest.raises(ValueError, match="Invalid as_of date"):
        market_agent.calculate_recency_decay(as_of="not-a-date")

    # API route returns 400 for invalid as_of
    resp = client.get("/api/v1/market/trends?as_of=invalid-date-format")
    assert resp.status_code == 400
    assert "Invalid as_of date" in resp.json()["detail"]

def test_invalid_posting_dates_are_rejected():
    # Job postings with invalid date strings should be rejected and not silently converted
    postings = [
        JobPostingDTO(
            posting_id="VALID_001",
            title="Python ML Engineer",
            company="Tech Corp",
            posting_date="2026-05-01",
            extracted_skills=["skill_python", "skill_pytorch"]
        ),
        JobPostingDTO(
            posting_id="INVALID_002",
            title="Data Scientist",
            company="Bad Date Inc",
            posting_date="INVALID_POSTING_DATE",
            extracted_skills=["skill_sql"]
        )
    ]

    res = market_agent.calculate_recency_decay(postings=postings, as_of="2026-06-01")
    # Only valid posting was processed into weights
    sql_item = next(s for s in res.top_skills if s.skill_id == "skill_sql")
    py_item = next(s for s in res.top_skills if s.skill_id == "skill_python")
    assert py_item.raw_frequency == 1
    assert sql_item.raw_frequency == 0

def test_future_posting_date_handling():
    # Posting with future date relative to as_of should clamp delta_days to 0 (decay weight 1.0)
    future_postings = [
        JobPostingDTO(
            posting_id="FUTURE_001",
            title="Future Engineer",
            company="Future Corp",
            posting_date="2026-12-01",
            extracted_skills=["skill_docker"]
        )
    ]
    res = market_agent.calculate_recency_decay(postings=future_postings, as_of="2026-01-01")
    docker_item = next(s for s in res.top_skills if s.skill_id == "skill_docker")
    assert docker_item.raw_frequency == 1
    assert 0.0 <= docker_item.recency_decay_score <= 1.0
    assert docker_item.demand_score == 1.0

def test_provenance_labels():
    # When empty list passed, data_source is empty
    empty_res = market_agent.calculate_recency_decay(postings=[])
    assert empty_res.total_postings_analyzed == 0
    assert empty_res.data_source == "empty"
