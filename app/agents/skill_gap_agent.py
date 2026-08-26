import logging
from typing import List, Dict, Any
import numpy as np
from app.config import settings
from app.models.schemas import SkillGapItem, SkillGapAnalysisResponse
from app.models.domain import compute_skill_gap_score
from app.agents.profiling_agent import profiling_agent
from app.agents.market_agent import market_agent, SKILL_TAXONOMY
from app.database.sqlite_db import get_sqlite_connection
from app.database.neo4j_db import graph_manager
from app.database.chroma_db import vector_store

logger = logging.getLogger(__name__)

# Elective mapping database helper for candidate electives that impart skills
SKILL_TO_ELECTIVE_MAP = {
    "skill_pytorch": ["AIML301", "CSE401"], # Deep Learning, Neural Networks
    "skill_tensorflow": ["AIML301", "CSE402"],
    "skill_nlp": ["AIML302", "CSE405"], # Natural Language Processing
    "skill_docker": ["CSE304", "CSE410"], # Cloud Computing & DevOps
    "skill_aws": ["CSE304", "CSE411"],
    "skill_mlops": ["AIML401"], # MLOps Engineering
    "skill_sql": ["CSE202"], # Database Systems
    "skill_dsa": ["CSE201"], # Data Structures
    "skill_fastapi": ["CSE303"] # Web Architecture
}

class SkillGapAnalyzerAgent:
    """
    Skill Gap Analyzer Agent:
    Compares student profile embedding (E_u) against market skill vectors (E_s),
    applies the explicit mathematical Skill Gap Formula G(s, u),
    and maps each identified gap to candidate curriculum electives in Neo4j.
    """

    def calculate_skill_gaps(self, student_id: str) -> SkillGapAnalysisResponse:
        profile = profiling_agent.get_profile(student_id)
        target_role = profile.target_role if profile else "AI/ML Engineer"
        
        # 1. Fetch Student Profile Vector E_u
        E_u = np.array(profiling_agent.get_student_profile_vector(student_id))
        E_u_norm = np.linalg.norm(E_u) + 1e-9

        # 2. Fetch Market Trends & Demand Scores
        market_trends = market_agent.process_job_postings([])
        market_skills = market_trends.top_skills
        
        # 3. Fetch Student Completed Courses & Calculate Mastery Factor C_mastery
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT course_code, grade_point FROM student_courses WHERE student_id = ?", (student_id,))
        completed_records = cursor.fetchall()
        completed_map = {row["course_code"]: row["grade_point"] for row in completed_records}
        conn.close()

        gap_items: List[SkillGapItem] = []

        for skill in market_skills:
            # Vector Similarity S_sim(E_u, E_s)
            E_s_raw = vector_store.get_embedding(f"{skill.skill_name} in {skill.category}")
            E_s = np.array(E_s_raw)
            E_s_norm = np.linalg.norm(E_s) + 1e-9
            
            raw_cosine = float(np.dot(E_u, E_s) / (E_u_norm * E_s_norm))
            # Scale cosine from [-1, 1] to [0, 1]
            scaled_sim = max(0.0, min(1.0, (raw_cosine + 1.0) / 2.0))

            # Compute Course Mastery Factor C_mastery
            c_mastery = 0.0
            candidate_courses = SKILL_TO_ELECTIVE_MAP.get(skill.skill_id, [])
            for c_code in candidate_courses:
                if c_code in completed_map:
                    grade_ratio = completed_map[c_code] / 10.0
                    c_mastery = max(c_mastery, grade_ratio)

            # Apply Explicit Formula: G(s, u) = [w1*D(s) + w2*R(s)] * [1 - S_sim] * [1 - C_mastery]
            gap_score = compute_skill_gap_score(
                market_demand=skill.demand_score,
                recency_decay=skill.recency_decay_score,
                semantic_similarity=scaled_sim,
                course_mastery=c_mastery,
                w1=settings.WEIGHT_MARKET_DEMAND,
                w2=settings.WEIGHT_RECENCY_DECAY
            )

            # Recommended Electives (Filter out already completed electives)
            uncompleted_electives = [c for c in candidate_courses if c not in completed_map]

            gap_items.append(SkillGapItem(
                skill_id=skill.skill_id,
                skill_name=skill.skill_name,
                category=skill.category,
                market_demand_score=skill.demand_score,
                semantic_similarity=round(scaled_sim, 4),
                course_mastery_factor=round(c_mastery, 4),
                gap_score=gap_score,
                recommended_elective_codes=uncompleted_electives
            ))

        # Sort by gap score descending
        gap_items.sort(key=lambda x: x.gap_score, reverse=True)

        return SkillGapAnalysisResponse(
            student_id=student_id,
            target_role=target_role,
            total_gaps_identified=len(gap_items),
            gaps=gap_items
        )

skill_gap_agent = SkillGapAnalyzerAgent()
