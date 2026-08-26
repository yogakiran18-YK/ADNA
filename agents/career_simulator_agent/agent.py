import os
import sys
import numpy as np
import shap
from typing import Dict, Any, Tuple
from sklearn.ensemble import GradientBoostingRegressor

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import StudentProfile, JobRole, GapReport, CareerSimulationResult
from core.reason_chain import ReasonChain

class CareerSimulatorAgent:
    def __init__(self, reason_chain: ReasonChain):
        self.reason_chain = reason_chain
        self.model = self._train_mock_model()
        self.feature_names = [
            "avg_gap_score", 
            "avg_demand_score", 
            "completed_credit_count", 
            "skill_overlap_ratio"
        ]

    def _train_mock_model(self):
        """
        Trains a quick mock GradientBoostingRegressor so we have real weights 
        and can generate genuine SHAP values during inference.
        In production, this would load a pre-trained model artifact.
        """
        # Synthetic data: 4 features
        # [avg_gap, avg_demand, completed_credits, overlap_ratio]
        X = np.array([
            [0.1, 0.9, 120, 0.95], # Great fit
            [0.8, 0.5, 30,  0.2],  # Poor fit
            [0.5, 0.7, 60,  0.5],  # Medium fit
            [0.2, 0.8, 90,  0.8],  # Good fit
            [0.9, 0.2, 10,  0.1]   # Terrible fit
        ])
        y = np.array([0.95, 0.1, 0.5, 0.8, 0.05])
        
        model = GradientBoostingRegressor(n_estimators=10, random_state=42)
        model.fit(X, y)
        return model

    def _generate_llm_narrative(self, student: StudentProfile, role: JobRole, gap_report: GapReport, mock_override: str = None) -> str:
        """
        Component A: The LLM Qualitative Narrative.
        This provides advisory context but DOES NOT influence the ML ranking.
        """
        if mock_override is not None:
            narrative = mock_override
        else:
            # Stub for actual LLM call (e.g. OpenAI/Anthropic)
            narrative = (
                f"Based on the profile for {student.student_id}, aiming for {role.title}, "
                f"there are {len(gap_report.missing_skills)} missing skills. "
                "With these gaps closed by the upcoming semesters, plausible roles include "
                f"entry-level {role.title} or adjacent junior positions."
            )
            
        self.reason_chain.log_step(
            step_id=f"sim_llm_{student.student_id}_{role.role_id}",
            agent_name="CareerSimulatorAgent",
            input_summary="Provided profile, role, and gap report to LLM",
            decision="Generated qualitative narrative",
            justification="Advisory component executed (Component A)",
            score_used=None
        )
        return narrative

    def _compute_ml_ranking(self, student: StudentProfile, role: JobRole, gap_report: GapReport) -> Tuple[float, Dict[str, float]]:
        """
        Component B: The ML Quantitative Ranking.
        This is strictly independent of the LLM narrative.
        """
        # 1. Feature Engineering
        # avg_gap_score
        gaps = [list(g.values())[0] for g in gap_report.missing_skills] if gap_report.missing_skills else [0.0]
        avg_gap_score = sum(gaps) / len(gaps)
        
        # avg_demand_score (For mock purposes, inversely correlated to gap if gap is 0, or just use a fixed mock value based on role)
        # In a real scenario, we'd fetch this from the graph or pass it in.
        avg_demand_score = 0.8 
        
        # completed_credit_count (Mocking 3 credits per course)
        completed_credit_count = len(student.completed_courses) * 3
        
        # skill_overlap_ratio
        req_count = len(role.required_skills)
        missing_count = len(gap_report.missing_skills)
        overlap_ratio = (req_count - missing_count) / req_count if req_count > 0 else 1.0

        # Feature Vector
        X_infer = np.array([[avg_gap_score, avg_demand_score, completed_credit_count, overlap_ratio]])
        
        # 2. Prediction
        ml_score = float(self.model.predict(X_infer)[0])
        
        # 3. SHAP Explainability
        explainer = shap.Explainer(self.model)
        shap_values = explainer(X_infer)
        
        # Map SHAP values to feature names
        shap_dict = {
            self.feature_names[i]: float(shap_values.values[0][i])
            for i in range(len(self.feature_names))
        }
        
        self.reason_chain.log_step(
            step_id=f"sim_ml_{student.student_id}_{role.role_id}",
            agent_name="CareerSimulatorAgent",
            input_summary=f"Features: {X_infer[0].tolist()}",
            decision=f"Computed ML ranking score: {ml_score:.4f}",
            justification="Independent ML prediction with SHAP explainability (Component B)",
            score_used=ml_score
        )
        
        return ml_score, shap_dict

    def simulate_career(self, student: StudentProfile, role: JobRole, gap_report: GapReport, mock_llm_override: str = None) -> CareerSimulationResult:
        """
        Combines Component A and Component B into the final result.
        """
        # Component A
        llm_narrative = self._generate_llm_narrative(student, role, gap_report, mock_override=mock_llm_override)
        
        # Component B
        ml_ranking_score, shap_explanations = self._compute_ml_ranking(student, role, gap_report)
        
        # Combination
        return CareerSimulationResult(
            student_id=student.student_id,
            target_role_id=role.role_id,
            ml_ranking_score=round(ml_ranking_score, 4),
            shap_explanations=shap_explanations,
            llm_narrative=llm_narrative
        )
