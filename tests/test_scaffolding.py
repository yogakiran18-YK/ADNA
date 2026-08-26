import pytest
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database.sqlite_db import init_sqlite_db, get_sqlite_connection
from app.database.neo4j_db import Neo4jGraphManager
from app.database.chroma_db import VectorStoreManager
from app.models.domain import compute_skill_gap_score, compute_planner_objective

client = TestClient(app)

def test_fastapi_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_sqlite_db_init():
    init_sqlite_db()
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row["name"] for row in cursor.fetchall()]
    conn.close()
    
    assert "students" in tables
    assert "student_courses" in tables
    assert "market_postings" in tables
    assert "roadmaps" in tables
    assert "roadmap_reasons" in tables

def test_skill_gap_formula_math():
    # Test with known values:
    # D(s)=0.85, R(s)=0.90 => MarketWeight = 0.6(0.85) + 0.4(0.90) = 0.51 + 0.36 = 0.87
    # Similarity = 0.70 => 1 - S_sim = 0.30
    # Mastery = 0.56 => 1 - C_mastery = 0.44
    # G = 0.87 * 0.30 * 0.44 = 0.11484 -> rounded 0.1148
    gap = compute_skill_gap_score(
        market_demand=0.85,
        recency_decay=0.90,
        semantic_similarity=0.70,
        course_mastery=0.56,
        w1=0.6,
        w2=0.4
    )
    assert pytest.approx(gap, 0.001) == 0.1148

def test_planner_objective_math():
    # J = 0.40(0.8) + 0.30(0.7) + 0.20(1.0) - 0.10(0.1)
    # J = 0.32 + 0.21 + 0.20 - 0.01 = 0.72
    score = compute_planner_objective(
        gap_closure=0.8,
        market_alignment=0.7,
        feasibility_score=1.0,
        workload_penalty=0.1
    )
    assert pytest.approx(score, 0.001) == 0.72

def test_graph_manager_prerequisite_feasibility():
    graph = Neo4jGraphManager()
    graph.add_course("CSE101", "Programming", 4, 1, "Core")
    graph.add_course("CSE201", "Data Structures", 4, 2, "Core")
    graph.add_course("CSE301", "Algorithms", 4, 3, "Core")
    
    graph.add_prerequisite("CSE101", "CSE201")
    graph.add_prerequisite("CSE201", "CSE301")

    # If CSE101 is completed, CSE201 is feasible, but CSE301 is not feasible yet
    feasible, missing, path = graph.check_prerequisite_feasibility("CSE301", ["CSE101"])
    assert feasible is False
    assert "CSE201" in missing

    # If CSE101 and CSE201 are completed, CSE301 is feasible
    feasible, missing, path = graph.check_prerequisite_feasibility("CSE301", ["CSE101", "CSE201"])
    assert feasible is True
    assert len(missing) == 0
    assert path == ["CSE101", "CSE201", "CSE301"]

def test_vector_store_manager():
    vstore = VectorStoreManager()
    vstore.add_skill("skill_pytorch", "PyTorch deep learning framework", {"category": "AI/ML"})
    emb = vstore.get_embedding("PyTorch neural networks")
    assert len(emb) == 384
    results = vstore.search_similar_skills(emb, top_k=1)
    assert len(results) >= 1
    assert results[0]["skill_id"] == "skill_pytorch"
