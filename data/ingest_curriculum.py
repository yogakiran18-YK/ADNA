import os
import sys
import json
import logging
from pydantic import ValidationError

# Ensure the root of the project is in the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.schemas import Course
from core.graph_client import GraphClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_and_validate_curriculum(file_path: str):
    """Loads and validates a curriculum JSON file"""
    validated_courses = []
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        for idx, item in enumerate(data):
            try:
                course = Course(**item)
                validated_courses.append(course)
            except ValidationError as e:
                logger.error(f"Validation error for item at index {idx}: {e}")
                raise e
                
        return validated_courses
    except Exception as e:
        logger.error(f"Failed to load curriculum file {file_path}: {e}")
        raise e

def ingest_course(client: GraphClient, course: Course):
    """Ingests a single course, its skills, and its prerequisites into the graph"""
    
    # 1. Merge the Course Node
    course_query = """
    MERGE (c:Course {code: $code})
    SET c.title = $title,
        c.credits = $credits,
        c.semester = $semester,
        c.description = $description
    """
    client.execute_write(course_query, {
        "code": course.code,
        "title": course.title,
        "credits": course.credits,
        "semester": course.semester,
        "description": course.description or ""
    })
    
    # 2. Merge Skills and create TEACHES relationship
    for skill_name in course.skills_provided:
        skill_query = """
        MATCH (c:Course {code: $code})
        MERGE (s:Skill {name: $skill_name})
        MERGE (c)-[:TEACHES]->(s)
        """
        client.execute_write(skill_query, {
            "code": course.code,
            "skill_name": skill_name
        })
        
    # 3. Merge Prerequisites and create PREREQUISITE_OF relationship
    for prereq in course.prerequisites:
        # We ensure the prerequisite course node exists (even with just the code)
        prereq_query = """
        MATCH (c:Course {code: $course_code})
        MERGE (p:Course {code: $prereq_code})
        MERGE (p)-[r:PREREQUISITE_OF {type: $prereq_type}]->(c)
        """
        client.execute_write(prereq_query, {
            "course_code": course.code,
            "prereq_code": prereq.code,
            "prereq_type": prereq.type
        })

def main():
    curriculum_file = os.path.join(os.path.dirname(__file__), 'sample_curriculum.json')
    schema_file = os.path.join(os.path.dirname(__file__), 'graph_schema.cypher')
    
    logger.info("Loading and validating curriculum...")
    courses = load_and_validate_curriculum(curriculum_file)
    logger.info(f"Successfully validated {len(courses)} courses.")
    
    # Normally these would be environment variables
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    client = GraphClient(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        # Run schema migration (indexes and constraints)
        logger.info("Running schema migration...")
        client.run_cypher_script(schema_file)
        
        # Ingest courses
        logger.info("Ingesting courses into Neo4j...")
        for course in courses:
            ingest_course(client, course)
            logger.info(f"Ingested course: {course.code}")
            
        logger.info("Ingestion completed successfully.")
        
    except Exception as e:
        logger.error(f"An error occurred during ingestion: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
