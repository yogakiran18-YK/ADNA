import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from app.config import settings

def get_sqlite_connection():
    db_path = settings.SQLITE_DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_sqlite_db():
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # Students table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        current_semester INTEGER NOT NULL,
        target_role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Student completed/taken courses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        course_code TEXT NOT NULL,
        semester_taken INTEGER NOT NULL,
        grade TEXT NOT NULL,
        grade_point REAL NOT NULL,
        status TEXT DEFAULT 'COMPLETED',
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
    """)

    # Student interests table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_interests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        interest_tag TEXT NOT NULL,
        weight REAL DEFAULT 1.0,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
    """)

    # Market postings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_postings (
        posting_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        posting_date TEXT NOT NULL,
        extracted_skills_json TEXT NOT NULL
    )
    """)

    # Roadmaps table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roadmaps (
        roadmap_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        version INTEGER NOT NULL,
        semester_plans_json TEXT NOT NULL,
        objective_score REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
    """)

    # Roadmap reason chains table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roadmap_reasons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roadmap_id TEXT NOT NULL,
        course_code TEXT NOT NULL,
        target_skill_id TEXT NOT NULL,
        market_signal_demand REAL NOT NULL,
        graph_prereq_path_json TEXT NOT NULL,
        rationale_json TEXT NOT NULL,
        FOREIGN KEY(roadmap_id) REFERENCES roadmaps(roadmap_id)
    )
    """)

    # Career simulations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS career_simulations (
        sim_id TEXT PRIMARY KEY,
        student_id TEXT NOT NULL,
        trajectory_title TEXT NOT NULL,
        llm_reasoning TEXT NOT NULL,
        ml_fit_score REAL NOT NULL,
        composite_score REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_sqlite_db()
    print("SQLite database initialized successfully.")
