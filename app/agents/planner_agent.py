import json
import logging
import uuid
from typing import List, Dict, Any, Tuple, Optional, Set
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

class NoValidPathError(Exception):
    """Raised when no feasible roadmap path can be planned under given curriculum constraints."""
    pass

# Candidate Electives Catalogue per Semester (seeded for backward compatibility)
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
    Subject to graph prerequisite constraints (Neo4j / MockGraph) and credit caps.
    Stores queryable, structured reason chains linking courses to skill gaps, market signals, and prerequisite paths.
    """

    def _sync_catalogue_with_graph(self):
        """Ensures all courses from catalogue and default courses are synced into graph manager."""
        if not graph_manager.mock_graph.courses:
            return # Allow testing intentionally empty curriculum
        for c in ELECTIVE_CATALOGUE:
            graph_manager.add_course(c["code"], c["name"], c["credits"], c["semester"], "Elective")
            for p in c["prereqs"]:
                graph_manager.add_prerequisite(p, c["code"])
            for s in c["imparts"]:
                graph_manager.add_skill_mapping(c["code"], s, 1.0)

    def _gather_available_courses(self) -> List[Dict[str, Any]]:
        """
        Gathers all courses from the configured graph manager.
        Only syncs default elective catalogue if graph is in demo seed mode and empty.
        Does not merge hardcoded demo courses into user-ingested curriculum.
        """
        all_courses_dict = graph_manager.get_all_courses()
        if not all_courses_dict:
            return []

        course_skills_map = graph_manager.get_course_skills_map()
        all_courses = []
        for code, c_props in all_courses_dict.items():
            prereqs = graph_manager.get_prerequisites_for(code)
            imparts = course_skills_map.get(code, [])
            all_courses.append({
                "code": code,
                "name": c_props.get("name", code),
                "credits": c_props.get("credits", 4),
                "semester": c_props.get("semester", 1),
                "category": c_props.get("category", "Core"),
                "prereqs": prereqs,
                "imparts": imparts
            })
        return all_courses

    def generate_roadmap(
        self,
        student_id: str,
        max_credits_per_sem: int = 24,
        raise_on_infeasible: bool = False,
        target_role_id: Optional[str] = None
    ) -> RoadmapResponse:
        roadmap_id = f"rm_{uuid.uuid4().hex[:8]}"
        curriculum_source = getattr(graph_manager, "curriculum_source", "seeded_demo")

        # 1. Check for cycles in the curriculum prerequisite graph
        has_cycle, cyclic_nodes = graph_manager.detect_cycles()
        if has_cycle:
            msg = f"Prerequisite cycle detected in curriculum among courses: {cyclic_nodes}. Cannot produce a feasible topological roadmap."
            logger.error(msg)
            if raise_on_infeasible:
                raise NoValidPathError(msg)
            return RoadmapResponse(
                roadmap_id=roadmap_id,
                student_id=student_id,
                version=1,
                objective_function_score=0.0,
                semester_plans=[],
                reason_chains=[],
                semesters=[],
                curriculum_source=curriculum_source,
                status="infeasible",
                error=msg
            )

        # 2. Check for empty curriculum
        all_courses = self._gather_available_courses()
        if not all_courses:
            msg = "Curriculum database is empty. No courses available to plan a roadmap."
            logger.warning(msg)
            if raise_on_infeasible:
                raise NoValidPathError(msg)
            return RoadmapResponse(
                roadmap_id=roadmap_id,
                student_id=student_id,
                version=1,
                objective_function_score=0.0,
                semester_plans=[],
                reason_chains=[],
                semesters=[],
                curriculum_source="empty",
                status="infeasible",
                error=msg
            )

        profile = profiling_agent.get_profile(student_id)
        current_sem = profile.current_semester if profile else 5

        # 3. Fetch Skill Gaps and Map Gaps to Demands (safely resolving target role)
        effective_role = target_role_id or (profile.target_role if profile and profile.target_role else "ROLE_AIML")
        try:
            gap_analysis = skill_gap_agent.calculate_skill_gaps(student_id, target_role_id=effective_role)
        except ValueError:
            # Fallback to default canonical role if user provided an unmapped role string
            gap_analysis = skill_gap_agent.calculate_skill_gaps(student_id, target_role_id="ROLE_AIML")
        gap_scores = {g.skill_id: g.gap_score for g in gap_analysis.gaps}
        market_demands = {g.skill_id: g.market_demand_score for g in gap_analysis.gaps}
        is_sample_data = gap_analysis.is_sample_data

        # 4. Get Completed Courses from SQLite & Profile
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT course_code FROM student_courses WHERE student_id = ?", (student_id,))
        completed_codes = set(r["course_code"] for r in cursor.fetchall())
        conn.close()

        if profile and getattr(profile, "completed_courses", None):
            for cc in profile.completed_courses:
                completed_codes.add(cc.course_code)
        elif profile and getattr(profile, "credits_breakdown", None):
            completed_codes.update(profile.credits_breakdown.keys())

        # Target the top priority role-required skill gaps (highest deficit)
        role_req_gaps = gap_analysis.role_required_gaps if gap_analysis.role_required_gaps else gap_analysis.gaps
        target_skills = set(g.skill_id for g in role_req_gaps[:5])

        # 5. Greedy Topological Multi-Semester Optimization
        selected_courses: List[Dict[str, Any]] = []
        already_planned: Set[str] = set(completed_codes)
        semester_plans: List[SemesterPlan] = []
        reason_chains: List[ReasonChainItem] = []

        total_gap_closure = 0.0
        total_market_alignment = 0.0
        total_feasibility = 0.0
        total_workload_penalty = 0.0

        # Determine planning horizons
        start_sem = max(1, current_sem)
        end_sem = max(8, start_sem + 1)

        # Track courses completed prior to the current semester being scheduled
        # Prerequisites MUST be satisfied in earlier semesters (sem < current_sem)
        cleared_before_sem: Set[str] = set(completed_codes)

        for sem in range(start_sem, end_sem + 1):
            candidates = [
                c for c in all_courses
                if c["code"] not in already_planned and c["semester"] <= sem
            ]
            sem_courses: List[str] = []
            sem_credits = 0

            # Score each candidate course using objective terms
            scored_candidates = []
            for cand in candidates:
                is_feasible, missing, path = graph_manager.check_prerequisite_feasibility(cand["code"], list(cleared_before_sem))
                feasibility_val = 1.0 if is_feasible else 0.0

                # Gap closure contribution
                gap_val = sum(gap_scores.get(s, 0.0) for s in cand["imparts"])
                # Market alignment contribution
                market_val = (
                    sum(market_demands.get(s, 0.0) for s in cand["imparts"]) / max(1, len(cand["imparts"]))
                    if cand["imparts"] else 0.5
                )

                # Prioritize courses imparting target gap skills
                relevant_skills_count = sum(1 for s in cand["imparts"] if s in target_skills)
                relevance_boost = 0.5 if relevant_skills_count > 0 else 0.0

                # Candidate composite score using configured weights
                cand_score = (
                    (settings.WEIGHT_GAP_CLOSURE * (gap_val + relevance_boost)) +
                    (settings.WEIGHT_MARKET_ALIGNMENT * market_val) +
                    (settings.WEIGHT_FEASIBILITY * feasibility_val)
                )
                scored_candidates.append((cand_score, cand, is_feasible, path))

            # Select top feasible courses strictly honoring credit cap
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
            for cand_score, cand, is_feasible, path in scored_candidates:
                if is_feasible and (sem_credits + cand["credits"]) <= max_credits_per_sem:
                    # Avoid overpacking if we already have 4 courses in this semester and recommended credits met
                    if len(sem_courses) >= 4 and sem_credits >= settings.RECOMMENDED_CREDITS_PER_SEM:
                        continue
                    sem_courses.append(cand["code"])
                    sem_credits += cand["credits"]
                    already_planned.add(cand["code"])
                    selected_courses.append(cand)

                    # Accumulate objective function metrics
                    total_gap_closure += sum(gap_scores.get(s, 0.0) for s in cand["imparts"])
                    total_market_alignment += (
                        sum(market_demands.get(s, 0.0) for s in cand["imparts"]) / max(1, len(cand["imparts"]))
                        if cand["imparts"] else 0.5
                    )
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

            # Advance cleared prerequisites for subsequent semesters
            cleared_before_sem.update(sem_courses)

            # Workload penalty if credits exceed recommended bounds
            if sem_credits > settings.RECOMMENDED_CREDITS_PER_SEM:
                total_workload_penalty += (sem_credits - settings.RECOMMENDED_CREDITS_PER_SEM) * 0.05

            if sem_courses:
                semester_plans.append(SemesterPlan(
                    semester=sem,
                    planned_courses=sem_courses,
                    total_credits=sem_credits
                ))

        # Check if plan could be produced
        if not selected_courses:
            msg = "No feasible course combinations could be planned under the given prerequisite and credit constraints."
            logger.warning(msg)
            if raise_on_infeasible:
                raise NoValidPathError(msg)
            return RoadmapResponse(
                roadmap_id=roadmap_id,
                student_id=student_id,
                version=1,
                objective_function_score=0.0,
                semester_plans=[],
                reason_chains=[],
                semesters=[],
                curriculum_source=curriculum_source,
                status="infeasible",
                error=msg,
                is_sample_data=is_sample_data
            )

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

        semesters = [p.planned_courses for p in semester_plans]
        run_id = f"run_{roadmap_id}"

        # Save Roadmap and Reason Chains into SQLite
        try:
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
        except Exception as e:
            logger.warning(f"Failed to persist roadmap to SQLite: {e}")

        return RoadmapResponse(
            roadmap_id=roadmap_id,
            student_id=student_id,
            version=1,
            objective_function_score=round(objective_score, 4),
            semester_plans=semester_plans,
            reason_chains=reason_chains,
            semesters=semesters,
            estimated_time_to_completion_months=len(semesters) * 4,
            is_sample_data=is_sample_data,
            curriculum_source=curriculum_source,
            target_role=target_role_id,
            run_id=run_id,
            status="success"
        )

    def get_roadmap_trace(self, identifier: str) -> List[ReasonChainItem]:
        """
        Retrieves structured reason chains for a roadmap.
        Accepts either student_id or roadmap_id (e.g. 'rm_...' or 'run_rm_...').
        """
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        # 1. Try identifier as roadmap_id directly (with or without 'run_' prefix)
        clean_rm_id = identifier.replace("run_", "")
        cursor.execute("SELECT rationale_json FROM roadmap_reasons WHERE roadmap_id = ?", (clean_rm_id,))
        rows = cursor.fetchall()

        # 2. If not found, try identifier as student_id
        if not rows:
            cursor.execute("SELECT roadmap_id FROM roadmaps WHERE student_id = ? ORDER BY created_at DESC LIMIT 1", (identifier,))
            row = cursor.fetchone()
            if row:
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
