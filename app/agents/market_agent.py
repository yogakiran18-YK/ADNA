import json
import logging
import math
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.models.schemas import JobPostingDTO, SkillDemandItem, MarketTrendsResponse
from app.models.domain import compute_recency_decay
from app.database.sqlite_db import get_sqlite_connection
from app.database.chroma_db import vector_store

logger = logging.getLogger(__name__)

# Curated Taxonomy of Industry Skills for CSE / AI & ML
SKILL_TAXONOMY = {
    "skill_pytorch": {"name": "PyTorch", "category": "AI/ML", "keywords": ["pytorch", "torch", "deep learning"]},
    "skill_tensorflow": {"name": "TensorFlow", "category": "AI/ML", "keywords": ["tensorflow", "keras"]},
    "skill_python": {"name": "Python", "category": "Programming", "keywords": ["python", "py"]},
    "skill_sql": {"name": "SQL & Relational DBs", "category": "Databases", "keywords": ["sql", "postgresql", "mysql", "sqlite"]},
    "skill_docker": {"name": "Docker & Containers", "category": "Cloud/DevOps", "keywords": ["docker", "container", "kubernetes"]},
    "skill_aws": {"name": "AWS Cloud Services", "category": "Cloud/DevOps", "keywords": ["aws", "amazon web services", "cloud", "s3", "ec2"]},
    "skill_fastapi": {"name": "FastAPI & REST APIs", "category": "Backend", "keywords": ["fastapi", "rest api", "backend", "express"]},
    "skill_dsa": {"name": "Data Structures & Algorithms", "category": "Core CS", "keywords": ["data structures", "algorithms", "dsa", "leetcode"]},
    "skill_nlp": {"name": "Natural Language Processing", "category": "AI/ML", "keywords": ["nlp", "natural language processing", "spacy", "bert", "transformers", "llm"]},
    "skill_mlops": {"name": "MLOps & Model Deployment", "category": "AI/ML", "keywords": ["mlops", "model deployment", "mlflow", "triton"]}
}

class MarketTrendsAgent:
    """
    Market Trends Agent:
    Ingests job listings, extracts skill keywords via curated taxonomy + NLP,
    calculates weighted skill demand using an exponential recency decay formula,
    and syncs skill embeddings with ChromaDB.
    """

    def extract_skills_from_text(self, text: str) -> List[str]:
        """Matches text content against curated taxonomy keywords."""
        text_lower = text.lower()
        extracted = []
        for skill_id, info in SKILL_TAXONOMY.items():
            for kw in info["keywords"]:
                if kw in text_lower:
                    extracted.append(skill_id)
                    break
        return extracted

    def process_job_postings(self, postings: List[JobPostingDTO] = None, current_date_str: str = "2026-08-03") -> MarketTrendsResponse:
        """
        Calculates demand score D(s) per skill:
        D(s) = sum_p [ I(s in p) * e^(-lambda * delta_t_p) ] / MaxDemand
        """
        if not postings:
            from app.api.v1.market import DEFAULT_SEED_POSTINGS
            postings = DEFAULT_SEED_POSTINGS

        curr_dt = datetime.strptime(current_date_str, "%Y-%m-%d")

        conn = get_sqlite_connection()
        cursor = conn.cursor()

        skill_decay_weights: Dict[str, float] = {s_id: 0.0 for s_id in SKILL_TAXONOMY.keys()}
        skill_frequencies: Dict[str, int] = {s_id: 0 for s_id in SKILL_TAXONOMY.keys()}

        for post in postings:
            # Save raw posting to SQLite
            cursor.execute("""
            INSERT OR REPLACE INTO market_postings (posting_id, title, company, posting_date, extracted_skills_json)
            VALUES (?, ?, ?, ?, ?)
            """, (post.posting_id, post.title, post.company, post.posting_date, json.dumps(post.extracted_skills)))

            # Calculate days since posting
            try:
                p_dt = datetime.strptime(post.posting_date, "%Y-%m-%d")
                delta_days = max(0, (curr_dt - p_dt).days)
            except Exception:
                delta_days = 0

            recency_weight = compute_recency_decay(delta_days, decay_lambda=settings.RECENCY_DECAY_LAMBDA)

            # Combine explicit skills and extracted text skills
            skills_in_post = set(post.extracted_skills)
            extracted_additional = self.extract_skills_from_text(post.title + " " + post.company)
            skills_in_post.update(extracted_additional)

            for s_id in skills_in_post:
                if s_id in skill_decay_weights:
                    skill_decay_weights[s_id] += recency_weight
                    skill_frequencies[s_id] += 1

        conn.commit()
        conn.close()

        # Normalize demand scores to [0, 1]
        max_decay_score = max(skill_decay_weights.values()) if skill_decay_weights.values() else 1.0
        if max_decay_score == 0:
            max_decay_score = 1.0

        top_skills: List[SkillDemandItem] = []
        for s_id, info in SKILL_TAXONOMY.items():
            decay_score = skill_decay_weights[s_id]
            norm_demand = round(decay_score / max_decay_score, 4)
            recency_avg = round(decay_score / max(1, skill_frequencies[s_id]), 4) if skill_frequencies[s_id] > 0 else 0.0

            item = SkillDemandItem(
                skill_id=s_id,
                skill_name=info["name"],
                category=info["category"],
                raw_frequency=skill_frequencies[s_id],
                recency_decay_score=recency_avg,
                demand_score=norm_demand
            )
            top_skills.append(item)

            # Sync with ChromaDB vector store
            doc_text = f"{info['name']} in {info['category']}. Keywords: {', '.join(info['keywords'])}"
            vector_store.add_skill(
                skill_id=s_id,
                text=doc_text,
                metadata={
                    "skill_name": info["name"],
                    "category": info["category"],
                    "demand_score": norm_demand,
                    "raw_frequency": skill_frequencies[s_id]
                }
            )

        top_skills.sort(key=lambda x: x.demand_score, reverse=True)

        return MarketTrendsResponse(
            total_postings_analyzed=len(postings),
            top_skills=top_skills
        )

market_agent = MarketTrendsAgent()
