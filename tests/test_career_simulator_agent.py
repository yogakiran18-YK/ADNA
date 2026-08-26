import os
import sys
import pytest

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import StudentProfile, JobRole, GapReport
from core.reason_chain import ReasonChain
from agents.career_simulator_agent.agent import CareerSimulatorAgent

def test_independence_of_ml_and_llm():
    """
    Test explicitly proves that altering the LLM's text output has 0.0 impact 
    on the ML feature vector and numeric score.
    """
    chain = ReasonChain()
    agent = CareerSimulatorAgent(chain)
    
    student = StudentProfile(student_id="S1", current_skills=[], completed_courses=["CS101", "CS102"])
    role = JobRole(role_id="R1", title="Data Scientist", required_skills=["Python", "SQL", "Stats"])
    gap_report = GapReport(
        student_id="S1", 
        target_role_id="R1", 
        missing_skills=[{"Stats": 0.8}, {"SQL": 0.6}]
    )
    
    # Run 1: Mock LLM output A
    result_A = agent.simulate_career(student, role, gap_report, mock_llm_override="This is narrative A.")
    
    # Run 2: Mock LLM output B
    result_B = agent.simulate_career(student, role, gap_report, mock_llm_override="This is narrative B.")
    
    # Verify outputs are different for the LLM
    assert result_A.llm_narrative == "This is narrative A."
    assert result_B.llm_narrative == "This is narrative B."
    
    # Verify the ML score is identically preserved down to the float
    assert result_A.ml_ranking_score == result_B.ml_ranking_score
    
    # Verify SHAP explanations are populated for all 4 features
    shap_keys = set(result_A.shap_explanations.keys())
    assert shap_keys == {"avg_gap_score", "avg_demand_score", "completed_credit_count", "skill_overlap_ratio"}
    
    # Verify SHAP values are mathematically identical between runs
    for k in shap_keys:
        assert result_A.shap_explanations[k] == result_B.shap_explanations[k]

def test_reason_chain_logs():
    """
    Test that both components log to the reason chain independently.
    """
    chain = ReasonChain()
    agent = CareerSimulatorAgent(chain)
    
    student = StudentProfile(student_id="S2", current_skills=[], completed_courses=[])
    role = JobRole(role_id="R2", title="Tester", required_skills=["QA"])
    gap_report = GapReport(student_id="S2", target_role_id="R2", missing_skills=[{"QA": 0.9}])
    
    agent.simulate_career(student, role, gap_report)
    
    trace = chain.get_trace()
    assert len(trace) == 2
    
    llm_log = next((t for t in trace if t.step_id.startswith("sim_llm_")), None)
    ml_log = next((t for t in trace if t.step_id.startswith("sim_ml_")), None)
    
    assert llm_log is not None
    assert ml_log is not None
    
    assert "LLM" in llm_log.input_summary
    assert "Features:" in ml_log.input_summary
