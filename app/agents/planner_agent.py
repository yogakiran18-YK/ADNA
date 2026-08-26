import json
import logging
import uuid
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.models.schemas import (
    RoadmapGenerateRequest, RoadmapResponse, SemesterPlan, ReasonChainItem
)
from app.models.domain import compute_planner_objective
from app.agents.profiling_agent import profiling_agent
from app.agents.skill_gap_agent import skill_gap_agent
from app.agents.curriculum_agent import curriculum_agent
from app.database.sqlite_db import get_sqlite_connection
from app.database.neo4j_db import graph_manager

logger = logging.getLogger(__name__)

# Sample Candidate Electives Catalogue per Semester
ELECTIVE_CATALOGUE = [
    # Sem 5 Electives
    {"code": "AIML301", "name": "Deep Learning & PyTorch", "credits": 4, "semester": 5, "prereqs": ["CSE201"], "imparts": ["skill_pytorch", "skill_nlp"]},
    {"code": "CSE303", "name": "Web Architecture & FastAPI", "credits": 4, "semester": 5, "prereqs": ["CSE101"], "imparts": ["skill_fastapi", "skill_python"]},
    {"code": "CSE304", "name": "Cloud Computing & Docker", "credits": 4, "semester": 5, "prereqs": ["CSE101"], "imparts": ["skill_docker", "skill_aws"]},
    # Sem 6 Electives
    {"code": "AIML302", "name": "Natural Language Processing", "credits": 4, "semester": 6, "prereqs": ["AIML301"], "imparts": ["skill_nlp"]},
    {"code": "AIML401", "name": "MLOps Engineering & Deployment", "credits": 4, "semester": 6, "prereqs": ["AIML301"], "imparts": ["skill_mlops", "skill_docker"]},
    {"code": "CSE410", "name": "Advanced DevOps & Kubernetes", "credits": 4, "semester": 6, "prereqs": ["CSE304"], "imparts": ["skill_docker", "skill_aws"]},
    # Sem 7 & 8 Electives
    {"code": "CSE401", "name": "Neural Networks & Vision", "credits": 4, "semester": 7, "prereqs": ["AIML301"], "imparts": ["skill_pytorch"]},
    {"code": "CSE405", "name": "Large Language Models & RAG", "credits": 4, "semester": 8, "prereqs": ["AIML302"], "imparts": ["skill_nlp", "skill_pytorch"]}
]

class PlannerAgent:
    """
    Planner Agent:
    Solves an explicit multi-criteria optimization problem maximizing J(X) over remaining semesters:
    J(X) = wg * GapClosure + wm * MarketAlignment + wp * FeasibilityScore - ww * WorkloadPenalty
    Subject to graph prerequisite constraints (Neo4j) and credit caps.
    Stores queryable, structured reason chains linking courses to skill gaps, market signals, and prerequisite paths.
    """

    def generate_roadmap(self, student_id: str, max_credits_per_sem: int = 24) -> RoadmapResponse:
        profile = profiling_agent.get_profile(student_id)
        current_sem = profile.current_semester if profile else 5
        
        # 1. Fetch Skill Gaps and Map Gaps to Demands
        gap_analysis = skill_gap_agent.calculate_skill_gaps(student_id)
        gap_scores = {g.skill_id: g.gap_score for g in gap_analysis.gaps}
        market_demands = {g.skill_id: g.market_demand_score for g in gap_analysis.gaps}

        # 2. Get Completed Courses
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT course_code FROM student_courses WHERE student_id = ?", (student_id,))
        completed_codes = [r["course_code"] for r in cursor.fetchall()]
        conn.close()

        # Ingest Catalogue into Neo4j graph if not present
        for c in ELECTIVE_CATALOGUE:
            graph_manager.add_course(c["code"], c["name"], c["credits"], c["semester"], "Elective")
            for p in c["prereqs"]:
                graph_manager.add_prerequisite(p, c["code"])

        # 3. Greedy Heuristic Optimization per remaining semester
        selected_courses: List[Dict[str, Any]] = []
        already_planned: set = set(completed_codes)
        semester_plans: List[SemesterPlan] = []
        reason_chains: List[ReasonChainItem] = []

        total_gap_closure = 0.0
        total_market_alignment = 0.0
        total_feasibility = 0.0
        total_workload_penalty = 0.0

        for sem in range(current_sem, 9):
            candidates = [c for c in ELECTIVE_CATALOGUE if c["semester"] == sem and c["code"] not in already_planned]
            sem_courses: List[str] = []
            sem_credits = 0

            # Score each candidate course using objective terms
            scored_candidates = []
            for cand in candidates:
                # Prerequisite feasibility check via Neo4j
                is_feasible, missing, path = graph_manager.check_prerequisite_feasibility(cand["code"], list(already_planned))
                feasibility_val = 1.0 if is_feasible else 0.0

                # Gap closure contribution
                gap_val = sum(gap_scores.get(s, 0.0) for s in cand["imparts"])
                # Market alignment contribution
                market_val = sum(market_demands.get(s, 0.0) for s in cand["imparts"]) / max(1, len(cand["imparts"]))

                # Candidate composite score
                cand_score = (0.5 * gap_val) + (0.3 * market_val) + (0.2 * feasibility_val)
                scored_candidates.append((cand_score, cand, is_feasible, path))

            # Select top feasible courses up to credit cap
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            for cand_score, cand, is_feasible, path in scored_candidates:
                if is_feasible and (sem_credits + cand["credits"]) <= max_credits_per_sem:
                    sem_courses.append(cand["code"])
                    sem_credits += cand["credits"]
                    already_planned.add(cand["code"])
                    selected_courses.append(cand)

                    # Accumulate objective function metrics
                    total_gap_closure += sum(gap_scores.get(s, 0.0) for s in cand["imparts"])
                    total_market_alignment += sum(market_demands.get(s, 0.0) for s in cand["imparts"]) / max(1, len(cand["imparts"]))
                    total_feasibility += 1.0

                    # Construct Structured Reason Chain Item
                    primary_skill = cand["imparts"][0] if cand["imparts"] else "skill_dsa"
                    reason_item = ReasonChainItem(
                        course_code=cand["code"],
                        target_skill_id=primary_skill,
                        market_signal_demand=market_demands.get(primary_skill, 0.8),
                        prerequisite_feasibility_path=path,
                        score_contribution=round(cand_score, 4),
                        explanation_prose=f"Selected {cand['code']} ({cand['name']}) in Semester {sem} to address skill gap '{primary_skill}' (Market Demand: {market_demands.get(primary_skill, 0.8):.2f}) with verified prerequisite path {path}."
                    )
                    reason_chains.append(reason_item)

            # Workload penalty if credits exceed recommended bounds
            if sem_credits > settings.RECOMMENDED_CREDITS_PER_SEM:
                total_workload_penalty += (sem_credits - settings.RECOMMENDED_CREDITS_PER_SEM) * 0.05

            semester_plans.append(SemesterPlan(
                semester=sem,
                planned_courses=sem_courses,
                total_credits=sem_credits
            ))

        # Compute Final Objective Score J(X)
        count = max(1, len(selected_courses))
        norm_gap_closure = total_gap_closure / count
        norm_market_align = total_market_alignment / count
        norm_feasibility = total_feasibility / count

        objective_score = compute_planner_objective(
            gap_closure=norm_gap_closure,
            market_alignment=norm_market_align,
            feasibility_score=norm_feasibility,
            workload_penalty=total_workload_penalty,
            wg=settings.WEIGHT_GAP_CLOSURE,
            wm=settings.WEIGHT_MARKET_ALIGNMENT,
            wp=settings.WEIGHT_FEASIBILITY,
            ww=settings.WEIGHT_WORKLOAD_PENALTY
        )

        roadmap_id = f"rm_{uuid.uuid4().hex[:8]}"

        # Save Roadmap and Reason Chains into SQLite
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO roadmaps (roadmap_id, student_id, version, semester_plans_json, objective_score)
        VALUES (?, ?, ?, ?, ?)
        """, (roadmap_id, student_id, 1, json.dumps([p.model_dump() for p in semester_plans]), objective_score))

        for item in reason_chains:
            cursor.execute("""
            INSERT INTO roadmap_reasons (roadmap_id, course_code, target_skill_id, market_signal_demand, graph_prereq_path_json, rationale_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (roadmap_id, item.course_code, item.target_skill_id, item.market_signal_demand, json.dumps(item.prerequisite_feasibility_path), json.dumps(item.model_dump())))


        conn.commit()
        conn.close()

        return RoadmapResponse(
            roadmap_id=roadmap_id,
            student_id=student_id,
            version=1,
            objective_function_score=objective_score,
            semester_plans=semester_plans,
            reason_chains=reason_chains
        )

    def get_roadmap_trace(self, student_id: str) -> List[ReasonChainItem]:
        """Retrieves structured reason chains for a student's latest roadmap."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT roadmap_id FROM roadmaps WHERE student_id = ? ORDER BY created_at DESC LIMIT 1", (student_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return []

        roadmap_id = row["roadmap_id"]
        cursor.execute("SELECT rationale_json FROM roadmap_reasons WHERE roadmap_id = ?", (roadmap_id,))
        rows = cursor.fetchall()
        conn.close()

        items = []
        for r in rows:
            data = json.loads(r["rationale_json"])
            items.append(ReasonChainItem(**data))
        return items

planner_agent = PlannerAgent()
