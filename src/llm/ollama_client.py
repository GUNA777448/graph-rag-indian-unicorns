"""
Ollama LLM Client
Handles communication with local Ollama instance
"""

import requests
from dataclasses import dataclass
from typing import Optional, Dict, Any
from functools import lru_cache

from src.config import get_settings


@dataclass
class LLMResponse:
    """Structured LLM response"""
    content: str
    model: str
    total_duration_ms: float = 0.0
    eval_count: int = 0
    success: bool = True
    error: Optional[str] = None


class OllamaClient:
    """
    Client for interacting with Ollama API.
    Implements retry logic and error handling.
    """
    
    SYSTEM_PROMPT = """You are an expert analyst for Indian Unicorn Startups. 
You have access to a knowledge graph containing information about 102 Indian unicorn companies, 
their investors, sectors, locations, and valuations.

Guidelines:
- Use the provided context from the knowledge graph to answer questions accurately
- Be concise and specific in your responses
- Format numbers nicely (e.g., $5.6B for valuation)
- If data is not in the context, clearly state that
- Highlight key insights and patterns when relevant
- Use bullet points for lists"""

    def __init__(self):
        self._settings = get_settings()
        self._base_url = self._settings.ollama.base_url
        self._model = self._settings.ollama.model
        self._timeout = self._settings.ollama.timeout
    
    @property
    def generate_url(self) -> str:
        """Get the generate API endpoint"""
        return f"{self._base_url}/api/generate"
    
    @property
    def tags_url(self) -> str:
        """Get the tags API endpoint for health check"""
        return f"{self._base_url}/api/tags"
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(self.tags_url, timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def get_available_models(self) -> list:
        """Get list of available models"""
        try:
            response = requests.get(self.tags_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name") for m in data.get("models", [])]
        except requests.exceptions.RequestException:
            pass
        return []
    
    def generate(
        self,
        prompt: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: User's question
            context: Retrieved context from knowledge graph
            system_prompt: Optional custom system prompt
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse with generated content
        """
        settings = self._settings.ollama
        
        # Build the full prompt with context
        full_prompt = self._build_prompt(prompt, context)
        
        # Prepare request payload
        payload = {
            "model": self._model,
            "prompt": full_prompt,
            "system": system_prompt or self.SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "temperature": temperature or settings.temperature,
                "num_predict": max_tokens or settings.max_tokens,
            }
        }
        
        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=self._timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return LLMResponse(
                    content=data.get("response", ""),
                    model=data.get("model", self._model),
                    total_duration_ms=data.get("total_duration", 0) / 1_000_000,
                    eval_count=data.get("eval_count", 0),
                    success=True
                )
            else:
                return LLMResponse(
                    content="",
                    model=self._model,
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except requests.exceptions.ConnectionError:
            return LLMResponse(
                content="",
                model=self._model,
                success=False,
                error="Cannot connect to Ollama. Make sure it's running: `ollama serve`"
            )
        except requests.exceptions.Timeout:
            return LLMResponse(
                content="",
                model=self._model,
                success=False,
                error="Request timed out. The model may be loading or overloaded."
            )
        except Exception as e:
            return LLMResponse(
                content="",
                model=self._model,
                success=False,
                error=str(e)
            )
    
    def _build_prompt(self, user_query: str, context: str) -> str:
        """Build the complete prompt with context"""
        return f"""Context from Knowledge Graph:
{context}

User Question: {user_query}

Based on the context above, provide a helpful and accurate answer:"""


# Singleton accessor
_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get the singleton Ollama client instance"""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
