import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.agents.profiling_agent import profiling_agent
from app.models.schemas import StudentProfileCreate, CourseGradeRecord

client = TestClient(app)

def test_canonical_roadmap_trace_endpoint():
    student_id = "TEST_TRACE_CANONICAL_STU"
    profile_create = StudentProfileCreate(
        student_id=student_id,
        name="Trace Student",
        department="CSE",
        current_semester=4,
        target_role="AI / Machine Learning Engineer",
        interests=["Machine Learning"],
        completed_courses=[
            CourseGradeRecord(course_code="CS101", semester_taken=1, grade="A", grade_point=9.0),
            CourseGradeRecord(course_code="CS102", semester_taken=2, grade="A", grade_point=9.0)
        ]
    )
    profiling_agent.create_or_update_profile(profile_create)

    # 1. Generate roadmap
    gen_resp = client.post("/api/v1/roadmap/generate", json={
        "student_id": student_id,
        "max_credits_per_sem": 24
    })
    assert gen_resp.status_code == 200
    roadmap_data = gen_resp.json()
    roadmap_id = roadmap_data["roadmap_id"]
    assert roadmap_id is not None

    # 2. Query trace using canonical endpoint with student_id
    trace_resp_by_student = client.get(f"/api/v1/roadmap/{student_id}/trace")
    assert trace_resp_by_student.status_code == 200
    trace_data = trace_resp_by_student.json()
    assert isinstance(trace_data, list)
    assert len(trace_data) > 0

    first_item = trace_data[0]
    assert "course_code" in first_item
    assert "explanation_prose" in first_item
    assert "prerequisite_feasibility_path" in first_item
    assert "market_signal_demand" in first_item

    # 3. Query trace using canonical endpoint with roadmap_id
    trace_resp_by_roadmap = client.get(f"/api/v1/roadmap/{roadmap_id}/trace")
    assert trace_resp_by_roadmap.status_code == 200
    assert len(trace_resp_by_roadmap.json()) == len(trace_data)

    # 4. Query trace for nonexistent identifier returns 404
    non_existent = client.get("/api/v1/roadmap/NONEXISTENT_STUDENT_OR_ROADMAP/trace")
    assert non_existent.status_code == 404
