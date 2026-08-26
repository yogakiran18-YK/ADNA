import pytest
from app.agents.market_agent import market_agent
from app.models.schemas import JobPostingDTO
from app.database.chroma_db import vector_store

def test_skill_keyword_extraction():
    text = "We are seeking a Senior AI Engineer skilled in PyTorch, Docker containers, and Natural Language Processing."
    skills = market_agent.extract_skills_from_text(text)
    
    assert "skill_pytorch" in skills
    assert "skill_docker" in skills
    assert "skill_nlp" in skills

def test_market_demand_recency_decay():
    postings = [
        JobPostingDTO(
            posting_id="recent_01",
            title="PyTorch Machine Learning Engineer",
            company="AI Corp",
            posting_date="2026-08-03", # Today
            extracted_skills=["skill_pytorch"]
        ),
        JobPostingDTO(
            posting_id="old_01",
            title="TensorFlow Engineer",
            company="Legacy Tech",
            posting_date="2026-06-01", # 63 days ago -> exponential decay e^(-0.05 * 63) = ~0.04
            extracted_skills=["skill_tensorflow"]
        )
    ]
    
    response = market_agent.process_job_postings(postings, current_date_str="2026-08-03")
    assert response.total_postings_analyzed == 2
    
    skill_map = {s.skill_id: s for s in response.top_skills}
    
    # Recent PyTorch skill should have significantly higher demand score than old TensorFlow skill
    assert skill_map["skill_pytorch"].demand_score > skill_map["skill_tensorflow"].demand_score
    assert skill_map["skill_pytorch"].demand_score == 1.0 # Normalized max
    assert skill_map["skill_tensorflow"].demand_score < 0.1 # Severely decayed

def test_chroma_vector_store_sync():
    # Verify skill embeddings were synced into vector_store
    emb = vector_store.get_embedding("Deep learning and PyTorch neural networks")
    results = vector_store.search_similar_skills(emb, top_k=3)
    
    assert len(results) > 0
    top_skill_ids = [r["skill_id"] for r in results]
    assert "skill_pytorch" in top_skill_ids or "skill_nlp" in top_skill_ids
