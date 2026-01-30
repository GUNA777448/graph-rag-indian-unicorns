"""
Neo4j Database Connection Management
Implements connection pooling and context management
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

from src.config import get_settings


class Neo4jConnection:
    """
    Neo4j connection manager with connection pooling.
    Implements singleton pattern for efficient resource usage.
    """
    
    _instance: Optional["Neo4jConnection"] = None
    _driver: Optional[Driver] = None
    
    def __new__(cls) -> "Neo4jConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._driver is None:
            self._initialize_driver()
    
    def _initialize_driver(self) -> None:
        """Initialize the Neo4j driver with configuration"""
        settings = get_settings()
        try:
            self._driver = GraphDatabase.driver(
                settings.neo4j.uri,
                auth=(settings.neo4j.user, settings.neo4j.password),
                max_connection_lifetime=settings.neo4j.max_connection_lifetime,
                max_connection_pool_size=settings.neo4j.max_connection_pool_size,
                connection_timeout=settings.neo4j.connection_timeout,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to create Neo4j driver: {e}")
    
    @property
    def driver(self) -> Driver:
        """Get the Neo4j driver instance"""
        if self._driver is None:
            self._initialize_driver()
        return self._driver
    
    def verify_connectivity(self) -> bool:
        """Verify database connectivity"""
        try:
            self.driver.verify_connectivity()
            return True
        except (ServiceUnavailable, AuthError) as e:
            return False
    
    @contextmanager
    def session(self, database: Optional[str] = None) -> Generator[Session, None, None]:
        """
        Context manager for Neo4j sessions.
        Ensures proper session cleanup.
        """
        settings = get_settings()
        db = database or settings.neo4j.database
        session = self.driver.session(database=db)
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results as list of dicts.
        
        Args:
            query: Cypher query string
            params: Query parameters
            database: Target database (optional)
            
        Returns:
            List of result records as dictionaries
        """
        with self.session(database) as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
    
    def execute_write(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> None:
        """Execute a write transaction"""
        with self.session(database) as session:
            session.execute_write(lambda tx: tx.run(query, params or {}))
    
    def close(self) -> None:
        """Close the driver connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
    
    def __enter__(self) -> "Neo4jConnection":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# Singleton accessor
_connection: Optional[Neo4jConnection] = None


def get_connection() -> Neo4jConnection:
    """Get the singleton Neo4j connection instance"""
    global _connection
    if _connection is None:
        _connection = Neo4jConnection()
    return _connection
