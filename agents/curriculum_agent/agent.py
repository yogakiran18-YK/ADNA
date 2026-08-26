import os
import re
import spacy
from typing import List, Dict, Any, Tuple
from core.schemas import Course, Prerequisite
from core.reason_chain import ReasonChain
from core.graph_client import GraphClient

class CurriculumAgent:
    def __init__(self, graph_client: GraphClient, reason_chain: ReasonChain):
        self.graph_client = graph_client
        self.reason_chain = reason_chain
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if not installed, though it should be in the environment
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")

    def parse_curriculum_text(self, text: str) -> Dict[str, Any]:
        """
        Parses curriculum text into structured Courses.
        Returns a dictionary with 'courses' and 'ambiguous_extractions'.
        """
        courses = []
        ambiguous_extractions = []
        
        # Simple regex to split text into course blocks
        # Assumes format like "CS401 Title (X credits, Semester). Prerequisite: ..."
        course_pattern = re.compile(r'([A-Z]{2,4}\d{3,4})\s+(.*?)\((\d+)\s+credits?(?:,\s+([^)]+))?\)\.\s*(?:Prerequisite:\s*(.*?)\.)?(?=\s*[A-Z]{2,4}\d{3,4}|$)', re.IGNORECASE | re.DOTALL)
        
        matches = course_pattern.findall(text)
        
        for match in matches:
            code, title, credits_str, semester, prereq_text = match
            code = code.strip().upper()
            title = title.strip()
            credits = int(credits_str)
            semester = semester.strip() if semester else "Unknown"
            prereq_text = prereq_text.strip() if prereq_text else ""
            
            self.reason_chain.log_step(
                step_id=f"parse_{code}",
                agent_name="CurriculumAgent",
                input_summary=f"Extracted basic course info for {code}",
                decision=f"Parsed title '{title}', credits {credits}",
                justification="Regex pattern match on standard curriculum format",
                score_used=1.0
            )

            prerequisites = []
            
            if prereq_text:
                # Use spaCy to analyze the prerequisite phrase
                doc = self.nlp(prereq_text)
                
                # Look for strict course codes in the prerequisite text
                prereq_codes = re.findall(r'[A-Z]{2,4}\d{3,4}', prereq_text, re.IGNORECASE)
                
                if prereq_codes and len(prereq_codes[0]) > 0:
                    for p_code in prereq_codes:
                        p_code = p_code.upper()
                        prerequisites.append(Prerequisite(code=p_code, type="hard"))
                        
                    self.reason_chain.log_step(
                        step_id=f"resolve_prereq_{code}",
                        agent_name="CurriculumAgent",
                        input_summary=f"Prerequisite text: '{prereq_text}'",
                        decision=f"Resolved explicit prerequisite edges to {prereq_codes}",
                        justification="Found clear course codes in text",
                        score_used=0.95
                    )
                else:
                    # Ambiguous prerequisite extraction
                    ambiguous_extractions.append({
                        "course_code": code,
                        "raw_text": prereq_text,
                        "needs_review": True
                    })
                    self.reason_chain.log_step(
                        step_id=f"resolve_prereq_ambiguous_{code}",
                        agent_name="CurriculumAgent",
                        input_summary=f"Prerequisite text: '{prereq_text}'",
                        decision="Flagged prerequisite as ambiguous (needs_review=True)",
                        justification="No explicit course code found; text requires manual review to prevent unverified graph edges.",
                        score_used=0.3
                    )

            course = Course(
                code=code,
                title=title,
                credits=credits,
                semester=semester,
                description="",
                skills_provided=[],
                prerequisites=prerequisites
            )
            courses.append(course)

        return {
            "courses": courses,
            "ambiguous_extractions": ambiguous_extractions
        }

    def ingest_curriculum(self, courses: List[Course]) -> None:
        """
        Writes parsed courses into the Neo4j graph using GraphClient.
        """
        for course in courses:
            # 1. Merge Course
            self.graph_client.execute_write("""
                MERGE (c:Course {code: $code})
                SET c.title = $title,
                    c.credits = $credits,
                    c.semester = $semester,
                    c.description = $description
            """, {
                "code": course.code,
                "title": course.title,
                "credits": course.credits,
                "semester": course.semester,
                "description": course.description or ""
            })
            
            # 2. Merge explicit prerequisites
            for prereq in course.prerequisites:
                self.graph_client.execute_write("""
                    MATCH (c:Course {code: $course_code})
                    MERGE (p:Course {code: $prereq_code})
                    MERGE (p)-[r:PREREQUISITE_OF {type: $prereq_type}]->(c)
                """, {
                    "course_code": course.code,
                    "prereq_code": prereq.code,
                    "prereq_type": prereq.type
                })
                
            self.reason_chain.log_step(
                step_id=f"ingest_{course.code}",
                agent_name="CurriculumAgent",
                input_summary=f"Ingesting course {course.code} with {len(course.prerequisites)} prerequisites",
                decision="Merged course and prerequisite edges into graph",
                justification="Graph schema requires MERGE for idempotency",
                score_used=1.0
            )
