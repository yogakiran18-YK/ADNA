import pytest
from app.agents.planner_agent import planner_agent, NoValidPathError
from app.agents.profiling_agent import profiling_agent
from app.database.neo4j_db import graph_manager
from app.models.schemas import StudentProfileCreate, CourseGradeRecord

def test_empty_curriculum_handling():
    # Setup novice student
    student_id = "TEST_EMPTY_CURR_STUDENT"
    profile_create = StudentProfileCreate(
        student_id=student_id,
        name="Empty Curr Student",
        department="CSE",
        current_semester=1,
        target_role="AI / Machine Learning Engineer",
        interests=["Machine Learning"],
        completed_courses=[]
    )
    profiling_agent.create_or_update_profile(profile_create)

    # Backup graph
    courses_backup = dict(graph_manager.mock_graph.courses)
    prereqs_backup = set(graph_manager.mock_graph.prereqs)
    skills_backup = set(graph_manager.mock_graph.skills)

    try:
        # Clear curriculum
        graph_manager.clear_curriculum()

        # Non-raising call should return infeasible roadmap explaining empty curriculum
        roadmap = planner_agent.generate_roadmap(student_id, raise_on_infeasible=False)
        assert roadmap.status == "infeasible"
        assert "empty" in roadmap.error.lower()
        assert len(roadmap.semesters) == 0

        # Raising call should raise NoValidPathError
        with pytest.raises(NoValidPathError, match="empty"):
            planner_agent.generate_roadmap(student_id, raise_on_infeasible=True)
    finally:
        # Restore graph
        graph_manager.mock_graph.courses = courses_backup
        graph_manager.mock_graph.prereqs = prereqs_backup
        graph_manager.mock_graph.skills = skills_backup

def test_prerequisite_cycle_detection():
    student_id = "TEST_CYCLE_STUDENT"
    profile_create = StudentProfileCreate(
        student_id=student_id,
        name="Cycle Student",
        department="CSE",
        current_semester=1,
        target_role="AI / Machine Learning Engineer",
        interests=["Machine Learning"],
        completed_courses=[]
    )
    profiling_agent.create_or_update_profile(profile_create)

    courses_backup = dict(graph_manager.mock_graph.courses)
    prereqs_backup = set(graph_manager.mock_graph.prereqs)

    try:
        # Inject circular prerequisite
        graph_manager.add_course("CS_CYC_X", "Cycle Course X", 4, 3, "Core")
        graph_manager.add_course("CS_CYC_Y", "Cycle Course Y", 4, 3, "Core")
        graph_manager.add_prerequisite("CS_CYC_X", "CS_CYC_Y")
        graph_manager.add_prerequisite("CS_CYC_Y", "CS_CYC_X")

        roadmap = planner_agent.generate_roadmap(student_id, raise_on_infeasible=False)
        assert roadmap.status == "infeasible"
        assert "cycle" in roadmap.error.lower()
    finally:
        graph_manager.mock_graph.courses = courses_backup
        graph_manager.mock_graph.prereqs = prereqs_backup

def test_semester_credit_cap_and_topological_ordering():
    student_id = "TEST_CREDIT_CAP_STUDENT"
    profile_create = StudentProfileCreate(
        student_id=student_id,
        name="Credit Cap Student",
        department="CSE",
        current_semester=1,
        target_role="AI / Machine Learning Engineer",
        interests=["Machine Learning", "Algorithms"],
        completed_courses=[]
    )
    profiling_agent.create_or_update_profile(profile_create)

    max_credits = 16
    roadmap = planner_agent.generate_roadmap(student_id, max_credits_per_sem=max_credits)
    assert roadmap.status in ("feasible", "success")
    assert len(roadmap.semester_plans) > 0

    course_to_sem = {}
    for sp in roadmap.semester_plans:
        assert sp.total_credits <= max_credits, f"Semester {sp.semester} exceeded credit cap {max_credits}: {sp.total_credits}"
        for c in sp.planned_courses:
            course_to_sem[c] = sp.semester

    # Topological prerequisite check: each course's prereq must be in an EARLIER semester
    for c, sem in course_to_sem.items():
        prereqs = graph_manager.get_prerequisites_for(c)
        for p in prereqs:
            if p in course_to_sem:
                assert course_to_sem[p] < sem, f"Course {c} in sem {sem} scheduled before/with prereq {p} in sem {course_to_sem[p]}"
