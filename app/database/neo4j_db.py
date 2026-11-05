import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

class MockNeo4jGraph:
    """In-memory Graph storage mimicking Neo4j Cypher pathfinding & topological ordering."""
    def __init__(self):
        self.courses: Dict[str, Dict] = {} # code -> properties
        self.prereqs: Set[Tuple[str, str]] = set() # (prereq_code, course_code) i.e. prereq -> target
        self.skills: Set[Tuple[str, str, float]] = set() # (course_code, skill_id, weight)
        self._seed_default_curriculum()

    def _seed_default_curriculum(self):
        """Pre-seeds standard undergraduate CS curriculum courses with credits and prerequisites."""
        default_courses = [
            ("CS101", "Programming in C & Problem Solving", 4, 1, "Core", [], ["skill_python", "skill_dsa"]),
            ("MA101", "Engineering Mathematics I", 4, 1, "Core", [], ["skill_math"]),
            ("PH101", "Engineering Physics", 4, 1, "Core", [], ["skill_physics"]),
            ("EE101", "Basic Electrical & Electronics", 4, 1, "Core", [], ["skill_hardware"]),
            ("CS102", "Object-Oriented Programming with Python", 4, 2, "Core", ["CS101"], ["skill_python", "skill_dsa"]),
            ("MA102", "Engineering Mathematics II", 4, 2, "Core", ["MA101"], ["skill_math"]),
            ("CS103", "Digital Logic & Computer Organization", 4, 2, "Core", [], ["skill_hardware"]),
            ("CY101", "Engineering Chemistry", 4, 2, "Core", [], ["skill_chemistry"]),
            ("CS201", "Data Structures & Algorithms", 4, 3, "Core", ["CS102"], ["skill_dsa", "skill_python"]),
            ("CS202", "Discrete Mathematics & Graph Theory", 4, 3, "Core", ["MA101"], ["skill_math", "skill_dsa"]),
            ("CS203", "Computer Architecture & Assembly", 4, 3, "Core", ["CS103"], ["skill_hardware"]),
            ("CS204", "Software Engineering Principles", 4, 3, "Core", ["CS102"], ["skill_python", "skill_software"]),
            ("CS301", "Design & Analysis of Algorithms", 4, 4, "Core", ["CS201"], ["skill_dsa"]),
            ("CS302", "Operating Systems & System Programming", 4, 4, "Core", ["CS201"], ["skill_docker", "skill_systems"]),
            ("CS402", "Database Management Systems (SQL)", 4, 4, "Core", ["CS201"], ["skill_sql"]),
            ("MA201", "Applied Numerical Methods & Statistics", 4, 4, "Core", ["MA102"], ["skill_math", "skill_statistics"]),
            ("CS501", "Computer Networks & Internet Protocols", 4, 5, "Core", ["CS302"], ["skill_fastapi", "skill_networks"]),
            ("CS401", "Artificial Intelligence & Knowledge Representation", 4, 5, "Core", ["CS201"], ["skill_pytorch", "skill_nlp"]),
            ("CS502", "Theory of Computation & Automata", 4, 5, "Core", ["CS202"], ["skill_theory"]),
            ("CS503", "Web Technologies & Frontend Frameworks", 4, 5, "Elective", ["CS102"], ["skill_fastapi", "skill_web"]),
            ("CS601", "Machine Learning & Statistical Modeling", 4, 6, "Core", ["CS401"], ["skill_pytorch", "skill_tensorflow"]),
            ("CS602", "Compiler Design & Language Engineering", 4, 6, "Core", ["CS502"], ["skill_theory"]),
            ("CS603", "Cloud Computing & Containerization (Docker/AWS)", 4, 6, "Elective", ["CS302"], ["skill_docker", "skill_aws"]),
            ("CS604", "Information & Network Security", 4, 6, "Elective", ["CS501"], ["skill_security"]),
            ("CS701", "Deep Learning & Neural Networks (PyTorch)", 4, 7, "Elective", ["CS601"], ["skill_pytorch", "skill_tensorflow"]),
            ("CS702", "Distributed Systems & Microservices", 4, 7, "Elective", ["CS501"], ["skill_fastapi", "skill_docker"]),
            ("CS703", "Big Data Engineering & Stream Analytics", 4, 7, "Elective", ["CS402"], ["skill_sql", "skill_aws"]),
            ("CS704", "Natural Language Processing & Transformers", 4, 7, "Elective", ["CS601"], ["skill_nlp", "skill_pytorch"]),
            ("CS801", "Major Capstone Project", 4, 8, "Core", ["CS701"], ["skill_dsa", "skill_pytorch"]),
            ("CS802", "High Performance & GPU Computing", 4, 8, "Elective", ["CS701"], ["skill_pytorch"]),
            ("CS803", "MLOps & Model Lifecycle Engineering", 4, 8, "Elective", ["CS603"], ["skill_mlops", "skill_docker"]),
            # Elective catalogue aliases for backwards compatibility with tests
            ("CSE101", "Intro to Programming", 4, 1, "Core", [], ["skill_python"]),
            ("CSE201", "Data Structures", 4, 2, "Core", ["CSE101"], ["skill_dsa"]),
            ("CSE303", "Web Architecture & FastAPI", 4, 5, "Elective", ["CSE101"], ["skill_fastapi", "skill_python"]),
            ("CSE304", "Cloud Computing & Docker", 4, 5, "Elective", ["CSE101"], ["skill_docker", "skill_aws"]),
            ("AIML301", "Deep Learning & PyTorch", 4, 5, "Elective", ["CSE201"], ["skill_pytorch", "skill_nlp"]),
            ("AIML302", "Natural Language Processing", 4, 6, "Elective", ["AIML301"], ["skill_nlp"]),
            ("AIML401", "MLOps Engineering & Deployment", 4, 6, "Elective", ["AIML301"], ["skill_mlops", "skill_docker"]),
            ("CSE410", "Advanced DevOps & Kubernetes", 4, 6, "Elective", ["CSE304"], ["skill_docker", "skill_aws"]),
            ("CSE401", "Neural Networks & Vision", 4, 7, "Elective", ["AIML301"], ["skill_pytorch"]),
            ("CSE405", "Large Language Models & RAG", 4, 8, "Elective", ["AIML302"], ["skill_nlp", "skill_pytorch"])
        ]
        for code, name, credits, sem, cat, prereqs, skills in default_courses:
            self.add_course(code, name, credits, sem, cat)
            for p in prereqs:
                self.add_prerequisite(p, code)
            for s in skills:
                self.add_skill_mapping(code, s, 1.0)

    def add_course(self, code: str, name: str, credits: int, semester: int, category: str):
        self.courses[code] = {
            "code": code,
            "name": name,
            "credits": credits,
            "semester": semester,
            "category": category
        }

    def add_prerequisite(self, prereq_code: str, target_code: str):
        self.prereqs.add((prereq_code, target_code))

    def add_skill_mapping(self, course_code: str, skill_id: str, weight: float = 1.0):
        self.skills.add((course_code, skill_id, weight))

    def get_prerequisites_for(self, target_code: str) -> List[str]:
        """Returns direct prerequisites for target_code."""
        return [p for (p, c) in self.prereqs if c == target_code]

    def get_all_courses(self) -> Dict[str, Dict]:
        """Returns all courses in the graph."""
        return dict(self.courses)

    def get_skills_for_course(self, target_code: str) -> List[Tuple[str, float]]:
        """Returns skills imparted by target_code."""
        return [(s, w) for (c, s, w) in self.skills if c == target_code]

    def get_course_skills_map(self) -> Dict[str, List[str]]:
        """Returns mapping from course code to list of skill IDs."""
        res: Dict[str, List[str]] = {code: [] for code in self.courses.keys()}
        for (c, s, w) in self.skills:
            if c not in res:
                res[c] = []
            if s not in res[c]:
                res[c].append(s)
        return res

    def clear_curriculum(self):
        """Clears all courses, prerequisites, and skills."""
        self.courses.clear()
        self.prereqs.clear()
        self.skills.clear()

    def detect_cycle(self, course_codes: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """
        Detects if there is a cycle among prerequisite edges for the given courses (or all courses).
        Returns (has_cycle, cyclic_nodes).
        """
        nodes = set(course_codes) if course_codes else set(self.courses.keys())
        # Also include any prerequisite endpoints
        for (u, v) in self.prereqs:
            if course_codes is None or (u in nodes or v in nodes):
                nodes.add(u)
                nodes.add(v)

        in_degree = {n: 0 for n in nodes}
        adj = {n: [] for n in nodes}
        for (u, v) in self.prereqs:
            if u in nodes and v in nodes:
                adj[u].append(v)
                in_degree[v] += 1

        queue = [n for n in nodes if in_degree[n] == 0]
        visited_count = 0
        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count < len(nodes):
            cyclic = [n for n in nodes if in_degree[n] > 0]
            return True, cyclic
        return False, []

    def get_all_ancestor_prerequisites(self, target_code: str) -> Tuple[List[str], bool]:
        """
        Recursively finds all upstream prerequisites (DFS).
        Returns (ancestors, has_cycle).
        """
        visited = set()
        stack = [target_code]
        ancestors = []
        path_set = set()
        has_cycle = False

        while stack:
            curr = stack.pop()
            direct = self.get_prerequisites_for(curr)
            for p in direct:
                if p == target_code or p in path_set:
                    has_cycle = True
                if p not in visited:
                    visited.add(p)
                    ancestors.append(p)
                    stack.append(p)
                    path_set.add(p)
        return ancestors, has_cycle

    def check_feasibility(self, target_code: str, completed_codes: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Calculates if target_code can be taken given completed_codes.
        Returns: (is_feasible, missing_prereqs, prereq_path)
        """
        required, has_cycle = self.get_all_ancestor_prerequisites(target_code)
        if has_cycle:
            return False, ["CYCLE_DETECTED_" + target_code], []

        completed_set = set(completed_codes)
        missing = [req for req in required if req not in completed_set]
        is_feasible = len(missing) == 0
        path = self.get_topological_sort(required + [target_code])
        return is_feasible, missing, path

    def get_topological_sort(self, course_codes: List[str]) -> List[str]:
        """Kahn's Algorithm for topological ordering over prerequisite chains."""
        nodes = set(course_codes)
        in_degree = {n: 0 for n in nodes}
        adj = {n: [] for n in nodes}

        for (u, v) in self.prereqs:
            if u in nodes and v in nodes:
                adj[u].append(v)
                in_degree[v] += 1

        queue = [n for n in nodes if in_degree[n] == 0]
        topo = []
        while queue:
            # Sort queue by semester/code for deterministic topological ordering
            queue.sort(key=lambda c: (self.courses.get(c, {}).get("semester", 0), c))
            curr = queue.pop(0)
            topo.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Fallback for remaining nodes if cycle exists (or unconnected)
        for n in nodes:
            if n not in topo:
                topo.append(n)

        return topo


class Neo4jGraphManager:
    """Manages Neo4j Database connection with automatic in-memory fallback for offline environments."""

    def __init__(self):
        self.driver = None
        self.mock_graph = MockNeo4jGraph()
        self.use_mock = True
        self.curriculum_source = "seeded_demo"

        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # Connectivity check
            with self.driver.session() as session:
                session.run("RETURN 1")
            self.use_mock = False
            logger.info("Connected to live Neo4j database server.")
        except Exception as e:
            logger.warning(f"Neo4j live connection unavailable ({e}). Using in-memory graph fallback.")
            self.use_mock = True

    def close(self):
        if self.driver:
            self.driver.close()

    def get_backend_info(self) -> Dict[str, Any]:
        return {
            "backend": "neo4j" if not self.use_mock else "in_memory_mock",
            "is_demo_mock": self.use_mock,
            "curriculum_source": self.curriculum_source
        }

    def clear_curriculum(self):
        """Clears all courses and sets curriculum_source to empty."""
        self.mock_graph.clear_curriculum()
        self.curriculum_source = "empty"
        if not self.use_mock and self.driver:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")

    def mark_ingested(self):
        self.curriculum_source = "ingested"

    def get_all_courses(self) -> Dict[str, Dict[str, Any]]:
        """Returns all available courses from the configured graph store."""
        if self.use_mock or not self.driver:
            return self.mock_graph.get_all_courses()
        with self.driver.session() as session:
            result = session.run("MATCH (c:Course) RETURN c.code as code, c.name as name, c.credits as credits, c.semester as semester, c.category as category")
            return {
                r["code"]: {
                    "code": r["code"],
                    "name": r.get("name") or r["code"],
                    "credits": r.get("credits", 4),
                    "semester": r.get("semester", 1),
                    "category": r.get("category", "Core")
                }
                for r in result
            }

    def get_prerequisites_for(self, target_code: str) -> List[str]:
        """Returns direct prerequisites for target course from configured graph store."""
        if self.use_mock or not self.driver:
            return self.mock_graph.get_prerequisites_for(target_code)
        with self.driver.session() as session:
            result = session.run("MATCH (p:Course)-[:PREREQUISITE_OF]->(c:Course {code: $code}) RETURN p.code as prereq", code=target_code)
            return [r["prereq"] for r in result]

    def get_skills_for_course(self, target_code: str) -> List[Tuple[str, float]]:
        """Returns skills imparted by target course from configured graph store."""
        if self.use_mock or not self.driver:
            return self.mock_graph.get_skills_for_course(target_code)
        with self.driver.session() as session:
            result = session.run("MATCH (c:Course {code: $code})-[r:IMPARTS_SKILL|TEACHES]->(s:Skill) RETURN s.id as id, coalesce(r.weight, 1.0) as weight", code=target_code)
            return [(r["id"], float(r["weight"])) for r in result]

    def get_course_skills_map(self) -> Dict[str, List[str]]:
        """Returns mapping of course_code -> list of imparted skill IDs."""
        if self.use_mock or not self.driver:
            return self.mock_graph.get_course_skills_map()
        with self.driver.session() as session:
            result = session.run("MATCH (c:Course)-[r:IMPARTS_SKILL|TEACHES]->(s:Skill) RETURN c.code as code, s.id as skill_id")
            res: Dict[str, List[str]] = {}
            for r in result:
                code, skill_id = r["code"], r["skill_id"]
                if code not in res:
                    res[code] = []
                if skill_id not in res[code]:
                    res[code].append(skill_id)
            return res

    def detect_cycles(self, course_codes: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """Topological cycle detection across prerequisite graph."""
        if self.use_mock or not self.driver:
            return self.mock_graph.detect_cycle(course_codes)
        with self.driver.session() as session:
            result = session.run("MATCH (p:Course)-[:PREREQUISITE_OF]->(c:Course) RETURN p.code as prereq, c.code as target")
            prereqs = [(r["prereq"], r["target"]) for r in result]
            nodes = set(course_codes) if course_codes else set()
            for (u, v) in prereqs:
                if course_codes is None or (u in nodes or v in nodes):
                    nodes.add(u)
                    nodes.add(v)
            in_degree = {n: 0 for n in nodes}
            adj = {n: [] for n in nodes}
            for (u, v) in prereqs:
                if u in nodes and v in nodes:
                    adj[u].append(v)
                    in_degree[v] += 1
            queue = [n for n in nodes if in_degree[n] == 0]
            visited = 0
            while queue:
                curr = queue.pop(0)
                visited += 1
                for neighbor in adj[curr]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            if visited < len(nodes):
                return True, [n for n in nodes if in_degree[n] > 0]
            return False, []

    def add_course(self, code: str, name: str, credits: int, semester: int, category: str):
        self.mock_graph.add_course(code, name, credits, semester, category)
        if not self.use_mock and self.driver:
            with self.driver.session() as session:
                session.run(
                    """
                    MERGE (c:Course {code: $code})
                    SET c.name = $name, c.credits = $credits, c.semester = $semester, c.category = $category
                    """,
                    code=code, name=name, credits=credits, semester=semester, category=category
                )

    def add_prerequisite(self, prereq_code: str, target_code: str):
        self.mock_graph.add_prerequisite(prereq_code, target_code)
        if not self.use_mock and self.driver:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (p:Course {code: $prereq_code})
                    MATCH (t:Course {code: $target_code})
                    MERGE (p)-[:PREREQUISITE_OF]->(t)
                    """,
                    prereq_code=prereq_code, target_code=target_code
                )

    def add_skill_mapping(self, course_code: str, skill_id: str, weight: float = 1.0):
        self.mock_graph.add_skill_mapping(course_code, skill_id, weight)
        if not self.use_mock and self.driver:
            with self.driver.session() as session:
                session.run(
                    """
                    MATCH (c:Course {code: $course_code})
                    MERGE (s:Skill {id: $skill_id})
                    MERGE (c)-[:IMPARTS_SKILL {weight: $weight}]->(s)
                    """,
                    course_code=course_code, skill_id=skill_id, weight=weight
                )

    def check_prerequisite_feasibility(self, target_code: str, completed_codes: List[str]) -> Tuple[bool, List[str], List[str]]:
        if self.use_mock or not self.driver:
            return self.mock_graph.check_feasibility(target_code, completed_codes)

        with self.driver.session() as session:
            # Native Cypher shortest path / topological prerequisite traversal query
            query = """
            MATCH (target:Course {code: $target_code})
            OPTIONAL MATCH (prereq:Course)-[:PREREQUISITE_OF*1..]->(target)
            RETURN collect(DISTINCT prereq.code) as required_prereqs
            """
            result = session.run(query, target_code=target_code).single()
            required = result["required_prereqs"] if result and result["required_prereqs"] else []
            completed_set = set(completed_codes)
            missing = [r for r in required if r not in completed_set]
            is_feasible = len(missing) == 0

            # Topological path query
            path = self.mock_graph.get_topological_sort(required + [target_code])
            return is_feasible, missing, path

graph_manager = Neo4jGraphManager()
