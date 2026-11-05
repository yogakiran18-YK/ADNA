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

# Subject-to-role curriculum alignment taxonomy
ROLE_ENABLING_SUBJECTS: Dict[str, Dict[str, List[str]]] = {
    'ROLE_AIML': {
        'critical': ['CS401', 'CS601', 'CS701', 'CS703', 'CS704', 'CS803', 'AIML301', 'AIML302'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS301', 'MA101', 'MA102', 'MA201', 'CSE101', 'CSE201']
    },
    'ROLE_GENAI': {
        'critical': ['CS704', 'CS701', 'CS601', 'CS803', 'CS401', 'CS702', 'CSE405'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS301', 'MA101', 'MA102', 'CSE101', 'CSE201']
    },
    'ROLE_DS': {
        'critical': ['CS402', 'CS601', 'CS703', 'MA102', 'MA201', 'CS201'],
        'foundational': ['CS101', 'CS102', 'CS301', 'MA101', 'CS401', 'CSE101']
    },
    'ROLE_DATA_ANALYST': {
        'critical': ['CS402', 'MA201', 'CS601', 'CS703', 'CS102'],
        'foundational': ['CS101', 'MA101', 'MA102', 'CS201', 'CSE101']
    },
    'ROLE_FSD': {
        'critical': ['CS503', 'CS402', 'CS702', 'CS204', 'CS501', 'CSE303'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS302', 'CS603', 'CSE101', 'CSE201']
    },
    'ROLE_BACKEND': {
        'critical': ['CS302', 'CS402', 'CS501', 'CS702', 'CS201', 'CS301', 'CSE303'],
        'foundational': ['CS101', 'CS102', 'CS203', 'CS204', 'CS603', 'CSE101']
    },
    'ROLE_DEVOPS': {
        'critical': ['CS603', 'CS302', 'CS501', 'CS702', 'CS604', 'CS803', 'CSE304', 'CSE410'],
        'foundational': ['CS101', 'CS102', 'CS201', 'CS203', 'CS402', 'CSE101']
    },
    'ROLE_DEV': {
        'critical': ['CS201', 'CS301', 'CS302', 'CS402', 'CS204', 'CS501', 'CSE201'],
        'foundational': ['CS101', 'CS102', 'CS103', 'CS202', 'CS203', 'MA101', 'CSE101']
    }
}

TRAJECTORY_ARCHETYPES = [
    {
        "id": "traj_01",
        "title": "Machine Learning & AI Research Specialist",
        "description": "Focuses on deep learning architectures, PyTorch model design, and NLP systems.",
        "enabling_courses": ["CS401", "CS601", "CS701", "CS704"],
        "required_skill_weights": {"skill_pytorch": 0.4, "skill_nlp": 0.4, "skill_python": 0.2}
    },
    {
        "id": "traj_02",
        "title": "MLOps & Cloud Systems Engineer",
        "description": "Focuses on production ML deployment, containerized infrastructure, and scalable APIs.",
        "enabling_courses": ["CS601", "CS603", "CS702", "CS803"],
        "required_skill_weights": {"skill_mlops": 0.35, "skill_docker": 0.3, "skill_aws": 0.2, "skill_fastapi": 0.15}
    },
    {
        "id": "traj_03",
        "title": "Full-Stack AI Application Developer",
        "description": "Combines backend microservices, SQL databases, and web interface architectures.",
        "enabling_courses": ["CS402", "CS501", "CS503", "CS702"],
        "required_skill_weights": {"skill_python": 0.3, "skill_sql": 0.3, "skill_fastapi": 0.2, "skill_docker": 0.2}
    }
]

class CareerSimulatorAgent:
    """
    Career Simulator Agent:
    Computes a transparent, evidence-grounded heuristic career-fit estimate
    based on student curriculum progress, role subject specialization,
    skill coverage, and real market signals.
    Does NOT claim unvalidated machine learning prediction accuracy or external LLM calls.
    """

    def _resolve_role_key(self, role_str: str) -> str:
        role_upper = (role_str or "").upper()
        if "AIML" in role_upper or "MACHINE LEARNING" in role_upper or "AI" in role_upper:
            return "ROLE_AIML"
        if "GENAI" in role_upper or "GENERATIVE" in role_upper or "LLM" in role_upper:
            return "ROLE_GENAI"
        if "DATA SCIEN" in role_upper or "STATIST" in role_upper:
            return "ROLE_DS"
        if "ANALYST" in role_upper or "BUSINESS INTELLIGENCE" in role_upper:
            return "ROLE_DATA_ANALYST"
        if "FULL STACK" in role_upper or "WEB" in role_upper:
            return "ROLE_FSD"
        if "BACKEND" in role_upper:
            return "ROLE_BACKEND"
        if "DEVOPS" in role_upper or "CLOUD" in role_upper or "SRE" in role_upper:
            return "ROLE_DEVOPS"
        return "ROLE_DEV"

    def compute_heuristic_fit(
        self,
        completed_courses: List[str],
        role_key: str,
        gaps: List[Any],
        current_semester: int = 5
    ) -> Dict[str, Any]:
        courses_set = set(c.strip().upper() for c in completed_courses)
        enablers = ROLE_ENABLING_SUBJECTS.get(role_key, ROLE_ENABLING_SUBJECTS["ROLE_DEV"])
        crit_set = set(enablers["critical"])
        found_set = set(enablers["foundational"])

        completed_crit = courses_set.intersection(crit_set)
        completed_found = courses_set.intersection(found_set)

        # 1. Course Completion Progress (32 degree courses standard)
        completion_ratio = min(1.0, len(courses_set) / 32.0)

        # 2. Role Subject Specialization
        crit_score = len(completed_crit) / max(1, len(crit_set))
        found_score = len(completed_found) / max(1, len(found_set))
        role_subject_relevance = 0.65 * crit_score + 0.35 * found_score

        # 3. Skill Coverage Ratio
        total_gaps = len(gaps)
        covered_count = sum(1 for g in gaps if getattr(g, "course_mastery_factor", 0.0) >= 0.7 or getattr(g, "gap_score", 1.0) <= 0.25)
        skill_coverage_ratio = (covered_count / max(1, total_gaps)) if total_gaps > 0 else 0.50

        # 4. Market Alignment Factor
        if gaps:
            avg_demand = sum(getattr(g, "market_demand_score", 0.7) for g in gaps) / len(gaps)
        else:
            avg_demand = 0.75
        market_alignment = max(0.2, min(1.0, avg_demand))

        # Weights: Completion (0.25), Specialization (0.35), Skills (0.25), Market (0.15)
        raw_score = (
            0.25 * completion_ratio +
            0.35 * role_subject_relevance +
            0.25 * skill_coverage_ratio +
            0.15 * market_alignment
        )
        final_score = round(max(0.08, min(0.98, raw_score)), 4)

        # Transparent Feature Contribution Attribution (Deviation from 0.50 baseline)
        shap_explanations = {
            "Course Completion Progress": round(0.25 * (completion_ratio - 0.50), 4),
            "Role Subject Specialization": round(0.35 * (role_subject_relevance - 0.50), 4),
            "Skill Coverage Ratio": round(0.25 * (skill_coverage_ratio - 0.50), 4),
            "Market Alignment Factor": round(0.15 * (market_alignment - 0.50), 4)
        }

        # Domain Competencies
        math_foundations = {'CS101', 'CS102', 'MA101', 'MA102', 'PH101', 'EE101', 'CS103', 'CY101', 'CS202', 'MA201', 'CSE101'}
        core_systems = {'CS201', 'CS203', 'CS204', 'CS301', 'CS302', 'CS402', 'CS501', 'CS502', 'CSE201'}
        adv_specialization = {'CS401', 'CS503', 'CS601', 'CS602', 'CS603', 'CS604', 'CS701', 'CS702', 'CS703', 'CS704', 'CS801', 'CS802', 'CS803', 'AIML301', 'AIML302', 'AIML401'}

        domain_competency = {
            "Foundations & Math": round(min(1.0, len(courses_set.intersection(math_foundations)) / 10.0), 3),
            "Core Data Structures & Systems": round(min(1.0, len(courses_set.intersection(core_systems)) / 8.0), 3),
            "Role Specialization Subjects": round(role_subject_relevance, 3),
            "Applied Engineering & Systems": round(min(1.0, len(courses_set.intersection(adv_specialization)) / 10.0), 3)
        }

        # 8-Semester Readiness Progression Curve
        semester_readiness = {}
        for sem in range(1, 9):
            sem_key = f"Sem {sem}"
            if sem < current_semester:
                fraction = sem / max(1, current_semester)
                curve_val = 0.15 + fraction * (final_score - 0.15)
                semester_readiness[sem_key] = round(max(0.10, curve_val), 3)
            elif sem == current_semester:
                semester_readiness[sem_key] = round(final_score, 3)
            else:
                steps_remaining = 8 - current_semester
                step_idx = sem - current_semester
                projected = final_score + (0.94 - final_score) * (step_idx / max(1, steps_remaining))
                semester_readiness[sem_key] = round(min(0.96, projected), 3)

        # Cross-Role Fit Benchmarks
        benchmark_roles = [
            ("ROLE_AIML", "AI / ML Engineer"),
            ("ROLE_GENAI", "Generative AI Engineer"),
            ("ROLE_DS", "Data Scientist"),
            ("ROLE_FSD", "Full Stack Developer"),
            ("ROLE_DEVOPS", "Cloud & DevOps SRE"),
            ("ROLE_DEV", "Core Software Engineer")
        ]
        adjacent_role_scores = {}
        for b_id, b_label in benchmark_roles:
            b_enablers = ROLE_ENABLING_SUBJECTS.get(b_id, ROLE_ENABLING_SUBJECTS["ROLE_DEV"])
            b_crit = set(b_enablers["critical"])
            b_found = set(b_enablers["foundational"])
            b_rel = 0.65 * (len(courses_set.intersection(b_crit)) / max(1, len(b_crit))) + 0.35 * (len(courses_set.intersection(b_found)) / max(1, len(b_found)))
            b_score = 0.25 * completion_ratio + 0.35 * b_rel + 0.25 * skill_coverage_ratio + 0.15 * 0.75
            adjacent_role_scores[b_label] = round(max(0.10, min(0.96, b_score)), 3)

        if final_score >= 0.82:
            match_tier = "Tier 1: Industry Placement-Ready"
        elif final_score >= 0.68:
            match_tier = "Tier 2: Competitive Candidate"
        elif final_score >= 0.48:
            match_tier = "Tier 3: Emerging Trajectory"
        else:
            match_tier = "Tier 4: Foundation Building"

        stage_name = (
            f"Semester {current_semester}" if 1 <= current_semester <= 8 else "Senior"
        )

        return {
            "score": final_score,
            "shap_explanations": shap_explanations,
            "domain_competency": domain_competency,
            "semester_readiness": semester_readiness,
            "adjacent_role_scores": adjacent_role_scores,
            "match_tier": match_tier,
            "stage_name": stage_name,
            "completed_critical": list(completed_crit),
            "missing_critical": list(crit_set - completed_crit),
            "completed_count": len(completed_crit),
            "missing_count": len(crit_set - completed_crit)
        }

    def simulate_career_trajectories(
        self,
        student_id: str,
        target_role_override: Optional[str] = None
    ) -> CareerSimulationResponse:
        profile = profiling_agent.get_profile(student_id)
        target_role = target_role_override or (profile.target_role if profile else "AI / Machine Learning Engineer")
        current_sem = profile.current_semester if profile else 5
        role_key = self._resolve_role_key(target_role)

        gap_analysis = skill_gap_agent.calculate_skill_gaps(student_id)
        gaps = gap_analysis.gaps

        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT course_code FROM student_courses WHERE student_id = ?", (student_id,))
        completed_courses = [r["course_code"] for r in cursor.fetchall()]
        conn.close()

        heuristics = self.compute_heuristic_fit(completed_courses, role_key, gaps, current_sem)
        fit_score = heuristics["score"]

        # Trajectories
        simulated_items: List[CareerTrajectoryItem] = []
        for traj in TRAJECTORY_ARCHETYPES:
            # Trajectory fit calculation based on enabling courses
            traj_courses = set(traj["enabling_courses"])
            cleared_traj = traj_courses.intersection(set(completed_courses))
            traj_fit = round(0.40 * (len(cleared_traj) / max(1, len(traj_courses))) + 0.60 * fit_score, 4)

            reasoning = (
                f"Trajectory '{traj['title']}' aligns with {target_role}. "
                f"Cleared {len(cleared_traj)}/{len(traj_courses)} enabling courses ({', '.join(cleared_traj) if cleared_traj else 'None'}). "
                f"Upcoming recommended subjects: {', '.join(traj_courses - cleared_traj)}."
            )

            simulated_items.append(CareerTrajectoryItem(
                trajectory_id=traj["id"],
                title=traj["title"],
                description=traj["description"],
                key_enabling_courses=traj["enabling_courses"],
                llm_reasoning=reasoning,
                statistical_fit_score=traj_fit,
                composite_score=round((0.5 * 0.85) + (0.5 * traj_fit), 4),
                is_estimate=True
            ))

        simulated_items.sort(key=lambda x: x.composite_score, reverse=True)

        # Grounded narrative synthesized from real profile
        cleared_str = f"Cleared critical domain courses: {', '.join(heuristics['completed_critical'])}." if heuristics['completed_critical'] else "No upper-division specialization subjects completed yet."
        upcoming_str = f"Recommended upcoming courses: {', '.join(heuristics['missing_critical'][:3])}." if heuristics['missing_critical'] else "All key degree specialization courses cleared!"
        missing_skills_list = [g.skill_name for g in gaps[:3]] if gaps else []
        skills_str = f"Primary skill gaps to address: {', '.join(missing_skills_list)}." if missing_skills_list else "No major skill gaps identified against market baseline."

        narrative = (
            f"Curriculum Advisory Assessment for {student_id} (Target: {target_role}):\n\n"
            f"• Standing: {heuristics['stage_name']} ({len(completed_courses)} Degree Courses Completed, Heuristic Fit Score: {fit_score * 100:.1f}%).\n"
            f"• Coursework Analysis: {cleared_str} {upcoming_str}\n"
            f"• Market Skill Signals: {skills_str}\n"
            f"• Illustrative Career Trajectory: Projected to reach competitive entry-level alignment "
            f"by Semester {min(8, current_sem + 2)} upon completing required prerequisite courses and closing practical gaps. "
            f"(Note: This score is a heuristic benchmark estimate for degree guidance, not an empirical employment guarantee.)"
        )

        critical_enablers_summary = {
            "completed": heuristics["completed_critical"],
            "missing": heuristics["missing_critical"],
            "completed_count": heuristics["completed_count"],
            "missing_count": heuristics["missing_count"],
            "stage": heuristics["stage_name"]
        }

        # Save simulation records to SQLite
        try:
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            for item in simulated_items:
                sim_id = f"sim_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                INSERT INTO career_simulations (sim_id, student_id, trajectory_title, llm_reasoning, ml_fit_score, composite_score)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (sim_id, student_id, item.title, item.llm_reasoning, item.statistical_fit_score, item.composite_score))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"Could not persist simulation record: {e}")

        return CareerSimulationResponse(
            student_id=student_id,
            simulated_trajectories=simulated_items,
            target_role_id=target_role,
            role_title=target_role,
            ml_ranking_score=fit_score,
            heuristic_fit_score=fit_score,
            match_tier=heuristics["match_tier"],
            is_estimate=True,
            model_type="transparent_heuristic_estimate",
            shap_explanations=heuristics["shap_explanations"],
            llm_narrative=narrative,
            semester_readiness=heuristics["semester_readiness"],
            domain_competency=heuristics["domain_competency"],
            adjacent_role_scores=heuristics["adjacent_role_scores"],
            critical_enablers_summary=critical_enablers_summary
        )

simulator_agent = CareerSimulatorAgent()
