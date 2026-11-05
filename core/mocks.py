ALL_COURSES = [
    {"code": "CS101", "credits": 4, "skills": ["Python", "Programming", "C", "Algorithms"]},
    {"code": "MA101", "credits": 4, "skills": ["Mathematics", "Linear Algebra", "Calculus"]},
    {"code": "PH101", "credits": 4, "skills": ["Physics"]},
    {"code": "EE101", "credits": 4, "skills": ["Electronics", "IoT Protocols", "Microcontrollers"]},
    {"code": "CS102", "credits": 4, "skills": ["Python", "DataStructures", "Object-Oriented Programming"]},
    {"code": "MA102", "credits": 4, "skills": ["Probability", "Statistics", "Differential Equations"]},
    {"code": "CS103", "credits": 4, "skills": ["Computer Architecture", "Digital Logic"]},
    {"code": "CY101", "credits": 4, "skills": ["Environmental Studies"]},
    {"code": "CS201", "credits": 4, "skills": ["Data Structures", "Algorithms", "DataStructures"]},
    {"code": "CS202", "credits": 4, "skills": ["Discrete Math", "Graph Theory", "Cryptography"]},
    {"code": "CS203", "credits": 4, "skills": ["Assembly", "Computer Systems", "Microcontrollers"]},
    {"code": "CS204", "credits": 4, "skills": ["Java", "C++", "Software Engineering"]},
    {"code": "CS301", "credits": 4, "skills": ["Algorithms", "Problem Solving", "System Design"]},
    {"code": "CS302", "credits": 4, "skills": ["Operating Systems", "Linux", "Concurrency"]},
    {"code": "CS402", "credits": 4, "skills": ["SQL", "Databases", "PostgreSQL", "Data Warehousing"]},
    {"MA201": "MA201", "code": "MA201", "credits": 4, "skills": ["Statistics", "Data Analysis", "Numerical Methods"]},
    {"code": "CS501", "credits": 4, "skills": ["Computer Networks", "Network Security", "REST APIs"]},
    {"code": "CS401", "credits": 4, "skills": ["Artificial Intelligence", "Machine Learning", "Prompt Engineering"]},
    {"code": "CS502", "credits": 4, "skills": ["Automata", "Theory of Computation"]},
    {"code": "CS503", "credits": 4, "skills": ["React", "JavaScript", "TypeScript", "Next.js", "CSS/Tailwind", "UI/UX Design", "Web3.js"]},
    {"code": "CS601", "credits": 4, "skills": ["Machine Learning", "Scikit-Learn", "Python", "Data Visualization", "Tableau", "PowerBI"]},
    {"code": "CS602", "credits": 4, "skills": ["Compiler Design", "Language Engineering"]},
    {"code": "CS603", "credits": 4, "skills": ["Docker", "AWS", "Cloud Computing", "Kubernetes", "Azure", "GCP", "Terraform"]},
    {"code": "CS604", "credits": 4, "skills": ["Network Security", "Cryptography", "Security Auditing", "Smart Contracts", "Solidity"]},
    {"code": "CS701", "credits": 4, "skills": ["Deep Learning", "PyTorch", "TensorFlow", "Computer Vision"]},
    {"code": "CS702", "credits": 4, "skills": ["Distributed Systems", "Microservices", "System Design", "FastAPI", "Node.js", "Redis"]},
    {"code": "CS703", "credits": 4, "skills": ["ETL", "Apache Spark", "Big Data", "Data Warehousing", "Snowflake", "MongoDB"]},
    {"code": "CS704", "credits": 4, "skills": ["Natural Language Processing", "Large Language Models", "Transformers", "LangChain", "Vector Databases", "Prompt Engineering"]},
    {"code": "CS801", "credits": 4, "skills": ["Capstone", "System Design", "Project Management"]},
    {"code": "CS802", "credits": 4, "skills": ["High Performance Computing", "GPU Computing", "CUDA", "C++", "RTOS", "Embedded Linux"]},
    {"code": "CS803", "credits": 4, "skills": ["MLOps", "CI/CD", "Model Deployment", "React Native", "Flutter", "Mobile UI/UX"]}
]

ALL_EDGES = [
    {"prereq": "CS101", "course": "CS102"},
    {"prereq": "MA101", "course": "MA102"},
    {"prereq": "CS102", "course": "CS201"},
    {"prereq": "MA101", "course": "CS202"},
    {"prereq": "CS103", "course": "CS203"},
    {"prereq": "CS102", "course": "CS204"},
    {"prereq": "CS201", "course": "CS301"},
    {"prereq": "CS201", "course": "CS302"},
    {"prereq": "CS201", "course": "CS402"},
    {"prereq": "MA102", "course": "MA201"},
    {"prereq": "CS302", "course": "CS501"},
    {"prereq": "CS201", "course": "CS401"},
    {"prereq": "CS202", "course": "CS502"},
    {"prereq": "CS102", "course": "CS503"},
    {"prereq": "CS401", "course": "CS601"},
    {"prereq": "CS502", "course": "CS602"},
    {"prereq": "CS302", "course": "CS603"},
    {"prereq": "CS501", "course": "CS604"},
    {"prereq": "CS601", "course": "CS701"},
    {"prereq": "CS501", "course": "CS702"},
    {"prereq": "CS402", "course": "CS703"},
    {"prereq": "CS601", "course": "CS704"},
    {"prereq": "CS701", "course": "CS801"},
    {"prereq": "CS701", "course": "CS802"},
    {"prereq": "CS603", "course": "CS803"}
]

class MockE2EGraphClient:
    def __init__(self):
        self.writes = []
    
    def execute_write(self, query: str, parameters: dict = None):
        self.writes.append((query, parameters))
        return [{"s": "mock_node"}]
        
    def execute_read(self, query: str, parameters: dict = None):
        # SkillGap queries
        if "WHERE c.code IN $completed_courses" in query:
            completed = parameters.get("completed_courses", []) if parameters else []
            completed_set = set(c.strip().upper() for c in completed)
            skills = []
            for c in ALL_COURSES:
                if c["code"] in completed_set:
                    for s in c["skills"]:
                        skills.append({"skill_name": s})
            return skills
            
        if "s.demand_score_history[-1]" in query:
            reqs = parameters.get("required_skills", []) if parameters else []
            return [{"skill_name": s, "latest_score": 0.88} for s in reqs]
            
        # Planner queries
        if "RETURN c.code AS code, c.credits AS credits" in query:
            return [{"code": c["code"], "credits": c["credits"]} for c in ALL_COURSES]
            
        if "RETURN p.code AS prereq, c.code AS course" in query:
            return ALL_EDGES
            
        if "collect(s.name) AS skills" in query:
            return [{"code": c["code"], "skills": c["skills"]} for c in ALL_COURSES]
            
        return []

