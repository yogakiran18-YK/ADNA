import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.main import app

client = TestClient(app)
auth = ("admin", "viva2026")

def test_roadmap_pipeline_endpoint():
    payload = {
        "student": {
            "student_id": "TEST_1",
            "current_skills": [],
            "completed_courses": []
        },
        "target_role": {
            "role_id": "R1",
            "title": "Software Engineer",
            "required_skills": ["Python"]
        }
    }
    
    # 1. Test POST roadmap
    response = client.post("/students/TEST_1/roadmap", json=payload, auth=auth)
    assert response.status_code == 200
    
    data = response.json()
    assert "run_id" in data
    assert "roadmap" in data
    assert "reason_chain_length" in data
    assert data["reason_chain_length"] > 0
    
    run_id = data["run_id"]
    
    # 2. Test GET reason-chain
    trace_resp = client.get(f"/reason-chain/{run_id}", auth=auth)
    assert trace_resp.status_code == 200
    
    trace_data = trace_resp.json()
    assert len(trace_data) == data["reason_chain_length"]
    
    # Verify unauthorized access is blocked
    bad_auth = ("admin", "wrongpassword")
    bad_resp = client.get(f"/reason-chain/{run_id}", auth=bad_auth)
    assert bad_resp.status_code == 401

def test_gap_report_endpoint():
    payload = {
        "student": {
            "student_id": "TEST_2",
            "current_skills": [],
            "completed_courses": []
        },
        "target_role": {
            "role_id": "R1",
            "title": "Software Engineer",
            "required_skills": ["Python"]
        }
    }
    response = client.post("/students/TEST_2/gap-report", json=payload, auth=auth)
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "TEST_2"
    assert "missing_skills" in data

def test_career_simulation_endpoint():
    payload = {
        "student": {
            "student_id": "TEST_3",
            "current_skills": [],
            "completed_courses": []
        },
        "target_role": {
            "role_id": "R1",
            "title": "Software Engineer",
            "required_skills": ["Python"]
        }
    }
    response = client.post("/students/TEST_3/career-simulation", json=payload, auth=auth)
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == "TEST_3"
    assert "ml_ranking_score" in data
    assert "shap_explanations" in data
