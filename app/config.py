import os
from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "Autonomous Degree Navigator Agent (ADNA)"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database Paths & Connection Specs
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./adna.db")
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    
    # Neo4j Settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    USE_MOCK_NEO4J_IF_UNAVAILABLE: bool = True

    # Skill Gap Formula Weights
    WEIGHT_MARKET_DEMAND: float = 0.6
    WEIGHT_RECENCY_DECAY: float = 0.4
    RECENCY_DECAY_LAMBDA: float = 0.05

    # Planner Objective Function Weights
    WEIGHT_GAP_CLOSURE: float = 0.40
    WEIGHT_MARKET_ALIGNMENT: float = 0.30
    WEIGHT_FEASIBILITY: float = 0.20
    WEIGHT_WORKLOAD_PENALTY: float = 0.10

    # General Constraints
    DEFAULT_CREDIT_CAP_PER_SEM: int = 24
    RECOMMENDED_CREDITS_PER_SEM: int = 20

settings = Settings()
