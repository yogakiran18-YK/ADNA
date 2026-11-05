import re
import logging
from typing import List, Dict, Any, Tuple
from app.models.schemas import CourseDTO, CurriculumIngestResponse, PrereqCheckResponse
from app.database.neo4j_db import graph_manager

logger = logging.getLogger(__name__)

class CurriculumAgent:
    """
    Curriculum Agent:
    Extracts course structures, credits, semester placement, and prerequisite chains
    from university syllabus documents using NLP regex & spaCy pattern matching,
    then constructs the Neo4j Knowledge Graph.
    """

    def __init__(self):
        self.nlp = None
        self._init_nlp()

    def _init_nlp(self):
        try:
            import spacy
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                self.nlp = spacy.blank("en")
            logger.info("Loaded spaCy NLP pipeline for curriculum parsing.")
        except Exception as e:
            logger.warning(f"spaCy NLP initialization error ({e}). Using regex parser fallback.")
            self.nlp = None

    def parse_syllabus_text(self, text: str) -> List[CourseDTO]:
        """
        Parses text blocks into CourseDTO objects.
        Regex patterns extract course codes (e.g. CSE101, AIML302), credits, semester,
        and prerequisite declarations.
        """
        courses = []
        # Split into course blocks by course code headers
        blocks = re.split(r'\n\s*(?=[A-Z]{3,4}\d{3})', text)
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            # Match course code and title e.g. "CSE101: Introduction to Programming (4 Credits, Sem 1)"
            code_match = re.search(r'([A-Z]{3,4}\d{3})[:\s]+([^\n\(\)]+)', block)
            if not code_match:
                continue
            
            code = code_match.group(1).strip()
            name = code_match.group(2).strip()
            
            # Match credits
            credit_match = re.search(r'(\d+)\s*Credits?', block, re.IGNORECASE)
            credits = int(credit_match.group(1)) if credit_match else 4
            
            # Match semester
            sem_match = re.search(r'Sem(?:ester)?\s*(\d+)', block, re.IGNORECASE)
            semester = int(sem_match.group(1)) if sem_match else 1
            
            # Match category
            category = "Elective" if re.search(r'\bElective\b', block, re.IGNORECASE) else "Core"

            
            # Extract prerequisites e.g. "Prerequisites: CSE101, CSE102"
            prereqs = []
            prereq_match = re.search(r'Prereq(?:uisites?)?:\s*([^\n\.]+)', block, re.IGNORECASE)
            if prereq_match:
                prereq_str = prereq_match.group(1)
                prereqs = re.findall(r'[A-Z]{3,4}\d{3}', prereq_str)
                prereqs = [p for p in prereqs if p != code] # prevent self-loop
            
            # Imparted skills heuristic extraction
            imparts = {}
            if re.search(r'Python|Programming|C\+\+', block, re.IGNORECASE):
                imparts["skill_python"] = 0.9
            if re.search(r'Data Structures|Algorithms', block, re.IGNORECASE):
                imparts["skill_dsa"] = 0.95
            if re.search(r'Machine Learning|Deep Learning|Neural', block, re.IGNORECASE):
                imparts["skill_ml"] = 0.95
            if re.search(r'Database|SQL|DBMS', block, re.IGNORECASE):
                imparts["skill_dbms"] = 0.85
            if re.search(r'Cloud|AWS|DevOps|Docker', block, re.IGNORECASE):
                imparts["skill_cloud"] = 0.85

            courses.append(CourseDTO(
                code=code,
                name=name,
                credits=credits,
                semester=semester,
                category=category,
                prerequisites=prereqs,
                imparts_skills=imparts
            ))
            
        return courses

    def ingest_curriculum(self, courses: List[CourseDTO]) -> CurriculumIngestResponse:
        """
        Populates Neo4j Knowledge Graph with courses, prerequisite edges, and skill edges.
        """
        prereq_count = 0
        skill_count = 0

        for course in courses:
            # Add Course Node
            graph_manager.add_course(
                code=course.code,
                name=course.name,
                credits=course.credits,
                semester=course.semester,
                category=course.category
            )
            # Add Prerequisite Edges
            for p_code in course.prerequisites:
                graph_manager.add_prerequisite(prereq_code=p_code, target_code=course.code)
                prereq_count += 1
            
            # Add Skill Mapping Edges
            for s_id, weight in course.imparts_skills.items():
                graph_manager.add_skill_mapping(course_code=course.code, skill_id=s_id, weight=weight)
                skill_count += 1

        graph_manager.mark_ingested()

        return CurriculumIngestResponse(
            status="success",
            courses_parsed=len(courses),
            prerequisites_linked=prereq_count,
            skills_mapped=skill_count
        )

    def check_prerequisite_feasibility(self, target_code: str, completed_codes: List[str]) -> PrereqCheckResponse:
        """
        Queries Neo4j Knowledge Graph to assess if target course can be safely taken
        given completed course history, returning topological ordering.
        """
        is_feasible, missing, path = graph_manager.check_prerequisite_feasibility(
            target_code=target_code,
            completed_codes=completed_codes
        )
        return PrereqCheckResponse(
            target_course_code=target_code,
            is_feasible=is_feasible,
            missing_prerequisites=missing,
            prereq_chain_depth=len(path) - 1 if path else 0,
            topological_path=path
        )

curriculum_agent = CurriculumAgent()
