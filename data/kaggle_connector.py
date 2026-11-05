"""
ADNA Kaggle Dataset Connector & Pipeline Ingestion Engine
Connects downloaded Kaggle datasets (Job Postings, Coursera Courses, OULAD, Placement, Resumes)
directly into ADNA databases (SQLite, ChromaDB vector store, and agent pipelines).
"""

import os
import sys
import json
import logging
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.models.schemas import JobPostingDTO, MarketTrendsResponse
from app.agents.market_agent import market_agent, SKILL_TAXONOMY
from app.database.sqlite_db import get_sqlite_connection
from app.database.chroma_db import vector_store

logger = logging.getLogger("adna.kaggle_connector")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

RAW_DATA_DIR = os.path.join(BASE_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "processed")


def check_dataset_status() -> Dict[str, Any]:
    """Scans all downloaded raw datasets and returns status and metadata."""
    datasets = {
        "market_jobs": {
            "path": os.path.join(RAW_DATA_DIR, "market_trends_agent", "job_postings", "job_postings.csv"),
            "skills_path": os.path.join(RAW_DATA_DIR, "market_trends_agent", "job_postings", "job_skills.csv"),
            "agent": "Market Trends Agent",
            "source": "Kaggle: asaniczka/data-science-job-postings-and-skills"
        },
        "coursera_courses": {
            "path": os.path.join(RAW_DATA_DIR, "curriculum_agent", "coursera", "Coursera.csv"),
            "agent": "Curriculum Agent",
            "source": "Kaggle: khusheekapoor/coursera-courses-dataset-2021"
        },
        "mit_ocw": {
            "path": os.path.join(RAW_DATA_DIR, "curriculum_agent", "mit_ocw", "mit_courses_2025-02-26_010109.csv"),
            "agent": "Curriculum Agent",
            "source": "Kaggle: jorgoose/mit-opencourseware-youtube-course-data"
        },
        "esco_skills": {
            "path": os.path.join(RAW_DATA_DIR, "market_trends_agent", "esco", "skills.csv"),
            "agent": "Market Trends Agent",
            "source": "Kaggle: thenoob69/esco-skills"
        },
        "oulad_students": {
            "path": os.path.join(RAW_DATA_DIR, "student_profiling_agent", "oulad", "studentInfo.csv"),
            "agent": "Student Profiling Agent",
            "source": "Kaggle: anlgrbz/student-demographics-online-education-dataoulad"
        },
        "campus_placement": {
            "path": os.path.join(RAW_DATA_DIR, "career_simulator_agent", "placement", "Placement_Data_Full_Class.csv"),
            "agent": "Career Simulator Agent",
            "source": "Kaggle: benroshan/factors-affecting-campus-placement"
        },
        "resume_dataset": {
            "path": os.path.join(RAW_DATA_DIR, "career_simulator_agent", "resume_dataset", "UpdatedResumeDataSet.csv"),
            "agent": "Career Simulator Agent",
            "source": "Kaggle: jillanisofttech/updated-resume-dataset"
        }
    }

    report = {}
    suitability_notes = {
        "market_jobs": "Suitable & active. 12,218 postings supply live skill frequency, posting dates, and recency decay signals.",
        "coursera_courses": "Reference catalog only. Lacks prerequisite graph and university credit structures.",
        "mit_ocw": "Unsuitable for planning. Video lecture titles without degree prerequisite chains or credits.",
        "esco_skills": "Taxonomy reference only. Standardizes skill taxonomy but does not provide posting demand counts.",
        "oulad_students": "Unsuitable for career fit. Online VLE modular retention data (2013-2014) lacking CS curriculum or career outcomes.",
        "campus_placement": "Unsuitable for ML training. 215 MBA placement rows without engineering coursework or technical skills.",
        "resume_dataset": "Unsuitable for ML predictive model. 42,104 category text records without verified career outcome labels or student transcripts."
    }
    for key, info in datasets.items():
        exists = os.path.exists(info["path"])
        file_size_mb = round(os.path.getsize(info["path"]) / (1024 * 1024), 2) if exists else 0.0
        row_count = 0
        if exists:
            try:
                row_count = sum(1 for _ in open(info["path"], "r", encoding="utf-8", errors="ignore")) - 1
            except Exception:
                row_count = -1

        report[key] = {
            "connected": exists,
            "agent": info["agent"],
            "source": info["source"],
            "file_path": info["path"],
            "size_mb": file_size_mb,
            "total_records": max(0, row_count),
            "suitability_assessment": suitability_notes.get(key, "Evaluation pending"),
            "is_integrated_in_recommendations": (key == "market_jobs")
        }
    return report


def load_kaggle_market_postings(limit: int = 250) -> Tuple[List[JobPostingDTO], Dict[str, Any]]:
    """
    Connects to the Kaggle Data Science Job Postings dataset, joins postings with skills,
    maps skills into ADNA taxonomy and JobPostingDTO schema.
    Returns bounded postings and deterministic audit report (read, accepted, rejected, reasons).
    """
    postings_path = os.path.join(RAW_DATA_DIR, "market_trends_agent", "job_postings", "job_postings.csv")
    skills_path = os.path.join(RAW_DATA_DIR, "market_trends_agent", "job_postings", "job_skills.csv")

    if not os.path.exists(postings_path) or not os.path.exists(skills_path):
        raise FileNotFoundError(f"Kaggle market dataset not found in {postings_path}")

    # Bounded read: read up to max(limit * 3, 100) to keep memory bounded and deterministic
    read_limit = max(100, min(limit * 3, 3000))
    logger.info(f"Loading Kaggle market dataset from {postings_path} (bounded read up to {read_limit} rows)...")
    df_postings = pd.read_csv(postings_path, nrows=read_limit)
    df_skills = pd.read_csv(skills_path, nrows=read_limit)

    merged = pd.merge(df_postings, df_skills, on="job_link", how="inner")
    logger.info(f"Merged {len(merged)} candidate postings with extracted skills.")

    records_read = len(merged)
    records_accepted = 0
    records_rejected = 0
    rejection_reasons: Dict[str, int] = {
        "missing_title": 0,
        "duplicate_id": 0,
        "empty_skills": 0,
        "limit_reached": 0
    }

    skill_keyword_map = {}
    for skill_id, info in SKILL_TAXONOMY.items():
        for kw in info["keywords"]:
            skill_keyword_map[kw.lower()] = skill_id

    postings: List[JobPostingDTO] = []
    seen_ids = set()

    for idx, row in merged.iterrows():
        if len(postings) >= limit:
            records_rejected += 1
            rejection_reasons["limit_reached"] += 1
            continue

        raw_title = str(row.get("job_title", "")).strip()
        if not raw_title or raw_title.lower() in ["nan", "null"]:
            records_rejected += 1
            rejection_reasons["missing_title"] += 1
            continue

        company = str(row.get("company", "Tech Enterprise")).strip()
        raw_skills_str = str(row.get("job_skills", ""))
        first_seen = str(row.get("first_seen", "2026-08-01"))

        # Clean and validate date format YYYY-MM-DD
        try:
            posting_date = first_seen[:10]
            datetime.strptime(posting_date, "%Y-%m-%d")
        except Exception:
            records_rejected += 1
            if "invalid_posting_date" not in rejection_reasons:
                rejection_reasons["invalid_posting_date"] = 0
            rejection_reasons["invalid_posting_date"] += 1
            continue

        # Map raw skills to taxonomy IDs
        extracted_skills = set()
        raw_skill_tokens = [s.strip().lower() for s in raw_skills_str.split(",") if s.strip()]
        for token in raw_skill_tokens:
            for kw, s_id in skill_keyword_map.items():
                if kw in token:
                    extracted_skills.add(s_id)

        # Keyword match on title
        title_lower = raw_title.lower()
        for kw, s_id in skill_keyword_map.items():
            if kw in title_lower:
                extracted_skills.add(s_id)

        if not extracted_skills:
            if any(term in title_lower for term in ["data", "learning", "ai", "ml", "engineer"]):
                extracted_skills.add("skill_python")
            else:
                records_rejected += 1
                rejection_reasons["empty_skills"] += 1
                continue

        post_id = f"kaggle_{idx:05d}"
        if post_id in seen_ids:
            records_rejected += 1
            rejection_reasons["duplicate_id"] += 1
            continue
        seen_ids.add(post_id)

        postings.append(JobPostingDTO(
            posting_id=post_id,
            title=raw_title,
            company=company,
            posting_date=posting_date,
            extracted_skills=list(extracted_skills)
        ))
        records_accepted += 1

    stats = {
        "records_read": records_read,
        "records_accepted": records_accepted,
        "records_rejected": records_rejected,
        "rejection_reasons": rejection_reasons
    }
    logger.info(f"Processed Kaggle postings: read={records_read}, accepted={records_accepted}, rejected={records_rejected}")
    return postings, stats


def ingest_kaggle_market_data(limit: int = 250, as_of: Optional[str] = None) -> MarketTrendsResponse:
    """
    Ingests Kaggle job postings into SQLite `market_postings` table, calculates
    recency-decayed skill demand scores, and updates ChromaDB embeddings.
    """
    postings, stats = load_kaggle_market_postings(limit=limit)
    response = market_agent.process_job_postings(postings, as_of=as_of)
    response.ingestion_summary = stats
    response.data_source = "kaggle_dataset"
    response.is_sample_data = False
    logger.info(f"Ingested {response.total_postings_analyzed} Kaggle postings. Top skills scored: {len(response.top_skills)}")
    return response


def convert_coursera_to_curriculum(limit: int = 50) -> str:
    """
    Converts Kaggle Coursera course catalog into ADNA curriculum format
    saved to data/processed/kaggle_curriculum.json.
    """
    coursera_path = os.path.join(RAW_DATA_DIR, "curriculum_agent", "coursera", "Coursera.csv")
    if not os.path.exists(coursera_path):
        raise FileNotFoundError(f"Coursera dataset not found in {coursera_path}")

    df = pd.read_csv(coursera_path, nrows=limit * 2)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

    courses = []
    code_counter = 101

    for _, row in df.iterrows():
        title = str(row.get("Course Name", "")).strip()
        university = str(row.get("University", "Online")).strip()
        difficulty = str(row.get("Difficulty Level", "Intermediate")).lower()
        rating = row.get("Course Rating", 4.5)
        raw_skills = str(row.get("Skills", ""))

        if not title:
            continue

        # Extract skills
        skills_list = [s.strip() for s in raw_skills.split() if len(s.strip()) > 2][:6]
        if not skills_list:
            skills_list = ["Computer Science", "Software Engineering"]

        # Assign semester based on difficulty
        if "beginner" in difficulty:
            semester = 1
            credits = 3
        elif "intermediate" in difficulty:
            semester = 3
            credits = 4
        else:
            semester = 5
            credits = 4

        code = f"CR-{code_counter}"
        code_counter += 1

        courses.append({
            "code": code,
            "title": f"{title} ({university})",
            "credits": credits,
            "semester": semester,
            "description": f"Offered by {university}. Rating: {rating}. Difficulty: {difficulty.capitalize()}.",
            "skills_provided": skills_list,
            "prerequisites": []
        })

        if len(courses) >= limit:
            break

    output_path = os.path.join(PROCESSED_DATA_DIR, "kaggle_curriculum.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2)

    logger.info(f"Converted {len(courses)} Coursera courses into {output_path}")
    return output_path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ADNA Kaggle Dataset Connector")
    parser.add_argument("--status", action="store_true", help="Print status of all Kaggle datasets")
    parser.add_argument("--ingest-market", action="store_true", help="Ingest Kaggle job postings into SQLite & ChromaDB")
    parser.add_argument("--limit", type=int, default=100, help="Number of records to process")
    parser.add_argument("--convert-curriculum", action="store_true", help="Convert Coursera dataset to ADNA curriculum")
    args = parser.parse_args()

    # Default action if no flags provided: report status and ingest market data
    if not (args.status or args.ingest_market or args.convert_curriculum):
        args.status = True
        args.ingest_market = True
        args.convert_curriculum = True

    if args.status:
        print("\n================ ADNA KAGGLE DATASET STATUS ================")
        status = check_dataset_status()
        for k, v in status.items():
            icon = "[OK]" if v["connected"] else "[MISSING]"
            print(f"{icon} [{v['agent']}] {k}: {v['total_records']} rows ({v['size_mb']} MB) -> {v['source']}")
        print("============================================================\n")

    if args.convert_curriculum:
        print("\n--- Converting Coursera to ADNA Curriculum Format ---")
        curr_file = convert_coursera_to_curriculum(limit=args.limit)
        print(f"Curriculum JSON saved to: {curr_file}")

    if args.ingest_market:
        print(f"\n--- Ingesting {args.limit} Kaggle Market Postings into SQLite & ChromaDB ---")
        res = ingest_kaggle_market_data(limit=args.limit)
        print(f"Analysis complete: {res.total_postings_analyzed} postings ingested.")
        print("Top Skills by Market Demand Score:")
        for item in res.top_skills[:10]:
            print(f"  • {item.skill_name} ({item.category}): Demand={item.demand_score:.4f}, Raw Frequency={item.raw_frequency}")


if __name__ == "__main__":
    main()
