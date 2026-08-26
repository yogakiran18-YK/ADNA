import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from app.models.schemas import StudentProfileCreate, StudentProfileResponse, CourseGradeRecord
from app.database.sqlite_db import get_sqlite_connection
from app.database.chroma_db import vector_store

logger = logging.getLogger(__name__)

GRADE_POINT_MAP = {
    "S": 10.0, "A": 9.0, "B": 8.0, "C": 7.0, "D": 6.0, "E": 5.0, "F": 0.0,
    "10": 10.0, "9": 9.0, "8": 8.0, "7": 7.0, "6": 6.0, "5": 5.0, "0": 0.0
}

class StudentProfilingAgent:
    """
    Student Profiling Agent:
    Tracks student academic records, grades, and self-reported interests in SQLite,
    and computes a dynamic 384-dimensional student profile embedding vector (E_u)
    synthesizing target career goals, completed course mastery, and interest tags.
    """

    def create_or_update_profile(self, profile: StudentProfileCreate) -> StudentProfileResponse:
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        # Upsert student base info
        cursor.execute("""
        INSERT OR REPLACE INTO students (student_id, name, department, current_semester, target_role)
        VALUES (?, ?, ?, ?, ?)
        """, (profile.student_id, profile.name, profile.department, profile.current_semester, profile.target_role))

        # Clear & insert interests
        cursor.execute("DELETE FROM student_interests WHERE student_id = ?", (profile.student_id,))
        for interest in profile.interests:
            cursor.execute("""
            INSERT INTO student_interests (student_id, interest_tag, weight)
            VALUES (?, ?, ?)
            """, (profile.student_id, interest, 1.0))

        # Upsert completed courses
        total_credits = 0
        total_weighted_points = 0.0

        cursor.execute("DELETE FROM student_courses WHERE student_id = ?", (profile.student_id,))
        for course_rec in profile.completed_courses:
            gp = course_rec.grade_point
            if gp == 0.0 and course_rec.grade in GRADE_POINT_MAP:
                gp = GRADE_POINT_MAP[course_rec.grade]
            
            cursor.execute("""
            INSERT INTO student_courses (student_id, course_code, semester_taken, grade, grade_point)
            VALUES (?, ?, ?, ?, ?)
            """, (profile.student_id, course_rec.course_code, course_rec.semester_taken, course_rec.grade, gp))

            total_credits += 4 # Standard course credit assumption
            total_weighted_points += (gp * 4)

        conn.commit()
        conn.close()

        gpa = round(total_weighted_points / max(1, total_credits), 2) if total_credits > 0 else 0.0

        return StudentProfileResponse(
            student_id=profile.student_id,
            name=profile.name,
            department=profile.department,
            current_semester=profile.current_semester,
            target_role=profile.target_role,
            interests=profile.interests,
            total_credits_earned=total_credits,
            gpa=gpa,
            profile_vector_dim=384
        )

    def get_profile(self, student_id: str) -> Optional[StudentProfileResponse]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        s_row = cursor.fetchone()
        if not s_row:
            conn.close()
            return None

        cursor.execute("SELECT interest_tag FROM student_interests WHERE student_id = ?", (student_id,))
        interests = [row["interest_tag"] for row in cursor.fetchall()]

        cursor.execute("SELECT * FROM student_courses WHERE student_id = ?", (student_id,))
        c_rows = cursor.fetchall()

        total_credits = len(c_rows) * 4
        total_points = sum(r["grade_point"] * 4 for r in c_rows)
        gpa = round(total_points / max(1, total_credits), 2) if total_credits > 0 else 0.0

        conn.close()

        return StudentProfileResponse(
            student_id=s_row["student_id"],
            name=s_row["name"],
            department=s_row["department"],
            current_semester=s_row["current_semester"],
            target_role=s_row["target_role"],
            interests=interests,
            total_credits_earned=total_credits,
            gpa=gpa,
            profile_vector_dim=384
        )

    def get_student_profile_vector(self, student_id: str) -> List[float]:
        """
        Generates 384-dimensional vector E_u combining:
        - Target role embedding (alpha = 0.5)
        - Completed course embeddings weighted by grade mastery (beta = 0.3)
        - Self-reported interest embeddings (gamma = 0.2)
        """
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT target_role FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        target_role = row["target_role"] if row else "Software Engineer"

        cursor.execute("SELECT interest_tag FROM student_interests WHERE student_id = ?", (student_id,))
        interests = [r["interest_tag"] for r in cursor.fetchall()]

        cursor.execute("SELECT course_code, grade_point FROM student_courses WHERE student_id = ?", (student_id,))
        courses = cursor.fetchall()
        conn.close()

        # Vector 1: Target Role
        v_role = np.array(vector_store.get_embedding(f"Target Career Role: {target_role}"))

        # Vector 2: Completed Courses (grade weighted)
        v_courses = np.zeros(384)
        if courses:
            for c in courses:
                c_vec = np.array(vector_store.get_embedding(f"Course {c['course_code']}"))
                weight = c["grade_point"] / 10.0
                v_courses += (c_vec * weight)
            v_courses /= max(1, len(courses))

        # Vector 3: Interests
        v_interests = np.zeros(384)
        if interests:
            for interest in interests:
                i_vec = np.array(vector_store.get_embedding(f"Interest in {interest}"))
                v_interests += i_vec
            v_interests /= len(interests)

        # Composite weighted vector synthesis
        E_u = (0.5 * v_role) + (0.3 * v_courses) + (0.2 * v_interests)
        norm = np.linalg.norm(E_u) + 1e-9
        return (E_u / norm).tolist()

profiling_agent = StudentProfilingAgent()
