import os
import sys
import networkx as nx
from itertools import combinations
from typing import List, Dict, Any, Set

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import StudentProfile, JobRole, GapReport, CareerSimulationResult, RoadmapPlan
from core.reason_chain import ReasonChain
from core.graph_client import GraphClient

class NoValidPathError(Exception):
    pass

class PlannerAgent:
    def __init__(self, graph_client: GraphClient, reason_chain: ReasonChain, max_credits_per_semester: int = 15):
        self.graph_client = graph_client
        self.reason_chain = reason_chain
        self.max_credits = max_credits_per_semester

    def _build_course_graph(self) -> nx.DiGraph:
        """
        Extracts the curriculum graph from Neo4j into NetworkX.
        Returns a directed graph where edges point from prerequisite -> course.
        """
        G = nx.DiGraph()
        
        # 1. Fetch all courses
        courses_query = """
        MATCH (c:Course)
        RETURN c.code AS code, c.credits AS credits
        """
        courses = self.graph_client.execute_read(courses_query)
        for c in courses:
            G.add_node(c["code"], credits=c["credits"])
            
        # 2. Fetch all PREREQUISITE_OF edges
        edges_query = """
        MATCH (p:Course)-[:PREREQUISITE_OF]->(c:Course)
        RETURN p.code AS prereq, c.code AS course
        """
        edges = self.graph_client.execute_read(edges_query)
        for e in edges:
            G.add_edge(e["prereq"], e["course"])
            
        # 3. Fetch skills taught by courses
        skills_query = """
        MATCH (c:Course)-[:TEACHES]->(s:Skill)
        RETURN c.code AS code, collect(s.name) AS skills
        """
        skills = self.graph_client.execute_read(skills_query)
        for s in skills:
            if s["code"] in G.nodes:
                G.nodes[s["code"]]["skills"] = s["skills"]
                
        return G

    def generate_roadmap(self, student: StudentProfile, role: JobRole, gap_report: GapReport, sim_result: CareerSimulationResult) -> RoadmapPlan:
        """
        Generates an optimized semester-by-semester RoadmapPlan.
        """
        G = self._build_course_graph()
        
        # Parse gap report into a fast lookup dict mapping skill -> gap_score
        gap_dict = {}
        for skill_map in gap_report.missing_skills:
            for skill, score in skill_map.items():
                gap_dict[skill] = score
                
        completed_courses = set(student.completed_courses)
        semesters = []
        
        # We need to cover all courses that teach missing skills, or just loop until no more useful courses
        # For simplicity, we loop until gap_dict is empty or we can't take any more courses
        
        # Identify target courses (any course that teaches a skill in our gap_dict)
        target_courses = set()
        for node in G.nodes:
            node_skills = G.nodes[node].get("skills", [])
            for s in node_skills:
                if s in gap_dict:
                    target_courses.add(node)
                    
        # If target courses also have prerequisites we haven't taken, we need to take those prerequisites too.
        # So we actually need to find all ancestors of target_courses.
        all_required_courses = set()
        for tc in target_courses:
            if tc in G:
                ancestors = nx.ancestors(G, tc)
                all_required_courses.add(tc)
                all_required_courses.update(ancestors)
                
        # Remove already completed courses
        all_required_courses -= completed_courses
        
        while all_required_courses:
            # Find available courses for this semester (prereqs met)
            available = []
            for c in all_required_courses:
                if "credits" not in G.nodes.get(c, {}):
                    # This is a phantom node (e.g. from a broken edge) and cannot be taken
                    continue
                    
                prereqs = set(G.predecessors(c))
                if prereqs.issubset(completed_courses):
                    available.append(c)
                    
            if not available:
                raise NoValidPathError("Impossible prerequisite chain or missing node detected. No valid path to complete requirements.")
                
            # Heuristic Search (Greedy): Find valid combination of available courses that maximizes reward
            # Reward = sum(gap_score_reduction) for skills taught by the courses
            # Penalty(credit_overload) is handled by strictly generating combinations <= MAX_CREDITS
            
            best_combo = []
            best_reward = -1.0
            
            # Generate all subsets of available courses
            # To avoid exponential explosion in test, we limit combination size (e.g. max 5 courses)
            max_courses_in_combo = min(len(available), 5)
            
            for r in range(1, max_courses_in_combo + 1):
                for combo in combinations(available, r):
                    total_credits = sum(G.nodes[c].get("credits", 3) for c in combo)
                    if total_credits <= self.max_credits:
                        # Calculate reward
                        reward = 0.0
                        combo_skills = set()
                        for c in combo:
                            for s in G.nodes[c].get("skills", []):
                                combo_skills.add(s)
                                
                        for s in combo_skills:
                            reward += gap_dict.get(s, 0.0)
                            
                        # Slight reward for taking prerequisites (to unblock future courses even if gap=0 for this specific course)
                        # This prevents the agent from ignoring a 0-gap prereq required for a high-gap advanced course
                        # In the real paper this might be Backpropagation of Rewards. Here we add a small heuristic +0.1 per course.
                        reward += 0.1 * len(combo)
                        
                        if reward > best_reward:
                            best_reward = reward
                            best_combo = list(combo)
                            
            if not best_combo:
                raise NoValidPathError(f"No valid course combination found under {self.max_credits} credits.")
                
            # Log the decision
            justification = f"Selected {best_combo} reducing gap via skills {[s for c in best_combo for s in G.nodes[c].get('skills', []) if s in gap_dict]}. "
            justification += f"Based on ML Score {sim_result.ml_ranking_score} from CareerSimulatorAgent and GapReport from SkillGapAgent."
            
            self.reason_chain.log_step(
                step_id=f"plan_semester_{len(semesters)+1}_{student.student_id}",
                agent_name="PlannerAgent",
                input_summary=f"Available courses: {available}. Max credits: {self.max_credits}",
                decision=f"Assigned {best_combo} to Semester {len(semesters)+1}",
                justification=justification,
                score_used=best_reward
            )
            
            # Update state
            semesters.append(best_combo)
            completed_courses.update(best_combo)
            all_required_courses.difference_update(best_combo)
            
            # Update gap dict
            for c in best_combo:
                for s in G.nodes[c].get("skills", []):
                    if s in gap_dict:
                        del gap_dict[s]
                        
        plan = RoadmapPlan(
            student_id=student.student_id,
            semesters=semesters,
            estimated_time_to_completion_months=len(semesters) * 4 # Assuming 4 months per semester
        )
        return plan
