import json
import logging
import uuid
import numpy as np
from typing import List, Dict, Any, Optional
from app.models.schemas import CareerSimulationRequest, CareerSimulationResponse, CareerTrajectoryItem


from app.agents.profiling_agent import profiling_agent
from app.agents.skill_gap_agent import skill_gap_agent
from app.database.sqlite_db import get_sqlite_connection
from app.database.chroma_db import vector_store

logger = logging.getLogger(__name__)

# Predefined Career Trajectory Archetypes for Grounded RAG Simulation
TRAJECTORY_ARCHETYPES = [
    {
        "id": "traj_01",
        "title": "Machine Learning & AI Research Specialist",
        "description": "Focuses on deep learning architectures, PyTorch model design, and NLP research.",
        "enabling_courses": ["AIML301", "AIML302", "CSE401", "CSE405"],
        "required_skill_weights": {"skill_pytorch": 0.4, "skill_nlp": 0.4, "skill_python": 0.2}
    },
    {
        "id": "traj_02",
        "title": "MLOps & Cloud Systems Engineer",
        "description": "Focuses on production ML deployment, containerized infrastructure, and scalable APIs.",
        "enabling_courses": ["AIML301", "AIML401", "CSE303", "CSE304", "CSE410"],
        "required_skill_weights": {"skill_mlops": 0.35, "skill_docker": 0.3, "skill_aws": 0.2, "skill_fastapi": 0.15}
    },
    {
        "id": "traj_03",
        "title": "Full-Stack AI Application Developer",
        "description": "Combines backend microservices, SQL databases, and lightweight AI model integration.",
        "enabling_courses": ["CSE202", "CSE303", "CSE304", "AIML301"],
        "required_skill_weights": {"skill_python": 0.3, "skill_sql": 0.3, "skill_fastapi": 0.2, "skill_docker": 0.2}
    }
]

class CareerSimulatorAgent:
    """
    Career Simulator Agent (Hybrid Model):
    Combines LLM-style RAG trajectory proposals with an independent, non-LLM
    Statistical/ML Scorer that evaluates career fit scores using cosine matrix operations.
    Logs both outputs to SQLite to defend model independence in IEEE paper write-ups.
    """

    def compute_independent_statistical_fit(self, student_id: str, trajectory_req_skills: Dict[str, float]) -> float:
        """
        Independent Statistical Scorer:
        Computes cosine similarity between Student Profile Vector (E_u) and Trajectory Requirement Vector.
        Operates completely independently of LLM prompt outputs.
        """
        E_u = np.array(profiling_agent.get_student_profile_vector(student_id))
        E_u_norm = np.linalg.norm(E_u) + 1e-9

        # Construct Trajectory Skill Vector
        t_vec = np.zeros(384)
        for s_id, weight in trajectory_req_skills.items():
            s_emb = np.array(vector_store.get_embedding(f"Skill {s_id}"))
            t_vec += (s_emb * weight)
        
        t_norm = np.linalg.norm(t_vec) + 1e-9
        cosine_sim = float(np.dot(E_u, t_vec) / (E_u_norm * t_norm))
        # Scale to [0, 1]
        fit_score = max(0.0, min(1.0, (cosine_sim + 1.0) / 2.0))
        return round(fit_score, 4)

    def simulate_career_trajectories(self, student_id: str, target_role_override: Optional[str] = None) -> CareerSimulationResponse:
        profile = profiling_agent.get_profile(student_id)
        gap_analysis = skill_gap_agent.calculate_skill_gaps(student_id)
        
        simulated_items: List[CareerTrajectoryItem] = []
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        for traj in TRAJECTORY_ARCHETYPES:
            # 1. Grounded RAG LLM Simulation Reasoning Generation
            # (In production: LLM API call grounded in profile + gaps; Mocked for testable performance)
            llm_reasoning_text = (
                f"Trajectory '{traj['title']}' aligns with your target interests in {profile.interests if profile else 'AI/ML'}. "
                f"Recommended enabling electives include {', '.join(traj['enabling_courses'])} to close identified skill gaps."
            )
            # Standardized LLM score baseline
            llm_score = 0.85

            # 2. Independent Statistical / ML Scorer
            stat_fit_score = self.compute_independent_statistical_fit(student_id, traj["required_skill_weights"])

            # 3. Hybrid Composite Score
            composite_score = round((0.5 * llm_score) + (0.5 * stat_fit_score), 4)

            item = CareerTrajectoryItem(
                trajectory_id=traj["id"],
                title=traj["title"],
                description=traj["description"],
                key_enabling_courses=traj["enabling_courses"],
                llm_reasoning=llm_reasoning_text,
                statistical_fit_score=stat_fit_score,
                composite_score=composite_score
            )
            simulated_items.append(item)

            # Log simulation to SQLite for dual-output auditability
            sim_id = f"sim_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
            INSERT INTO career_simulations (sim_id, student_id, trajectory_title, llm_reasoning, ml_fit_score, composite_score)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (sim_id, student_id, traj["title"], llm_reasoning_text, stat_fit_score, composite_score))

        conn.commit()
        conn.close()

        simulated_items.sort(key=lambda x: x.composite_score, reverse=True)

        return CareerSimulationResponse(
            student_id=student_id,
            simulated_trajectories=simulated_items
        )

simulator_agent = CareerSimulatorAgent()
