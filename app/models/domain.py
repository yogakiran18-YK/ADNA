import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class CourseNode:
    code: str
    name: str
    credits: int
    semester: int
    category: str
    prerequisites: List[str] = field(default_factory=list)
    imparts_skills: Dict[str, float] = field(default_factory=dict) # skill_id -> weight

@dataclass
class SkillNode:
    id: str
    name: str
    category: str

def compute_recency_decay(days_ago: float, decay_lambda: float = 0.05) -> float:
    """
    R(s) = e^(-lambda * delta_t)
    Exponential recency decay for job posting signals.
    """
    return math.exp(-decay_lambda * max(0.0, days_ago))

def compute_skill_gap_score(
    market_demand: float,
    recency_decay: float,
    semantic_similarity: float,
    course_mastery: float,
    w1: float = 0.6,
    w2: float = 0.4
) -> float:
    """
    Skill Gap Score Formula G(s, u):
    G(s, u) = [w1 * D(s) + w2 * R(s)] * [1 - S_sim(E_u, E_s)] * [1 - C_mastery(u, s)]
    """
    market_weight = (w1 * market_demand) + (w2 * recency_decay)
    unmatched_similarity = 1.0 - max(-1.0, min(1.0, semantic_similarity))
    unmatched_mastery = 1.0 - max(0.0, min(1.0, course_mastery))
    
    gap_score = market_weight * unmatched_similarity * unmatched_mastery
    return round(gap_score, 4)

def compute_planner_objective(
    gap_closure: float,
    market_alignment: float,
    feasibility_score: float,
    workload_penalty: float,
    wg: float = 0.40,
    wm: float = 0.30,
    wp: float = 0.20,
    ww: float = 0.10
) -> float:
    """
    Planner Objective Function J(X):
    J(X) = wg * GapClosure(X) + wm * MarketAlignment(X) + wp * FeasibilityScore(X) - ww * WorkloadPenalty(X)
    """
    j_score = (wg * gap_closure) + (wm * market_alignment) + (wp * feasibility_score) - (ww * workload_penalty)
    return round(j_score, 4)
