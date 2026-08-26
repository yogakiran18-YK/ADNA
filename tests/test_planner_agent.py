import os
import sys
import pytest

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import StudentProfile, JobRole, GapReport, CareerSimulationResult
from core.reason_chain import ReasonChain
from agents.planner_agent.agent import PlannerAgent, NoValidPathError

class MockGraphClient:
    def __init__(self, courses, edges, skills):
        self.courses = courses
        self.edges = edges
        self.skills = skills
        
    def execute_read(self, query: str, parameters: dict = None):
        if "RETURN c.code AS code, c.credits AS credits" in query:
            return self.courses
        if "MATCH (p:Course)-[:PREREQUISITE_OF]->(c:Course)" in query:
            return self.edges
        if "MATCH (c:Course)-[:TEACHES]->(s:Skill)" in query:
            return self.skills
        return []

def test_provable_adaptivity():
    """
    Proves that a change in profile (completed courses) produces a demonstrably different roadmap.
    """
    courses = [
        {"code": "CS101", "credits": 3},
        {"code": "CS102", "credits": 3},
        {"code": "CS201", "credits": 3}
    ]
    edges = [
        {"prereq": "CS101", "course": "CS102"},
        {"prereq": "CS102", "course": "CS201"}
    ]
    skills = [
        {"code": "CS101", "skills": ["Python"]},
        {"code": "CS102", "skills": ["Algorithms"]},
        {"code": "CS201", "skills": ["DataStructures"]}
    ]
    
    graph_client = MockGraphClient(courses, edges, skills)
    chain = ReasonChain()
    agent = PlannerAgent(graph_client, chain, max_credits_per_semester=6)
    
    role = JobRole(role_id="R1", title="Dev", required_skills=["Python", "Algorithms", "DataStructures"])
    sim_result = CareerSimulationResult(
        student_id="S1", target_role_id="R1", ml_ranking_score=0.9, shap_explanations={}, llm_narrative="Mock"
    )
    
    # Run 1: 0 completed courses
    student_A = StudentProfile(student_id="S1", current_skills=[], completed_courses=[])
    gap_A = GapReport(student_id="S1", target_role_id="R1", missing_skills=[{"Python": 1.0}, {"Algorithms": 1.0}, {"DataStructures": 1.0}])
    roadmap_A = agent.generate_roadmap(student_A, role, gap_A, sim_result)
    
    # Run 2: 1 completed course (CS101)
    student_B = StudentProfile(student_id="S1", current_skills=[], completed_courses=["CS101"])
    gap_B = GapReport(student_id="S1", target_role_id="R1", missing_skills=[{"Algorithms": 1.0}, {"DataStructures": 1.0}])
    roadmap_B = agent.generate_roadmap(student_B, role, gap_B, sim_result)
    
    # Assert adaptivity (Roadmap A starts with CS101, Roadmap B starts with CS102)
    assert roadmap_A.semesters[0] == ["CS101"]
    assert roadmap_B.semesters[0] == ["CS102"]
    
    # Roadmap A should take 3 semesters (since max credits is 6 and we only have linear chain)
    # Actually wait, CS101 -> CS102 -> CS201. Max credits 6 allows 2 courses, but prereqs force 1 per semester
    assert len(roadmap_A.semesters) == 3
    assert len(roadmap_B.semesters) == 2

def test_graceful_failure_no_path():
    """
    Proves that an impossible prerequisite chain raises a clear error.
    """
    courses = [
        {"code": "CS301", "credits": 3},
        {"code": "CS302", "credits": 3}
    ]
    # Circular dependency or missing prereq
    edges = [
        {"prereq": "MISSING_COURSE", "course": "CS301"}
    ]
    skills = [
        {"code": "CS301", "skills": ["AdvancedML"]}
    ]
    
    graph_client = MockGraphClient(courses, edges, skills)
    chain = ReasonChain()
    agent = PlannerAgent(graph_client, chain)
    
    student = StudentProfile(student_id="S2", current_skills=[], completed_courses=[])
    role = JobRole(role_id="R2", title="ML Eng", required_skills=["AdvancedML"])
    gap = GapReport(student_id="S2", target_role_id="R2", missing_skills=[{"AdvancedML": 1.0}])
    sim_result = CareerSimulationResult(
        student_id="S2", target_role_id="R2", ml_ranking_score=0.9, shap_explanations={}, llm_narrative="Mock"
    )
    
    with pytest.raises(NoValidPathError) as excinfo:
        agent.generate_roadmap(student, role, gap, sim_result)
        
    assert "Impossible prerequisite chain" in str(excinfo.value)
