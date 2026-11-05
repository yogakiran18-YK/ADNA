import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from app.models.schemas import StudentProfileCreate, StudentProfileResponse, CourseGradeRecord
from app.database.sqlite_db import get_sqlite_connection
from app.database.chroma_db import vector_store

from app.database.neo4j_db import graph_manager

logger = logging.getLogger(__name__)

GRADE_POINT_MAP = {
    "S": 10.0, "A": 9.0, "B": 8.0, "C": 7.0, "D": 6.0, "E": 5.0, "F": 0.0,
    "10": 10.0, "9": 9.0, "8": 8.0, "7": 7.0, "6": 6.0, "5": 5.0, "0": 0.0
}

def resolve_course_credits(course_code: str, explicit_credits: Optional[int] = None) -> Tuple[int, bool]:
    """
    Resolves credit value for a course.
    Returns (credit_value, is_estimated).
    Uses explicit credits if provided, curriculum credits if in curriculum graph,
    or documented fallback (4) if course credit is unknown.
    """
    if explicit_credits is not None and explicit_credits > 0:
        return explicit_credits, False
    code = course_code.strip().upper()
    all_courses = graph_manager.get_all_courses()
    if code in all_courses:
        c_info = all_courses[code]
        if "credits" in c_info and c_info["credits"] is not None:
            return int(c_info["credits"]), False
    # Documented fallback default when curriculum credit is unknown
    return 4, True

class StudentProfilingAgent:
    """
    Student Profiling Agent:
    Tracks student academic records, grades, and self-reported interests in SQLite,
    and computes a dynamic 384-dimensional student profile embedding vector (E_u)
    synthesizing target career goals, completed course mastery, and interest tags.
    Handles known, missing, and estimated academic records honestly.
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

        # Upsert completed courses with curriculum credit resolution and honest GPA handling
        total_credits = 0
        total_graded_credits = 0
        total_graded_points = 0.0
        credits_estimated = False
        gpa_estimated = False
        estimated_fields: List[str] = []
        credits_breakdown: Dict[str, int] = {}
        processed_courses: List[CourseGradeRecord] = []

        cursor.execute("DELETE FROM student_courses WHERE student_id = ?", (profile.student_id,))
        for course_rec in profile.completed_courses:
            c_code = course_rec.course_code.strip().upper()
            c_credits, is_est_credits = resolve_course_credits(c_code, course_rec.credits)
            if is_est_credits:
                credits_estimated = True
                estimated_fields.append(f"credits:{c_code}")
            credits_breakdown[c_code] = c_credits
            total_credits += c_credits

            # Resolve grade and grade point
            g = course_rec.grade.strip().upper() if course_rec.grade else None
            gp = course_rec.grade_point
            if gp is None and g in GRADE_POINT_MAP:
                gp = GRADE_POINT_MAP[g]
            elif gp is not None and g is None:
                g = "S" if gp >= 10.0 else "A" if gp >= 9.0 else "B" if gp >= 8.0 else "C" if gp >= 7.0 else "D" if gp >= 6.0 else "E" if gp >= 5.0 else "F"

            is_grade_known = (gp is not None and gp >= 0.0)
            if is_grade_known:
                total_graded_credits += c_credits
                total_graded_points += (gp * c_credits)
            else:
                gpa_estimated = True
                estimated_fields.append(f"grade:{c_code}")

            db_grade = g if g is not None else "UNKNOWN"
            db_gp = gp if gp is not None else -1.0
            db_sem = course_rec.semester_taken if course_rec.semester_taken is not None else 0

            cursor.execute("""
            INSERT INTO student_courses (student_id, course_code, semester_taken, grade, grade_point)
            VALUES (?, ?, ?, ?, ?)
            """, (profile.student_id, c_code, db_sem, db_grade, db_gp))

            processed_courses.append(CourseGradeRecord(
                course_code=c_code,
                semester_taken=course_rec.semester_taken,
                grade=g,
                grade_point=gp,
                credits=c_credits,
                grade_estimated=(not is_grade_known),
                credits_estimated=is_est_credits
            ))

        conn.commit()
        conn.close()

        # GPA is calculated strictly from courses with known grades to avoid misleading totals
        gpa = round(total_graded_points / total_graded_credits, 2) if total_graded_credits > 0 else None

        return StudentProfileResponse(
            student_id=profile.student_id,
            name=profile.name,
            department=profile.department,
            current_semester=profile.current_semester,
            target_role=profile.target_role,
            interests=profile.interests,
            total_credits_earned=total_credits,
            gpa=gpa,
            profile_vector_dim=384,
            credits_estimated=credits_estimated,
            gpa_estimated=gpa_estimated,
            estimated_fields=estimated_fields,
            credits_breakdown=credits_breakdown,
            completed_courses=processed_courses
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

        total_credits = 0
        total_graded_credits = 0
        total_graded_points = 0.0
        credits_estimated = False
        gpa_estimated = False
        estimated_fields: List[str] = []
        credits_breakdown: Dict[str, int] = {}

        completed_course_records = []
        for r in c_rows:
            c_code = r["course_code"]
            c_credits, is_est = resolve_course_credits(c_code)
            if is_est:
                credits_estimated = True
                estimated_fields.append(f"credits:{c_code}")
            credits_breakdown[c_code] = c_credits
            total_credits += c_credits

            grade_val = r["grade"]
            gp_val = r["grade_point"]

            if grade_val in ("UNKNOWN", "", None) or gp_val < 0.0:
                g = None
                gp = None
                is_grade_known = False
                gpa_estimated = True
                estimated_fields.append(f"grade:{c_code}")
            else:
                g = grade_val
                gp = float(gp_val)
                is_grade_known = True
                total_graded_credits += c_credits
                total_graded_points += (gp * c_credits)

            sem_taken = r["semester_taken"] if r["semester_taken"] != 0 else None

            completed_course_records.append(CourseGradeRecord(
                course_code=c_code,
                semester_taken=sem_taken,
                grade=g,
                grade_point=gp,
                credits=c_credits,
                grade_estimated=(not is_grade_known),
                credits_estimated=is_est
            ))

        gpa = round(total_graded_points / total_graded_credits, 2) if total_graded_credits > 0 else None

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
            profile_vector_dim=384,
            credits_estimated=credits_estimated,
            gpa_estimated=gpa_estimated,
            estimated_fields=estimated_fields,
            credits_breakdown=credits_breakdown,
            completed_courses=completed_course_records
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
                gp = c["grade_point"]
                weight = (gp / 10.0) if gp >= 0.0 else 0.8
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
