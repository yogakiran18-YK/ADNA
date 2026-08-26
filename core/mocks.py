class MockE2EGraphClient:
    def __init__(self):
        self.writes = []
    
    def execute_write(self, query: str, parameters: dict = None):
        self.writes.append((query, parameters))
        return [{"s": "mock_node"}]
        
    def execute_read(self, query: str, parameters: dict = None):
        # SkillGap queries
        if "WHERE c.code IN $completed_courses" in query:
            return [] # No completed courses in mock
            
        if "s.demand_score_history[-1]" in query:
            reqs = parameters.get("required_skills", [])
            return [{"skill_name": reqs[0], "latest_score": 0.9}]
            
        # Planner queries
        if "RETURN c.code AS code, c.credits AS credits" in query:
            return [
                {"code": "CS101", "credits": 3},
                {"code": "CS102", "credits": 3}
            ]
        if "RETURN p.code AS prereq, c.code AS course" in query:
            return [{"prereq": "CS101", "course": "CS102"}]
            
        if "collect(s.name) AS skills" in query:
            return [
                {"code": "CS101", "skills": ["Python"]},
                {"code": "CS102", "skills": ["DataStructures"]}
            ]
            
        return []
