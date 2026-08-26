import pytest
import numpy as np
from app.agents.profiling_agent import profiling_agent
from app.models.schemas import StudentProfileCreate, CourseGradeRecord

def test_student_profile_creation_and_gpa():
    profile_req = StudentProfileCreate(
        student_id="STU1001",
        name="Alex Smith",
        department="CSE",
        current_semester=4,
        target_role="AI/ML Engineer",
        interests=["Deep Learning", "Computer Vision"],
        completed_courses=[
            CourseGradeRecord(course_code="CSE101", semester_taken=1, grade="A", grade_point=9.0),
            CourseGradeRecord(course_code="CSE201", semester_taken=2, grade="S", grade_point=10.0),
            CourseGradeRecord(course_code="MAT201", semester_taken=2, grade="B", grade_point=8.0)
        ]
    )
    
    response = profiling_agent.create_or_update_profile(profile_req)
    
    assert response.student_id == "STU1001"
    assert response.total_credits_earned == 12
    # GPA = (9*4 + 10*4 + 8*4) / 12 = 108 / 12 = 9.0
    assert response.gpa == 9.0

def test_student_profile_vector_synthesis():
    vector = profiling_agent.get_student_profile_vector("STU1001")
    assert len(vector) == 384
    norm = np.linalg.norm(vector)
    assert pytest.approx(norm, 0.001) == 1.0
