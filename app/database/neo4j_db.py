import logging
from typing import List, Dict, Set, Tuple, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class MockNeo4jGraph:
    """In-memory Graph storage mimicking Neo4j Cypher pathfinding & topological ordering."""
    def __init__(self):
        self.courses: Dict[str, Dict] = {} # code -> properties
        self.prereqs: Set[Tuple[str, str]] = set() # (prereq_code, course_code) i.e. prereq -> target
        self.skills: Set[Tuple[str, str, float]] = set() # (course_code, skill_id, weight)

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

    def get_all_ancestor_prerequisites(self, target_code: str) -> List[str]:
        """Recursively finds all upstream prerequisites (DFS)."""
        visited = set()
        stack = [target_code]
        ancestors = []
        while stack:
            curr = stack.pop()
            direct = self.get_prerequisites_for(curr)
            for p in direct:
                if p not in visited:
                    visited.add(p)
                    ancestors.append(p)
                    stack.append(p)
        return ancestors

    def check_feasibility(self, target_code: str, completed_codes: List[str]) -> Tuple[bool, List[str], List[str]]:
        """
        Calculates if target_code can be taken given completed_codes.
        Returns: (is_feasible, missing_prereqs, prereq_path)
        """
        required = self.get_all_ancestor_prerequisites(target_code)
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
