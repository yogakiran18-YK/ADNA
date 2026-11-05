import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agents.skill_gap_agent import skill_gap_agent, resolve_target_role
from app.agents.profiling_agent import profiling_agent
from app.models.schemas import StudentProfileCreate, CourseGradeRecord

client = TestClient(app)

def test_resolve_target_role_known_and_unsupported():
    # Known roles resolve cleanly
    role_id, title, skills = resolve_target_role("ROLE_AIML")
    assert role_id == "ROLE_AIML"
    assert "PyTorch" in skills or "skill_pytorch" in skills
    assert len(skills) >= 2

    # Unsupported role raises ValueError
    with pytest.raises(ValueError, match="Unknown or unsupported target role"):
        resolve_target_role("ROLE_NONEXISTENT_XYZ_123")

def test_changing_target_role_changes_gaps():
    # Setup test student with foundational courses
    student_id = "TEST_ROLE_AWARE_STUDENT"
    profile_create = StudentProfileCreate(
        student_id=student_id,
        name="Role Test Student",
        department="CSE",
        current_semester=4,
        target_role="AI / Machine Learning Engineer",
        interests=["Python", "Algorithms"],
        completed_courses=[
            CourseGradeRecord(course_code="CS101", semester_taken=1, grade="A", grade_point=9.0),
            CourseGradeRecord(course_code="CS102", semester_taken=2, grade="A", grade_point=9.0),
        ]
    )
    profiling_agent.create_or_update_profile(profile_create)

    # Calculate gaps for AIML
    gaps_aiml = skill_gap_agent.calculate_skill_gaps(student_id, target_role_id="ROLE_AIML")
    # Calculate gaps for FullStack
    gaps_fs = skill_gap_agent.calculate_skill_gaps(student_id, target_role_id="ROLE_FULLSTACK")

    # Priority role-required skills should be role-specific
    aiml_req_skills = [g.skill_id for g in gaps_aiml.role_required_gaps]
    fs_req_skills = [g.skill_id for g in gaps_fs.role_required_gaps]

    assert aiml_req_skills != fs_req_skills
    assert "skill_pytorch" in aiml_req_skills or "skill_mlops" in aiml_req_skills
    assert "skill_fastapi" in fs_req_skills or "skill_docker" in fs_req_skills

    # API returns distinct gaps and accepts target_role_id query param
    resp_aiml = client.get(f"/api/v1/skills/gap-analysis/{student_id}?target_role_id=ROLE_AIML")
    assert resp_aiml.status_code == 200
    data_aiml = resp_aiml.json()
    assert data_aiml["target_role_id"] == "ROLE_AIML"
    assert len(data_aiml["role_required_gaps"]) > 0

    resp_fs = client.get(f"/api/v1/skills/gap-analysis/{student_id}?target_role_id=ROLE_FULLSTACK")
    assert resp_fs.status_code == 200
    data_fs = resp_fs.json()
    assert data_fs["target_role_id"] == "ROLE_FULLSTACK"
    assert data_aiml["role_required_gaps"][0]["skill_id"] != data_fs["role_required_gaps"][0]["skill_id"] or \
           data_aiml["role_required_gaps"] != data_fs["role_required_gaps"]

def test_unknown_target_role_returns_400():
    student_id = "TEST_ROLE_AWARE_STUDENT"
    resp = client.get(f"/api/v1/skills/gap-analysis/{student_id}?target_role_id=ROLE_UNKNOWN_BAD_ID")
    assert resp.status_code == 400
    assert "Unknown or unsupported target role" in resp.json()["detail"]
