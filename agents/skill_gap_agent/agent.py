import os
import sys
from typing import List, Dict, Any
from core.schemas import StudentProfile, JobRole, GapReport
from core.reason_chain import ReasonChain
from core.graph_client import GraphClient

class SkillGapAgent:
    def __init__(self, graph_client: GraphClient, reason_chain: ReasonChain):
        self.graph_client = graph_client
        self.reason_chain = reason_chain

    def compute_gap_report(self, student: StudentProfile, role: JobRole) -> GapReport:
        """
        Compares a student profile against target job role requirements and market demand scores.
        
        Gap Score Formula:
            gap_score(skill) = demand_score(skill) * (1 - student_proficiency(skill))
            
        Proficiency logic (simplified for Phase 4):
            - 1.0 if the student has completed ANY course that TEACHES the skill.
            - 0.0 otherwise.
            Note: This can be scaled (e.g. 0.0 to 1.0 based on grades/depth) when schema supports it.
        """
        
        # 1. Determine what skills the student already has from completed courses
        # We query the graph to see what skills the student's completed courses TEACH.
        student_skills = set(student.current_skills)
        if student.completed_courses:
            # Query graph for skills taught by completed courses
            query = """
            MATCH (c:Course)-[:TEACHES]->(s:Skill)
            WHERE c.code IN $completed_courses
            RETURN DISTINCT s.name AS skill_name
            """
            results = self.graph_client.execute_read(query, {"completed_courses": student.completed_courses})
            for record in results:
                student_skills.add(record["skill_name"])

        # 2. Fetch the latest demand scores for the required skills
        required_skills = role.required_skills
        demand_scores = {}
        
        if required_skills:
            # We respect Phase 3 schema: read the last element of the demand_score_history array.
            query = """
            MATCH (s:Skill)
            WHERE s.name IN $required_skills
            // COALESCE with empty array, then get the last element (index -1)
            // If the array is empty or missing, it will return null
            RETURN s.name AS skill_name, 
                   s.demand_score_history[-1] AS latest_score
            """
            results = self.graph_client.execute_read(query, {"required_skills": required_skills})
            for record in results:
                # Default to 0.0 if not found
                demand_scores[record["skill_name"]] = record.get("latest_score") or 0.0
                
        # 3. Compute Gap Scores
        gap_scores = []
        
        for skill in required_skills:
            demand = demand_scores.get(skill, 0.0)
            
            # Proficiency: 1.0 if they have the skill (from profile or courses), 0.0 if not
            proficiency = 1.0 if skill in student_skills else 0.0
            
            # Formula: gap_score(skill) = demand_score(skill) * (1 - student_proficiency(skill))
            gap = demand * (1.0 - proficiency)
            
            self.reason_chain.log_step(
                step_id=f"gap_compute_{student.student_id}_{skill}",
                agent_name="SkillGapAgent",
                input_summary=f"Skill: {skill}, Demand: {demand}, Proficiency: {proficiency}",
                decision=f"Computed gap score: {gap}",
                justification="gap = demand * (1 - proficiency)",
                score_used=gap
            )
            
            # Only add to missing skills if there is an actual gap (gap > 0)
            # Or if proficiency is 0 (to catch 0-demand skills that are still required)
            if proficiency < 1.0:
                gap_scores.append({"skill": skill, "gap_score": round(gap, 4)})
                
        # 4. Rank missing skills by gap_score descending
        gap_scores.sort(key=lambda x: x["gap_score"], reverse=True)
        
        # 5. Format for the GapReport (List[Dict[str, float]])
        # E.g. [{"Python": 0.85}, {"SQL": 0.5}]
        missing_skills_formatted = [{item["skill"]: item["gap_score"]} for item in gap_scores]
        
        report = GapReport(
            student_id=student.student_id,
            target_role_id=role.role_id,
            missing_skills=missing_skills_formatted
        )
        
        return report
