import os
import sys
import pytest
from datetime import datetime, timezone

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import StudentProfile, JobRole
from core.graph_client import GraphClient
from core.mocks import MockE2EGraphClient
from agents.orchestrator import ADNAOrchestrator


def test_orchestrator_e2e_pipeline():
    """
    End-to-end integration test verifying that all 5 agents run in sequence,
    schema validations pass, and the ReasonChain aggregates chronologically.
    """
    mock_client = MockE2EGraphClient()
    orchestrator = ADNAOrchestrator(mock_client)
    
    # Inputs
    curriculum_text = "CS101 Intro (3 credits, Fall). CS102 Data (3 credits, Spring). Prerequisite: CS101."
    market_jobs = [
        {"job_id": "1", "description": "Needs Python and DataStructures.", "salary": 100000, "posted_date": datetime.now(timezone.utc).isoformat()}
    ]
    student = StudentProfile(student_id="STU_999", current_skills=[], completed_courses=[])
    role = JobRole(role_id="ROLE_1", title="Software Engineer", required_skills=["Python"])
    
    # Execute Pipeline
    roadmap, trace = orchestrator.run_pipeline(
        curriculum_text=curriculum_text,
        market_jobs=market_jobs,
        student=student,
        role=role,
        mock_llm_override="End-to-end mock narrative."
    )
    
    # 1. Verify schema compliance (if it didn't raise, validation passed)
    assert roadmap.student_id == "STU_999"
    assert len(roadmap.semesters) > 0 # At least one semester planned
    assert roadmap.semesters[0] == ["CS101"] # Prereq first
    
    # 2. Verify ReasonChain Aggregation
    assert len(trace) > 0
    
    # Verify we have logs from ALL agents in the aggregated chain
    agent_names_in_trace = {step.agent_name for step in trace}
    
    expected_agents = {
        "CurriculumAgent",
        "MarketTrendsAgent",
        "SkillGapAgent",
        "CareerSimulatorAgent",
        "PlannerAgent"
    }
    
    assert expected_agents.issubset(agent_names_in_trace)
    
    # Verify chronological order (timestamp monotonic increase)
    for i in range(1, len(trace)):
        assert trace[i].timestamp >= trace[i-1].timestamp
