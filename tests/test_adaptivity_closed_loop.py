import pytest
from app.agents.profiling_agent import profiling_agent
from app.agents.market_agent import market_agent
from app.agents.planner_agent import planner_agent
from app.models.schemas import StudentProfileCreate, CourseGradeRecord, JobPostingDTO

def test_closed_loop_grade_update_adaptivity():
    # 1. Initial State: Student completed Intro programming & Data Structures
    student_id = "STU_ADAPT_01"
    profile_v1 = StudentProfileCreate(
        student_id=student_id,
        name="Adaptivity Test User 1",
        department="CSE",
        current_semester=5,
        target_role="AI/ML Engineer",
        interests=["Deep Learning"],
        completed_courses=[
            CourseGradeRecord(course_code="CSE101", semester_taken=1, grade="A", grade_point=9.0),
            CourseGradeRecord(course_code="CSE201", semester_taken=2, grade="S", grade_point=10.0)
        ]
    )
    profiling_agent.create_or_update_profile(profile_v1)

    # Initial Roadmap Generation
    roadmap_v1 = planner_agent.generate_roadmap(student_id)
    v1_courses = [c for sem in roadmap_v1.semester_plans for c in sem.planned_courses]

    # AIML301 should be planned in Semester 5
    assert "AIML301" in v1_courses

    # 2. Grade Update: Student completes AIML301 with Grade S (10.0) in Sem 5 & advances to Sem 6
    profile_v2 = StudentProfileCreate(
        student_id=student_id,
        name="Adaptivity Test User 1",
        department="CSE",
        current_semester=6,
        target_role="AI/ML Engineer",
        interests=["Deep Learning"],
        completed_courses=[
            CourseGradeRecord(course_code="CSE101", semester_taken=1, grade="A", grade_point=9.0),
            CourseGradeRecord(course_code="CSE201", semester_taken=2, grade="S", grade_point=10.0),
            CourseGradeRecord(course_code="AIML301", semester_taken=5, grade="S", grade_point=10.0)
        ]
    )
    profiling_agent.create_or_update_profile(profile_v2)

    # 3. Closed-Loop Refresh
    roadmap_v2 = planner_agent.generate_roadmap(student_id)
    v2_courses = [c for sem in roadmap_v2.semester_plans for c in sem.planned_courses]

    # PROOF OF ADAPTIVITY:
    # (a) AIML301 is no longer recommended in remaining semesters because it is completed.
    # (b) Advanced prerequisites dependent on AIML301 (AIML302 / AIML401) now become feasible and recommended!
    assert "AIML301" not in v2_courses
    assert ("AIML302" in v2_courses) or ("AIML401" in v2_courses)


def test_closed_loop_market_signal_adaptivity():
    student_id = "STU_ADAPT_02"
    profile = StudentProfileCreate(
        student_id=student_id,
        name="Adaptivity Test User 2",
        department="CSE",
        current_semester=5,
        target_role="Cloud MLOps Engineer",
        interests=["Cloud Computing", "DevOps"],
        completed_courses=[
            CourseGradeRecord(course_code="CSE101", semester_taken=1, grade="A", grade_point=9.0)
        ]
    )
    profiling_agent.create_or_update_profile(profile)

    # 1. Market Shift: Ingest job postings with extreme surge in MLOps & Docker demand
    market_postings_surge = [
        JobPostingDTO(
            posting_id="surge_01",
            title="Senior MLOps Engineer",
            company="DevOps Scale",
            posting_date="2026-08-03",
            extracted_skills=["skill_mlops", "skill_docker", "skill_aws"]
        ),
        JobPostingDTO(
            posting_id="surge_02",
            title="Cloud DevOps Specialist",
            company="Cloud Scaling",
            posting_date="2026-08-03",
            extracted_skills=["skill_mlops", "skill_docker", "skill_aws", "skill_fastapi"]
        )
    ]
    market_agent.process_job_postings(market_postings_surge, current_date_str="2026-08-03")

    # 2. Closed-Loop Roadmap Generation
    roadmap_surged = planner_agent.generate_roadmap(student_id)
    surged_courses = [c for sem in roadmap_surged.semester_plans for c in sem.planned_courses]

    # PROOF OF MARKET ADAPTIVITY:
    # Recommended courses adapt to prioritize Docker/Cloud (CSE304) and Web Architecture (CSE303)
    assert ("CSE304" in surged_courses) or ("CSE303" in surged_courses)
