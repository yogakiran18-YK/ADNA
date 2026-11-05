import logging
from typing import List, Dict, Any, Optional, Tuple
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

# Curated Role Definitions mapping role IDs/titles to target-role required skills
ROLE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "ROLE_AIML": {
        "id": "ROLE_AIML",
        "title": "AI / Machine Learning Engineer",
        "required_skills": ["skill_pytorch", "skill_python", "skill_nlp", "skill_mlops", "skill_tensorflow", "skill_dsa"],
        "aliases": [
            "ai / machine learning engineer", "ai & machine learning engineer", "ai and machine learning engineer",
            "ai/ml engineer", "machine learning engineer", "aiml", "cloud mlops engineer", "mlops engineer"
        ]
    },
    "ROLE_GENAI": {
        "id": "ROLE_GENAI",
        "title": "Generative AI & LLM Solutions Engineer",
        "required_skills": ["skill_pytorch", "skill_nlp", "skill_python", "skill_fastapi"],
        "aliases": [
            "generative ai & llm solutions engineer", "generative ai and llm solutions engineer",
            "genai", "llm engineer", "prompt engineer"
        ]
    },
    "ROLE_FULLSTACK": {
        "id": "ROLE_FULLSTACK",
        "title": "Full Stack Web Developer",
        "required_skills": ["skill_python", "skill_fastapi", "skill_sql", "skill_docker", "skill_dsa"],
        "aliases": [
            "role_fsd", "full stack web developer", "fullstack developer", "full stack developer", "fsd"
        ]
    },
    "ROLE_BACKEND": {
        "id": "ROLE_BACKEND",
        "title": "Backend Systems Engineer",
        "required_skills": ["skill_python", "skill_fastapi", "skill_sql", "skill_docker", "skill_dsa"],
        "aliases": ["backend systems engineer", "backend developer", "backend engineer"]
    },
    "ROLE_DEVOPS": {
        "id": "ROLE_DEVOPS",
        "title": "DevOps & SRE Engineer",
        "required_skills": ["skill_docker", "skill_aws", "skill_python", "skill_fastapi"],
        "aliases": [
            "devops & sre engineer", "devops and sre engineer", "devops engineer",
            "sre", "cloud engineer", "cloud mlops engineer"
        ]
    },
    "ROLE_CLOUD_ARCH": {
        "id": "ROLE_CLOUD_ARCH",
        "title": "Cloud Solutions Architect",
        "required_skills": ["skill_aws", "skill_docker", "skill_fastapi", "skill_sql"],
        "aliases": ["cloud solutions architect", "cloud architect"]
    },
    "ROLE_DS": {
        "id": "ROLE_DS",
        "title": "Data Scientist & Analytics Specialist",
        "required_skills": ["skill_python", "skill_sql", "skill_pytorch", "skill_dsa"],
        "aliases": [
            "data scientist & analytics specialist", "data scientist and analytics specialist",
            "data scientist", "ds"
        ]
    },
    "ROLE_DATA_ANALYST": {
        "id": "ROLE_DATA_ANALYST",
        "title": "Business Intelligence & Data Analyst",
        "required_skills": ["skill_sql", "skill_python", "skill_dsa"],
        "aliases": [
            "business intelligence & data analyst", "business intelligence and data analyst",
            "data analyst", "bi analyst"
        ]
    },
    "ROLE_DE": {
        "id": "ROLE_DE",
        "title": "Data Engineer & Big Data Architect",
        "required_skills": ["skill_sql", "skill_python", "skill_aws", "skill_dsa"],
        "aliases": [
            "data engineer & big data architect", "data engineer and big data architect",
            "data engineer"
        ]
    },
    "ROLE_DEV": {
        "id": "ROLE_DEV",
        "title": "Core Software Engineer",
        "required_skills": ["skill_python", "skill_dsa", "skill_sql"],
        "aliases": ["core software engineer", "software engineer", "software developer", "dev"]
    },
    "ROLE_SEC": {
        "id": "ROLE_SEC",
        "title": "Cybersecurity Analyst & Systems Auditor",
        "required_skills": ["skill_python", "skill_docker", "skill_dsa", "skill_aws"],
        "aliases": [
            "cybersecurity analyst & systems auditor", "cybersecurity analyst and systems auditor",
            "security engineer", "cybersecurity analyst"
        ]
    },
    "ROLE_CUSTOM": {
        "id": "ROLE_CUSTOM",
        "title": "Custom Career Goal",
        "required_skills": ["skill_python", "skill_dsa"],
        "aliases": ["custom career goal", "custom"]
    }
}

def _normalize_role_str(s: str) -> str:
    import re
    s = s.lower().replace('&', ' and ').replace('/', ' and ').replace('+', ' and ').replace('-', ' ')
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    return ' '.join(s.split())

def resolve_target_role(role_input: Optional[str]) -> Tuple[str, str, List[str]]:
    """
    Resolves role identifier or title into (canonical_id, canonical_title, required_skills).
    Raises ValueError for unknown/unsupported role inputs.
    """
    if not role_input or not role_input.strip():
        r = ROLE_DEFINITIONS["ROLE_AIML"]
        return r["id"], r["title"], list(r["required_skills"])

    clean = role_input.strip().upper()
    if clean in ROLE_DEFINITIONS:
        r = ROLE_DEFINITIONS[clean]
        return r["id"], r["title"], list(r["required_skills"])

    clean_lower = role_input.strip().lower()
    for r_id, r_info in ROLE_DEFINITIONS.items():
        if r_info["title"].lower() == clean_lower:
            return r_info["id"], r_info["title"], list(r_info["required_skills"])
        if clean_lower in [a.lower() for a in r_info.get("aliases", [])]:
            return r_info["id"], r_info["title"], list(r_info["required_skills"])

    # Fuzzy normalized check for punctuation/conjunction variations (&, /, and)
    norm_input = _normalize_role_str(role_input)
    for r_id, r_info in ROLE_DEFINITIONS.items():
        if _normalize_role_str(r_info["title"]) == norm_input:
            return r_info["id"], r_info["title"], list(r_info["required_skills"])
        for alias in r_info.get("aliases", []):
            if _normalize_role_str(alias) == norm_input:
                return r_info["id"], r_info["title"], list(r_info["required_skills"])

    valid_roles = list(ROLE_DEFINITIONS.keys())
    raise ValueError(f"Unknown or unsupported target role '{role_input}'. Supported roles: {valid_roles}")

class SkillGapAnalyzerAgent:
    """
    Skill Gap Analyzer Agent:
    Compares student profile embedding (E_u) against market skill vectors (E_s),
    applies the explicit mathematical Skill Gap Formula G(s, u),
    and maps each identified gap to candidate curriculum electives in Neo4j.
    Operates role-specifically to compute role-required gaps vs broader market skills.
    """

    def calculate_skill_gaps(
        self,
        student_id: str,
        target_role_override: Optional[str] = None,
        target_role_id: Optional[str] = None,
        custom_required_skills: Optional[List[str]] = None
    ) -> SkillGapAnalysisResponse:
        profile = profiling_agent.get_profile(student_id)
        effective_role_input = target_role_override or target_role_id or (profile.target_role if profile else "ROLE_AIML")

        canonical_role_id, canonical_role_title, role_skills = resolve_target_role(effective_role_input)
        if custom_required_skills:
            role_skills = custom_required_skills

        # 1. Fetch Student Profile Vector E_u
        E_u = np.array(profiling_agent.get_student_profile_vector(student_id))
        E_u_norm = np.linalg.norm(E_u) + 1e-9

        # 2. Fetch Market Trends & Demand Scores from real ingested postings
        market_trends = market_agent.get_current_demand_scores()
        market_skills = market_trends.top_skills

        # 3. Fetch Student Completed Courses & Calculate Mastery Factor C_mastery
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT course_code, grade_point FROM student_courses WHERE student_id = ?", (student_id,))
        completed_records = cursor.fetchall()
        completed_map = {row["course_code"]: row["grade_point"] for row in completed_records}
        conn.close()

        # Find courses that teach skills from graph abstraction
        course_skills_map = graph_manager.get_course_skills_map()
        graph_skill_courses: Dict[str, List[str]] = {}
        for c_code, s_list in course_skills_map.items():
            for s_id in s_list:
                if s_id not in graph_skill_courses:
                    graph_skill_courses[s_id] = []
                if c_code not in graph_skill_courses[s_id]:
                    graph_skill_courses[s_id].append(c_code)

        role_required_items: List[SkillGapItem] = []
        broader_market_items: List[SkillGapItem] = []
        unmapped_skills: List[str] = []

        # Check for unmapped role skills
        for rs in role_skills:
            if rs not in SKILL_TAXONOMY and rs not in graph_skill_courses:
                unmapped_skills.append(rs)

        for skill in market_skills:
            is_req = skill.skill_id in role_skills
            relevance = "role_required" if is_req else "broader_market"

            # Vector Similarity S_sim(E_u, E_s)
            E_s_raw = vector_store.get_embedding(f"{skill.skill_name} in {skill.category}")
            E_s = np.array(E_s_raw)
            E_s_norm = np.linalg.norm(E_s) + 1e-9

            raw_cosine = float(np.dot(E_u, E_s) / (E_u_norm * E_s_norm))
            # Scale cosine from [-1, 1] to [0, 1]
            scaled_sim = max(0.0, min(1.0, (raw_cosine + 1.0) / 2.0))

            # Candidate courses from graph skill mappings
            candidate_courses = graph_skill_courses.get(skill.skill_id, [])

            # Compute Course Mastery Factor C_mastery honestly
            c_mastery = 0.0
            for c_code in candidate_courses:
                if c_code in completed_map:
                    gp = completed_map[c_code]
                    grade_ratio = (gp / 10.0) if (gp is not None and gp >= 0.0) else 0.8
                    c_mastery = max(c_mastery, min(1.0, grade_ratio))

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

            item = SkillGapItem(
                skill_id=skill.skill_id,
                skill_name=skill.skill_name,
                category=skill.category,
                market_demand_score=skill.demand_score,
                semantic_similarity=round(scaled_sim, 4),
                course_mastery_factor=round(c_mastery, 4),
                gap_score=gap_score,
                recommended_elective_codes=uncompleted_electives,
                is_role_required=is_req,
                role_relevance=relevance
            )

            if is_req:
                role_required_items.append(item)
            else:
                broader_market_items.append(item)

        # Sort each partition by gap score descending
        role_required_items.sort(key=lambda x: x.gap_score, reverse=True)
        broader_market_items.sort(key=lambda x: x.gap_score, reverse=True)

        # Overall gaps: role-required gaps first, followed by broader market skills
        all_gaps = role_required_items + broader_market_items

        # Role-specific missing skills formatted for downstream consumer
        missing_skills_formatted = [
            {item.skill_name: item.gap_score}
            for item in role_required_items
            if item.gap_score > 0 or item.course_mastery_factor < 1.0
        ]

        return SkillGapAnalysisResponse(
            student_id=student_id,
            target_role=canonical_role_title,
            target_role_id=canonical_role_id,
            target_role_title=canonical_role_title,
            total_gaps_identified=len(role_required_items),
            gaps=all_gaps,
            role_required_gaps=role_required_items,
            broader_market_gaps=broader_market_items,
            unmapped_skills=unmapped_skills,
            missing_skills=missing_skills_formatted,
            is_sample_data=market_trends.is_sample_data
        )

skill_gap_agent = SkillGapAnalyzerAgent()
