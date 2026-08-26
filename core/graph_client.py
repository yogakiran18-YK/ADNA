from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class GraphClient:
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
    def close(self):
        if self.driver:
            self.driver.close()

    def execute_write(self, query: str, parameters: dict = None):
        """Execute a write transaction"""
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Error executing write query: {e}")
                raise e

    def execute_read(self, query: str, parameters: dict = None):
        """Execute a read transaction"""
        with self.driver.session() as session:
            try:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"Error executing read query: {e}")
                raise e

    def run_cypher_script(self, file_path: str):
        """Execute a cypher script containing multiple statements separated by ';'"""
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Split by ';' but ignore empty statements
        queries = [q.strip() for q in content.split(';') if q.strip()]
        
        with self.driver.session() as session:
            for query in queries:
                if not query.startswith("//"): # Basic check to skip full line comments
                    try:
                        session.run(query)
                    except Exception as e:
                        logger.error(f"Error executing script query '{query}': {e}")
                        raise e
