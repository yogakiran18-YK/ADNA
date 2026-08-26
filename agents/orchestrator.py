import os
import sys
from typing import List, Dict, Any, Tuple

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import Course, StudentProfile, JobRole, GapReport, CareerSimulationResult, RoadmapPlan
from core.reason_chain import ReasonChain, ReasonStep
from core.graph_client import GraphClient

from agents.curriculum_agent.agent import CurriculumAgent
from agents.market_trends_agent.agent import MarketTrendsAgent
from agents.skill_gap_agent.agent import SkillGapAgent
from agents.career_simulator_agent.agent import CareerSimulatorAgent
from agents.planner_agent.agent import PlannerAgent, NoValidPathError

class ADNAOrchestrator:
    def __init__(self, graph_client: GraphClient):
        self.graph_client = graph_client
        self.reason_chain = ReasonChain()
        
        # Initialize all agents sharing the same reason chain
        self.curriculum_agent = CurriculumAgent(self.graph_client, self.reason_chain)
        self.market_agent = MarketTrendsAgent(self.graph_client, self.reason_chain)
        self.skill_gap_agent = SkillGapAgent(self.graph_client, self.reason_chain)
        self.career_agent = CareerSimulatorAgent(self.reason_chain)
        self.planner_agent = PlannerAgent(self.graph_client, self.reason_chain)

    def run_pipeline(self, 
                     curriculum_text: str, 
                     market_jobs: List[Dict[str, Any]], 
                     student: StudentProfile, 
                     role: JobRole,
                     mock_llm_override: str = None) -> Tuple[RoadmapPlan, List[ReasonStep]]:
        """
        Executes the full end-to-end ADNA pipeline.
        Enforces strict Pydantic schema validation at each boundary.
        """
        
        # 1. Curriculum Agent (Ingestion Phase)
        parse_result = self.curriculum_agent.parse_curriculum_text(curriculum_text)
        courses = parse_result.get("courses", [])
        
        # Validate output schema strictly
        validated_courses = []
        for c in courses:
            validated_course = Course.model_validate(c.model_dump())
            validated_courses.append(validated_course)
            
        self.curriculum_agent.ingest_curriculum(validated_courses)
        
        # 2. Market Trends Agent (Ingestion Phase)
        demand_scores = self.market_agent.compute_demand_scores(market_jobs)
        # Type check basic dict
        if not isinstance(demand_scores, dict):
            raise TypeError(f"MarketTrendsAgent must return dict, got {type(demand_scores)}")
        self.market_agent.update_graph_scores(demand_scores)
        
        # 3. Skill Gap Agent (Student Phase)
        gap_report_raw = self.skill_gap_agent.compute_gap_report(student, role)
        # Validate output schema strictly
        gap_report = GapReport.model_validate(gap_report_raw.model_dump())
        
        # 4. Career Simulator Agent (Student Phase)
        sim_result_raw = self.career_agent.simulate_career(student, role, gap_report, mock_llm_override=mock_llm_override)
        # Validate output schema strictly
        sim_result = CareerSimulationResult.model_validate(sim_result_raw.model_dump())
        
        # 5. Planner Agent (Student Phase)
        roadmap_raw = self.planner_agent.generate_roadmap(student, role, gap_report, sim_result)
        # Validate output schema strictly
        roadmap = RoadmapPlan.model_validate(roadmap_raw.model_dump())
        
        # Return fully aggregated and trace-linked result
        return roadmap, self.reason_chain.get_trace()
