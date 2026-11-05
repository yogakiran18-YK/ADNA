import os
import sys
import pytest
from datetime import datetime, timezone, date
import numpy as np
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.models.schemas import StudentProfileCreate, CourseGradeRecord, JobPostingDTO
from app.agents.profiling_agent import profiling_agent
from app.agents.market_agent import market_agent
from app.agents.skill_gap_agent import skill_gap_agent
from app.agents.simulator_agent import simulator_agent
from app.agents.planner_agent import planner_agent, NoValidPathError
from app.database.neo4j_db import graph_manager
from app.database.chroma_db import vector_store
from app.models.domain import compute_recency_decay

client = TestClient(app)

def test_market_decay_formula_and_as_of():
    """Verifies exponential recency decay math and explicit as_of parameter handling."""
    # Delta t = 0 -> decay factor 1.0
    decay_zero = compute_recency_decay(days_ago=0, decay_lambda=0.05)
    assert pytest.approx(decay_zero, 0.001) == 1.0

    # Delta t = 10 -> decay factor e^(-0.05 * 10) = e^(-0.5) ~ 0.6065
    decay_10 = compute_recency_decay(days_ago=10, decay_lambda=0.05)
    assert pytest.approx(decay_10, 0.001) == 0.6065

    # Delta t = 60 -> decay factor e^(-0.05 * 60) = e^(-3) ~ 0.0498
    decay_60 = compute_recency_decay(days_ago=60, decay_lambda=0.05)
    assert pytest.approx(decay_60, 0.001) == 0.0498

    # Process postings with explicit as_of date
    custom_as_of = "2026-06-01"
    postings = [
        JobPostingDTO(
            posting_id="P1",
            title="AI Engineer",
            company="Test Corp",
            posting_date="2026-05-20", # 12 days before as_of
            extracted_skills=["skill_pytorch"]
        )
    ]
    trends = market_agent.process_job_postings(postings=postings, as_of=custom_as_of)
    assert trends.as_of == custom_as_of
    assert len(trends.top_skills) > 0
    pytorch_item = next((s for s in trends.top_skills if s.skill_id == "skill_pytorch"), None)
    assert pytorch_item is not None
    assert 0.0 <= pytorch_item.demand_score <= 1.0
    assert 0.0 <= pytorch_item.recency_decay_score <= 1.0

def test_deterministic_lexical_fallback_vectorizer():
    """Verifies that vectorizer produces deterministic, unit-norm 384-d vectors without pseudo-random values."""
    text1 = "FastAPI Docker Python Cloud"
    text2 = "FastAPI Docker Python Cloud"
    text3 = "Graphic Design Oil Painting"

    v1 = vector_store._get_lexical_vector(text1)
    v2 = vector_store._get_lexical_vector(text2)
    v3 = vector_store._get_lexical_vector(text3)

    assert len(v1) == 384
    # Determinism: identical input produces identical vectors
    assert v1 == v2
    # Semantics: distinct inputs produce distinct vectors
    assert v1 != v3

    # Unit norm: ||v|| ~ 1.0
    norm_v1 = sum(x * x for x in v1)
    assert pytest.approx(norm_v1, 0.01) == 1.0

    # No NaNs or infinities
    assert all(not np.isnan(x) and not np.isinf(x) for x in v1)

def test_empty_and_minimal_inputs_handling():
    """Verifies graceful handling of empty interests, empty courses, and brand new profiles."""
    stu_id = "TEST_CANONICAL_MINIMAL"
    profile_create = StudentProfileCreate(
        student_id=stu_id,
        name="Empty Profile Student",
        department="CSE",
        current_semester=1,
        target_role="AI / Machine Learning Engineer",
        interests=[],
        completed_courses=[]
    )
    profile = profiling_agent.create_or_update_profile(profile_create)
    assert profile.total_credits_earned == 0
    assert profile.gpa is None
    assert profile.interests == []
    assert len(profile.completed_courses) == 0

    # Skill gaps calculation should not crash
    gaps = skill_gap_agent.calculate_skill_gaps(stu_id)
    assert gaps.total_gaps_identified > 0
    # Every course mastery factor should be 0.0
    assert all(g.course_mastery_factor == 0.0 for g in gaps.gaps)

    # Simulation should return Tier 4 baseline without crashing
    sim = simulator_agent.simulate_career_trajectories(stu_id)
    assert sim.model_type == "transparent_heuristic_estimate"
    assert sim.match_tier == "Tier 4: Foundation Building"
    assert len(sim.simulated_trajectories) >= 3

def test_planner_topological_ordering_and_no_duplicates():
    """Verifies topological precedence and duplicate prevention in academic roadmaps."""
    stu_id = "TEST_CANONICAL_TOPOLOGICAL"
    profile_create = StudentProfileCreate(
        student_id=stu_id,
        name="Topological Test Student",
        department="CSE",
        current_semester=1,
        target_role="AI / Machine Learning Engineer",
        interests=["Algorithms"],
        completed_courses=[]
    )
    profiling_agent.create_or_update_profile(profile_create)
    roadmap = planner_agent.generate_roadmap(stu_id, max_credits_per_sem=20)
    assert roadmap.status in ("success", "feasible")
    assert len(roadmap.semester_plans) > 0

    # 1. No duplicates: every course appears at most once across all semesters
    all_courses = []
    course_to_sem = {}
    for sp in roadmap.semester_plans:
        for c in sp.planned_courses:
            all_courses.append(c)
            course_to_sem[c] = sp.semester

    assert len(all_courses) == len(set(all_courses)), f"Duplicate courses detected: {all_courses}"

    # 2. Prerequisite precedence: for every course in sem S, prerequisites must be in sem < S
    for c, sem in course_to_sem.items():
        prereqs = graph_manager.mock_graph.get_prerequisites_for(c)
        for p in prereqs:
            if p in course_to_sem:
                assert course_to_sem[p] < sem, f"Course {c} (sem {sem}) scheduled before or with prerequisite {p} (sem {course_to_sem[p]})"

def test_cycle_detection_and_infeasible_outcome():
    """Verifies that circular prerequisite dependencies halt planning and return explainable errors."""
    courses_backup = dict(graph_manager.mock_graph.courses)
    prereqs_backup = set(graph_manager.mock_graph.prereqs)

    try:
        # Inject circular dependency: CANON_A -> CANON_B -> CANON_A
        graph_manager.add_course("CANON_A", "Cyclic Course A", 4, 5, "Elective")
        graph_manager.add_course("CANON_B", "Cyclic Course B", 4, 5, "Elective")
        graph_manager.add_prerequisite("CANON_B", "CANON_A")
        graph_manager.add_prerequisite("CANON_A", "CANON_B")

        has_cycle, cyclic_nodes = graph_manager.mock_graph.detect_cycle()
        assert has_cycle is True
        assert "CANON_A" in cyclic_nodes
        assert "CANON_B" in cyclic_nodes

        # Non-raising call returns status='infeasible' with explainable error
        roadmap = planner_agent.generate_roadmap("TEST_CANONICAL_MINIMAL", raise_on_infeasible=False)
        assert roadmap.status == "infeasible"
        assert "cycle" in roadmap.error.lower()

        # Raising call raises NoValidPathError
        with pytest.raises(NoValidPathError):
            planner_agent.generate_roadmap("TEST_CANONICAL_MINIMAL", raise_on_infeasible=True)

    finally:
        graph_manager.mock_graph.courses = courses_backup
        graph_manager.mock_graph.prereqs = prereqs_backup

def test_canonical_api_v1_contract():
    """Verifies end-to-end FastAPI canonical /api/v1 contract."""
    stu_id = "TEST_API_V1_STUDENT"

    # 1. POST /api/v1/student/profile
    profile_payload = {
        "student_id": stu_id,
        "name": "API Tester",
        "department": "CSE",
        "current_semester": 5,
        "target_role": "AI / Machine Learning Engineer",
        "interests": ["PyTorch", "NLP"],
        "completed_courses": [
            {"course_code": "CS101", "semester_taken": 1, "grade": "A", "grade_point": 9.0},
            {"course_code": "CS102", "semester_taken": 2, "grade": "S", "grade_point": 10.0}
        ]
    }
    resp = client.post("/api/v1/student/profile", json=profile_payload)
    assert resp.status_code == 200
    p_data = resp.json()
    assert p_data["student_id"] == stu_id
    assert p_data["gpa"] == 9.5
    assert p_data["total_credits_earned"] == 8

    # 2. GET /api/v1/student/{student_id}/profile
    get_resp = client.get(f"/api/v1/student/{stu_id}/profile")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "API Tester"

    # 3. GET /api/v1/skills/gap-analysis/{student_id}
    gap_resp = client.get(f"/api/v1/skills/gap-analysis/{stu_id}")
    assert gap_resp.status_code == 200
    gap_data = gap_resp.json()
    assert "gaps" in gap_data
    assert len(gap_data["gaps"]) > 0

    # 4. POST /api/v1/career/simulate
    sim_resp = client.post("/api/v1/career/simulate", json={"student_id": stu_id})
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert sim_data["model_type"] == "transparent_heuristic_estimate"
    assert "simulated_trajectories" in sim_data
    assert "shap_explanations" in sim_data
    assert "semester_readiness" in sim_data

    # 5. POST /api/v1/roadmap/generate
    rm_resp = client.post("/api/v1/roadmap/generate", json={"student_id": stu_id, "max_credits_per_sem": 24})
    assert rm_resp.status_code == 200
    rm_data = rm_resp.json()
    assert rm_data["status"] == "success"
    assert "semester_plans" in rm_data
    assert "reason_chains" in rm_data
    assert "semesters" in rm_data
    assert len(rm_data["semester_plans"]) > 0

    # 6. GET /api/v1/market/trends
    trends_resp = client.get("/api/v1/market/trends")
    assert trends_resp.status_code == 200
    trends_data = trends_resp.json()
    assert "top_skills" in trends_data
    assert "data_source" in trends_data
