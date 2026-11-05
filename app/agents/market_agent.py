import json
import logging
import math
from datetime import datetime, date, timezone
from typing import List, Dict, Any, Tuple, Optional
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

    def process_job_postings(
        self,
        postings: Optional[List[JobPostingDTO]] = None,
        current_date_str: Optional[str] = None,
        as_of: Optional[str] = None
    ) -> MarketTrendsResponse:
        """
        Calculates demand score D(s) per skill with exponential recency decay:
        D(s) = sum_p [ I(s in p) * e^(-lambda * delta_t_p) ] / MaxDemand
        where delta_t_p = max(0, (as_of - posting_date).days)
        and lambda = settings.RECENCY_DECAY_LAMBDA (default 0.05).
        Default as_of date policy: UTC date (datetime.now(timezone.utc)).
        Explicit as_of and posting dates are strictly validated.
        """
        is_sample_data = False
        raw_as_of = as_of or current_date_str
        if raw_as_of is not None:
            clean_date = raw_as_of.strip()[:10]
            try:
                curr_dt = datetime.strptime(clean_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                ref_date_str = clean_date
            except Exception as e:
                raise ValueError(f"Invalid as_of date '{raw_as_of}'. Expected format YYYY-MM-DD.") from e
        else:
            curr_dt = datetime.now(timezone.utc)
            ref_date_str = curr_dt.strftime("%Y-%m-%d")

        if postings is None:
            # Check SQLite for real ingested postings first
            conn = get_sqlite_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT posting_id, title, company, posting_date, extracted_skills_json FROM market_postings")
            rows = cursor.fetchall()
            conn.close()

            if rows:
                postings = []
                for r in rows:
                    try:
                        skills = json.loads(r["extracted_skills_json"])
                    except Exception:
                        skills = []
                    postings.append(JobPostingDTO(
                        posting_id=r["posting_id"],
                        title=r["title"],
                        company=r["company"],
                        posting_date=r["posting_date"],
                        extracted_skills=skills
                    ))
                is_sample_data = False
            else:
                from app.api.v1.market import DEFAULT_SEED_POSTINGS
                postings = DEFAULT_SEED_POSTINGS
                is_sample_data = True
        elif len(postings) > 0 and all(p.posting_id.startswith("job_") for p in postings):
            # Known default seed prefix
            is_sample_data = True

        # Handle empty postings gracefully
        if len(postings) == 0:
            top_skills = [
                SkillDemandItem(
                    skill_id=s_id,
                    skill_name=info["name"],
                    category=info["category"],
                    raw_frequency=0,
                    recency_decay_score=0.0,
                    demand_score=0.0
                )
                for s_id, info in SKILL_TAXONOMY.items()
            ]
            return MarketTrendsResponse(
                total_postings_analyzed=0,
                top_skills=top_skills,
                as_of=ref_date_str,
                is_sample_data=is_sample_data,
                data_source="empty"
            )

        conn = get_sqlite_connection()
        try:
            cursor = conn.cursor()

            skill_decay_weights: Dict[str, float] = {s_id: 0.0 for s_id in SKILL_TAXONOMY.keys()}
            skill_frequencies: Dict[str, int] = {s_id: 0 for s_id in SKILL_TAXONOMY.keys()}

            rejected_invalid_dates = 0
            accepted_postings_count = 0

            for post in postings:
                # Validate posting date strictly
                try:
                    p_dt = datetime.strptime(post.posting_date.strip()[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                except Exception:
                    rejected_invalid_dates += 1
                    logger.warning(f"Rejecting posting {post.posting_id}: invalid posting date '{post.posting_date}'")
                    continue

                # Save valid posting to SQLite
                cursor.execute("""
                INSERT OR REPLACE INTO market_postings (posting_id, title, company, posting_date, extracted_skills_json)
                VALUES (?, ?, ?, ?, ?)
                """, (post.posting_id, post.title, post.company, post.posting_date, json.dumps(post.extracted_skills)))
                accepted_postings_count += 1

                # Deliberate past vs future posting handling:
                # If posting is in the past, delta_days >= 0 and recency decays exponentially.
                # If posting is dated in the future relative to as_of, delta_days is clamped to 0 (decay weight 1.0, strictly bounded in [0, 1]).
                delta_days = max(0, (curr_dt - p_dt).days)
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
        finally:
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
            total_postings_analyzed=accepted_postings_count,
            top_skills=top_skills,
            as_of=ref_date_str,
            is_sample_data=is_sample_data,
            data_source="sample_seed" if is_sample_data else "ingested_sqlite",
            ingestion_summary={"rejected_invalid_dates": rejected_invalid_dates} if rejected_invalid_dates > 0 else None
        )

    def get_current_demand_scores(self, as_of: Optional[str] = None) -> MarketTrendsResponse:
        """
        Reads existing ingested market postings from SQLite and computes demand scores.
        Only falls back to seed postings if SQLite contains no postings.
        """
        return self.process_job_postings(postings=None, as_of=as_of)

    # Backward-compatible alias
    calculate_recency_decay = process_job_postings

market_agent = MarketTrendsAgent()
