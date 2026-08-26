import os
import json
import spacy
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from core.reason_chain import ReasonChain
from core.graph_client import GraphClient

class MarketTrendsAgent:
    """
    Agent responsible for analyzing job market data and computing skill demand scores.
    """
    # Explicit weights for the demand score formula
    W1_FREQ = 0.5    # How frequently a skill appears across job postings is the strongest baseline indicator.
    W2_RECENCY = 0.3 # Tech moves fast; recency ensures we capture trending skills.
    W3_SALARY = 0.2  # High salary implies premium value, but weighted lowest to not overshadow baseline required skills.

    def __init__(self, graph_client: GraphClient, reason_chain: ReasonChain):
        self.graph_client = graph_client
        self.reason_chain = reason_chain
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
            
        # For simplicity in this mock setup, we'll match against a known set of skills
        # Normally this would be a dynamic query pulling all `(:Skill)` nodes from the graph.
        self.known_skills = ["Python", "SQL", "C++", "Fortran", "React", "Data Structures", "Algorithms"]

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extracts skills from text using basic keyword matching against known skills."""
        doc = self.nlp(text)
        found_skills = []
        for skill in self.known_skills:
            if skill.lower() in text.lower():
                found_skills.append(skill)
        return list(set(found_skills))

    def compute_demand_scores(self, jobs: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Computes the demand score for skills found in the job dataset.
        Returns a dictionary mapping skill_name to demand_score.
        """
        if not jobs:
            return {}

        skill_stats = defaultdict(lambda: {"count": 0, "salaries": [], "latest_date": datetime.min.replace(tzinfo=timezone.utc)})
        
        # Current time reference for recency calculation (assuming now is around Aug 2026 based on mock data)
        now = datetime.now(timezone.utc)
        
        for job in jobs:
            skills = self.extract_skills_from_text(job.get("description", ""))
            
            # Parse date safely
            try:
                date_str = job.get("posted_date", "")
                if date_str.endswith("Z"):
                    date_str = date_str[:-1] + "+00:00"
                job_date = datetime.fromisoformat(date_str)
            except ValueError:
                job_date = datetime.min.replace(tzinfo=timezone.utc)
                
            salary = job.get("salary", 0)

            for skill in skills:
                skill_stats[skill]["count"] += 1
                skill_stats[skill]["salaries"].append(salary)
                if job_date > skill_stats[skill]["latest_date"]:
                    skill_stats[skill]["latest_date"] = job_date
                    
        if not skill_stats:
            return {}

        # Compute maxes for normalization
        max_count = max([stats["count"] for stats in skill_stats.values()]) or 1
        
        avg_salaries = {s: (sum(stats["salaries"])/len(stats["salaries"]) if stats["salaries"] else 0) for s, stats in skill_stats.items()}
        max_salary = max(avg_salaries.values()) or 1
        
        scores = {}
        for skill, stats in skill_stats.items():
            # 1. Normalized Frequency (0 to 1)
            norm_freq = stats["count"] / max_count
            
            # 2. Recency Weight (0 to 1)
            # Max penalty is 1.0 (very old). Decay over 3 years (~1000 days).
            days_old = (now - stats["latest_date"]).days
            recency = max(0.0, 1.0 - (days_old / 1000.0)) 
            
            # 3. Salary Correlation (0 to 1)
            salary_corr = avg_salaries[skill] / max_salary
            
            # Final Score Calculation
            final_score = (self.W1_FREQ * norm_freq) + (self.W2_RECENCY * recency) + (self.W3_SALARY * salary_corr)
            
            scores[skill] = round(final_score, 4)
            
            self.reason_chain.log_step(
                step_id=f"score_skill_{skill}_{now.strftime('%Y%m%d')}",
                agent_name="MarketTrendsAgent",
                input_summary=f"Skill: {skill}, Count: {stats['count']}, Avg Salary: {avg_salaries[skill]}, Days Old: {days_old}",
                decision=f"Computed Demand Score: {scores[skill]}",
                justification=f"w1({self.W1_FREQ})*{norm_freq:.2f} + w2({self.W2_RECENCY})*{recency:.2f} + w3({self.W3_SALARY})*{salary_corr:.2f}",
                score_used=scores[skill]
            )
            
        return scores
        
    def get_skill_score(self, scores: Dict[str, float], skill: str) -> float:
        """Safe getter for skill scores. Returns 0.0 if missing."""
        if skill not in scores:
            self.reason_chain.log_step(
                step_id=f"score_skill_missing_{skill}",
                agent_name="MarketTrendsAgent",
                input_summary=f"Skill: {skill} requested but absent from dataset",
                decision="Returned default 0.0 score",
                justification="Skill not found in recent job postings dataset",
                score_used=0.0
            )
            return 0.0
        return scores[skill]

    def update_graph_scores(self, scores: Dict[str, float]):
        """
        Writes demand scores back to (:Skill) nodes.
        Uses parallel arrays `demand_score_history` and `demand_score_timestamps`
        to maintain version history without breaking Neo4j property constraints.
        """
        timestamp_str = datetime.now(timezone.utc).isoformat()
        
        for skill, score in scores.items():
            query = """
            MATCH (s:Skill {name: $skill_name})
            SET s.demand_score_history = COALESCE(s.demand_score_history, []) + $score,
                s.demand_score_timestamps = COALESCE(s.demand_score_timestamps, []) + $timestamp
            RETURN s
            """
            result = self.graph_client.execute_write(query, {
                "skill_name": skill,
                "score": score,
                "timestamp": timestamp_str
            })
            
            if result:
                self.reason_chain.log_step(
                    step_id=f"update_graph_{skill}_{timestamp_str}",
                    agent_name="MarketTrendsAgent",
                    input_summary=f"Skill {skill} has new score {score}",
                    decision="Appended score and timestamp to parallel arrays on Skill node",
                    justification="Neo4j property versioning constraint strategy",
                    score_used=score
                )
