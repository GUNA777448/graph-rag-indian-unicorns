"""
Application Settings and Configuration
Uses environment variables with sensible defaults
"""

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional


@dataclass(frozen=True)
class Neo4jConfig:
    """Neo4j database configuration"""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "12345678"
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_timeout: int = 30


@dataclass(frozen=True)
class OllamaConfig:
    """Ollama LLM configuration"""
    base_url: str = "http://localhost:11434"
    model: str = "mistral"
    temperature: float = 0.3
    max_tokens: int = 500
    timeout: int = 60


@dataclass(frozen=True)
class RAGConfig:
    """RAG pipeline configuration"""
    max_context_items: int = 10
    max_companies_per_search: int = 5
    max_investors_per_search: int = 5
    enable_caching: bool = True
    cache_ttl: int = 300  # seconds


@dataclass(frozen=True)
class UIConfig:
    """Streamlit UI configuration"""
    page_title: str = "Indian Unicorns Graph RAG"
    page_icon: str = "🦄"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"


@dataclass
class Settings:
    """Main application settings"""
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    debug: bool = False
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables"""
        return cls(
            neo4j=Neo4jConfig(
                uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                user=os.getenv("NEO4J_USER", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD", "12345678"),
                database=os.getenv("NEO4J_DATABASE", "neo4j"),
            ),
            ollama=OllamaConfig(
                base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
                model=os.getenv("OLLAMA_MODEL", "mistral"),
                temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.3")),
            ),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings.from_env()
