import os
import sys
import pytest

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import StudentProfile, JobRole
from core.reason_chain import ReasonChain
from agents.skill_gap_agent.agent import SkillGapAgent

class MockGraphClient:
    def __init__(self, mock_courses_skills: dict, mock_demand_scores: dict):
        self.mock_courses_skills = mock_courses_skills
        self.mock_demand_scores = mock_demand_scores
        
    def execute_read(self, query: str, parameters: dict = None):
        if "MATCH (c:Course)-[:TEACHES]->(s:Skill)" in query:
            completed = parameters.get("completed_courses", [])
            results = []
            for c in completed:
                if c in self.mock_courses_skills:
                    for s in self.mock_courses_skills[c]:
                        results.append({"skill_name": s})
            return results
            
        if "MATCH (s:Skill)" in query:
            reqs = parameters.get("required_skills", [])
            results = []
            for s in reqs:
                if s in self.mock_demand_scores:
                    results.append({"skill_name": s, "latest_score": self.mock_demand_scores[s]})
            return results
        return []

def test_zero_completed_courses():
    mock_courses = {"CS101": ["Python", "Algorithms"]}
    mock_demand = {"Python": 1.0, "Algorithms": 0.8, "SQL": 0.5}
    
    graph = MockGraphClient(mock_courses, mock_demand)
    chain = ReasonChain()
    agent = SkillGapAgent(graph, chain)
    
    student = StudentProfile(student_id="S1", current_skills=[], completed_courses=[])
    role = JobRole(role_id="R1", title="Dev", required_skills=["Python", "Algorithms", "SQL"])
    
    report = agent.compute_gap_report(student, role)
    
    assert report.student_id == "S1"
    assert len(report.missing_skills) == 3
    
    # Check ranking (Python 1.0, Algorithms 0.8, SQL 0.5)
    # Report format: [{"Python": 1.0}, {"Algorithms": 0.8}, {"SQL": 0.5}]
    assert list(report.missing_skills[0].keys())[0] == "Python"
    assert report.missing_skills[0]["Python"] == 1.0
    
    assert list(report.missing_skills[2].keys())[0] == "SQL"
    
def test_meets_all_requirements():
    mock_courses = {"CS101": ["Python", "Algorithms"]}
    mock_demand = {"Python": 1.0, "Algorithms": 0.8}
    
    graph = MockGraphClient(mock_courses, mock_demand)
    chain = ReasonChain()
    agent = SkillGapAgent(graph, chain)
    
    student = StudentProfile(student_id="S2", current_skills=[], completed_courses=["CS101"])
    role = JobRole(role_id="R2", title="Dev", required_skills=["Python", "Algorithms"])
    
    report = agent.compute_gap_report(student, role)
    
    # Missing skills should be empty since proficiency is 1.0 for both
    assert len(report.missing_skills) == 0

def test_partial_overlap():
    mock_courses = {"CS101": ["Python"]}
    mock_demand = {"Python": 1.0, "SQL": 0.7, "C++": 0.9}
    
    graph = MockGraphClient(mock_courses, mock_demand)
    chain = ReasonChain()
    agent = SkillGapAgent(graph, chain)
    
    student = StudentProfile(student_id="S3", current_skills=[], completed_courses=["CS101"])
    role = JobRole(role_id="R3", title="Dev", required_skills=["Python", "SQL", "C++"])
    
    report = agent.compute_gap_report(student, role)
    
    assert len(report.missing_skills) == 2
    
    # C++ has higher demand (0.9) than SQL (0.7), so C++ should be first
    assert list(report.missing_skills[0].keys())[0] == "C++"
    assert report.missing_skills[0]["C++"] == 0.9
    assert list(report.missing_skills[1].keys())[0] == "SQL"
    assert report.missing_skills[1]["SQL"] == 0.7
    
    # Python is completely fulfilled, not in list
    assert not any("Python" in item for item in report.missing_skills)
    
    # Check ReasonChain logging
    trace = chain.get_trace()
    assert len(trace) == 3 # 3 required skills checked
    
    python_trace = next((t for t in trace if "Skill: Python" in t.input_summary), None)
    assert python_trace.score_used == 0.0 # gap is 0.0
