import os
import sys
import json
from unittest.mock import MagicMock
from datetime import datetime, timezone, timedelta

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.reason_chain import ReasonChain
from agents.market_trends_agent.agent import MarketTrendsAgent

class MockGraphClient:
    def __init__(self):
        self.queries = []
        
    def execute_write(self, query: str, parameters: dict = None):
        self.queries.append((query, parameters))
        return [{"s": "mock_node"}] # mock returned node

def test_market_trends_agent_scoring():
    graph_client = MockGraphClient()
    reason_chain = ReasonChain()
    agent = MarketTrendsAgent(graph_client=graph_client, reason_chain=reason_chain)
    
    # We will construct a synthetic jobs list reflecting:
    # 1. Rising Demand (Python) - recent, high frequency, high salary
    # 2. Stale/Old Data (Fortran) - old dates, lower salary
    # 3. Absent (Quantum Blockchain) - absent
    
    now = datetime.now(timezone.utc)
    recent_date = now.isoformat()
    old_date = (now - timedelta(days=1500)).isoformat() # Very old (over 3 years)

    jobs = [
        # Python jobs (Recent, 3 mentions)
        {"job_id": "1", "description": "Needs Python.", "salary": 120000, "posted_date": recent_date},
        {"job_id": "2", "description": "Expert in Python required.", "salary": 140000, "posted_date": recent_date},
        {"job_id": "3", "description": "Python developer.", "salary": 130000, "posted_date": recent_date},
        
        # Fortran jobs (Old, 2 mentions)
        {"job_id": "4", "description": "Legacy Fortran system.", "salary": 70000, "posted_date": old_date},
        {"job_id": "5", "description": "Fortran dev.", "salary": 80000, "posted_date": old_date}
    ]
    
    scores = agent.compute_demand_scores(jobs)
    
    # Assert Python score > Fortran score
    assert "Python" in scores
    assert "Fortran" in scores
    assert scores["Python"] > scores["Fortran"]
    
    # Python should be max frequency (1.0), max recency (1.0), max salary (1.0) -> Score around 1.0
    # Formula: 0.5 * 1.0 + 0.3 * 1.0 + 0.2 * 1.0 = 1.0 (approx)
    assert scores["Python"] == 1.0
    
    # Fortran should be penalized on recency and salary
    # Recency penalty: days > 1000 -> recency = 0.0
    # Frequency: 2/3 = 0.66
    # Salary: 75k / 130k = 0.57
    # Score: 0.5*0.66 + 0.3*0.0 + 0.2*0.57 = 0.33 + 0 + 0.114 = ~0.44
    assert scores["Fortran"] < 0.5
    
    # Check absent skill
    absent_score = agent.get_skill_score(scores, "Quantum Blockchain")
    assert absent_score == 0.0
    
    # Verify ReasonChain
    trace = reason_chain.get_trace()
    assert len(trace) > 0
    
    # Check that absent skill log was created
    absent_log = next((t for t in trace if "absent from dataset" in t.input_summary), None)
    assert absent_log is not None
    assert absent_log.score_used == 0.0

def test_graph_update_parallel_arrays():
    graph_client = MockGraphClient()
    reason_chain = ReasonChain()
    agent = MarketTrendsAgent(graph_client=graph_client, reason_chain=reason_chain)
    
    scores = {"Python": 0.95, "Fortran": 0.4}
    agent.update_graph_scores(scores)
    
    assert len(graph_client.queries) == 2
    
    python_query, python_params = graph_client.queries[0]
    assert "demand_score_history" in python_query
    assert "demand_score_timestamps" in python_query
    assert python_params["skill_name"] == "Python"
    assert python_params["score"] == 0.95
    assert "timestamp" in python_params
