import os
import sys
import pytest

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import Course
from core.reason_chain import ReasonChain
from agents.curriculum_agent.agent import CurriculumAgent

class MockGraphClient:
    def __init__(self):
        self.queries = []
        
    def execute_write(self, query: str, parameters: dict = None):
        self.queries.append((query, parameters))
        return []

def test_curriculum_agent_parsing_and_ambiguity():
    graph_client = MockGraphClient()
    reason_chain = ReasonChain()
    agent = CurriculumAgent(graph_client=graph_client, reason_chain=reason_chain)
    
    # Synthetic curriculum snippet
    text = "CS401 Advanced Topics (3 credits, Fall). Prerequisite: CS301. CS405 Quantum Computing (3 credits). Prerequisite: some background in physics or math."
    
    result = agent.parse_curriculum_text(text)
    
    courses = result["courses"]
    ambiguous = result["ambiguous_extractions"]
    
    # Verify courses are extracted
    assert len(courses) == 2, f"Expected 2 courses, got {len(courses)}"
    
    cs401 = next((c for c in courses if c.code == "CS401"), None)
    cs405 = next((c for c in courses if c.code == "CS405"), None)
    
    assert cs401 is not None
    assert cs405 is not None
    
    # Verify CS401 resolved its explicit prerequisite
    assert len(cs401.prerequisites) == 1
    assert cs401.prerequisites[0].code == "CS301"
    
    # Verify CS405 flagged ambiguity and did NOT create an edge
    assert len(cs405.prerequisites) == 0
    assert len(ambiguous) == 1
    assert ambiguous[0]["course_code"] == "CS405"
    assert ambiguous[0]["needs_review"] == True
    assert "physics or math" in ambiguous[0]["raw_text"].lower()
    
    # Verify ReasonChain logged the decisions
    trace = reason_chain.get_trace()
    assert len(trace) > 0
    
    # Check if ambiguous log exists
    ambiguous_log = next((t for t in trace if t.step_id == "resolve_prereq_ambiguous_CS405"), None)
    assert ambiguous_log is not None
    assert "needs_review=True" in ambiguous_log.decision

def test_graph_ingestion_edges():
    graph_client = MockGraphClient()
    reason_chain = ReasonChain()
    agent = CurriculumAgent(graph_client=graph_client, reason_chain=reason_chain)
    
    text = "CS401 Advanced Topics (3 credits, Fall). Prerequisite: CS301."
    result = agent.parse_curriculum_text(text)
    
    agent.ingest_curriculum(result["courses"])
    
    # Verify the queries that were written
    # 1 for MERGE Course
    # 1 for MERGE Prerequisite edge
    assert len(graph_client.queries) == 2
    
    prereq_query, params = graph_client.queries[1]
    assert "PREREQUISITE_OF" in prereq_query
    assert params["course_code"] == "CS401"
    assert params["prereq_code"] == "CS301"
