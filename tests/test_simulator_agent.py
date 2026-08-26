import pytest
from app.agents.profiling_agent import profiling_agent
from app.agents.simulator_agent import simulator_agent
from app.models.schemas import StudentProfileCreate, CourseGradeRecord
from app.database.sqlite_db import get_sqlite_connection

def test_career_simulator_hybrid_model():
    # Clean prior test rows for isolation
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM career_simulations WHERE student_id = ?", ("STU4004",))
    conn.commit()
    conn.close()

    profile_req = StudentProfileCreate(

        student_id="STU4004",
        name="Morgan Taylor",
        department="CSE",
        current_semester=5,
        target_role="AI/ML Engineer",
        interests=["Machine Learning", "MLOps"],
        completed_courses=[
            CourseGradeRecord(course_code="CSE101", semester_taken=1, grade="A", grade_point=9.0),
            CourseGradeRecord(course_code="CSE201", semester_taken=2, grade="S", grade_point=10.0)
        ]
    )
    profiling_agent.create_or_update_profile(profile_req)

    res = simulator_agent.simulate_career_trajectories("STU4004")

    assert res.student_id == "STU4004"
    assert len(res.simulated_trajectories) == 3

    for traj in res.simulated_trajectories:
        assert traj.statistical_fit_score >= 0.0 and traj.statistical_fit_score <= 1.0
        # Check hybrid score composition: composite = 0.5 * LLM + 0.5 * StatFit
        expected_comp = round((0.5 * 0.85) + (0.5 * traj.statistical_fit_score), 4)
        assert pytest.approx(traj.composite_score, 0.001) == expected_comp

    # Verify SQLite logging of both outputs for auditability
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM career_simulations WHERE student_id = ?", ("STU4004",))
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 3
