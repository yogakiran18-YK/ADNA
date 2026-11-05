import pytest
from app.agents.profiling_agent import profiling_agent
from app.models.schemas import StudentProfileCreate, CourseGradeRecord
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_missing_grades_produce_none_gpa():
    # Student with courses where grade/grade_point are not recorded (None)
    student_id = "TEST_ACADEMIC_NO_GRADES"
    profile_create = StudentProfileCreate(
        student_id=student_id,
        name="Ungraded Student",
        department="CSE",
        current_semester=3,
        target_role="Core Software Engineer",
        interests=["Data Structures"],
        completed_courses=[
            CourseGradeRecord(course_code="CS101", semester_taken=1, grade=None, grade_point=None),
            CourseGradeRecord(course_code="CS102", semester_taken=2, grade=None, grade_point=None),
        ]
    )
    profile = profiling_agent.create_or_update_profile(profile_create)

    # GPA must be None, NOT 0.00 or a fabricated 9.0!
    assert profile.gpa is None
    assert profile.gpa_estimated is True
    assert "grade:CS101" in profile.estimated_fields
    assert len(profile.completed_courses) == 2

    # API profile fetch returns gpa as null
    resp = client.get(f"/api/v1/student/profile/{student_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["gpa"] is None
    for c in data["completed_courses"]:
        assert c["grade"] is None
        assert c["grade_point"] is None

def test_mixed_known_and_unknown_grades():
    # Student with 1 known grade ("A", 9.0) and 1 unknown grade
    student_id = "TEST_ACADEMIC_MIXED_GRADES"
    profile_create = StudentProfileCreate(
        student_id=student_id,
        name="Mixed Student",
        department="CSE",
        current_semester=3,
        target_role="Core Software Engineer",
        interests=["Data Structures"],
        completed_courses=[
            CourseGradeRecord(course_code="CS101", semester_taken=1, grade="A", grade_point=9.0),
            CourseGradeRecord(course_code="CS102", semester_taken=2, grade=None, grade_point=None),
        ]
    )
    profile = profiling_agent.create_or_update_profile(profile_create)

    # GPA must be computed ONLY over the graded course (9.0), not diluted by a fake 0.0 for CS102
    assert profile.gpa == 9.0
    assert profile.gpa_estimated is True
    assert "grade:CS102" in profile.estimated_fields

def test_missing_credits_and_round_trip():
    # Student where credits are None; curriculum defaults are used honestly without crashing
    student_id = "TEST_ACADEMIC_ROUNDTRIP"
    profile_create = StudentProfileCreate(
        student_id=student_id,
        name="Roundtrip Student",
        department="CSE",
        current_semester=4,
        target_role="DevOps & SRE Engineer",
        interests=["Docker", "Linux"],
        completed_courses=[
            CourseGradeRecord(course_code="CS101", semester_taken=1, grade="B", grade_point=8.0, credits=None),
            CourseGradeRecord(course_code="CS102", semester_taken=2, grade=None, grade_point=None, credits=None),
        ]
    )
    created = profiling_agent.create_or_update_profile(profile_create)
    assert created.student_id == student_id
    assert created.gpa == 8.0

    # Fetch back from database
    loaded = profiling_agent.get_profile(student_id)
    assert loaded is not None
    assert loaded.student_id == student_id
    assert loaded.gpa == 8.0
    assert len(loaded.completed_courses) == 2

    # Check that unknown grade remained None
    c_map = {c.course_code: c for c in loaded.completed_courses}
    assert c_map["CS101"].grade == "B"
    assert c_map["CS101"].grade_point == 8.0
    assert c_map["CS102"].grade is None
    assert c_map["CS102"].grade_point is None
