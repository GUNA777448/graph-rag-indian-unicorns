"""
Graph Retriever
Extracts relevant entities and relationships from user queries
"""

import re
from dataclasses import dataclass, field
from typing import List, Set, Tuple, Optional
from enum import Enum, auto


class EntityType(Enum):
    """Types of entities that can be extracted from queries"""
    COMPANY = auto()
    INVESTOR = auto()
    SECTOR = auto()
    LOCATION = auto()
    VALUATION = auto()
    COMPARISON = auto()


@dataclass
class ExtractedEntities:
    """Container for extracted entities from a query"""
    companies: List[str] = field(default_factory=list)
    investors: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    query_types: Set[EntityType] = field(default_factory=set)
    is_comparison: bool = False
    is_aggregation: bool = False
    is_top_query: bool = False


class GraphRetriever:
    """
    Retrieves relevant context from the knowledge graph based on query analysis.
    Implements entity extraction and query classification.
    """
    
    # Known entities for better extraction
    KNOWN_INVESTORS = {
        "tiger global", "softbank", "sequoia", "accel", "matrix", 
        "temasek", "tencent", "alibaba", "lightspeed", "elevation",
        "nexus", "kalaari", "chiratae", "bessemer", "general atlantic"
    }
    
    KNOWN_SECTORS = {
        "fintech", "edtech", "e-commerce", "ecommerce", "saas", 
        "foodtech", "healthtech", "proptech", "logistics", "gaming",
        "d2c", "b2b", "marketplace", "mobility", "adtech"
    }
    
    KNOWN_LOCATIONS = {
        "bangalore", "bengaluru", "mumbai", "delhi", "gurgaon", 
        "gurugram", "noida", "pune", "chennai", "hyderabad",
        "jaipur", "thane", "goa", "kolkata"
    }
    
    COMPARISON_KEYWORDS = {"compare", "vs", "versus", "difference", "between"}
    AGGREGATION_KEYWORDS = {"total", "sum", "average", "count", "how many"}
    TOP_KEYWORDS = {"top", "best", "highest", "largest", "biggest", "most"}
    
    INVESTOR_KEYWORDS = {"investor", "invested", "portfolio", "fund", "vc", "capital", "backed"}
    SECTOR_KEYWORDS = {"sector", "industry", "segment", "vertical"}
    LOCATION_KEYWORDS = {"located", "based", "city", "where"}
    
    def extract_entities(self, query: str) -> ExtractedEntities:
        """
        Extract entities and classify the query.
        
        Args:
            query: User's natural language query
            
        Returns:
            ExtractedEntities with all extracted information
        """
        query_lower = query.lower()
        entities = ExtractedEntities()
        
        # Classify query type
        entities.is_comparison = any(kw in query_lower for kw in self.COMPARISON_KEYWORDS)
        entities.is_aggregation = any(kw in query_lower for kw in self.AGGREGATION_KEYWORDS)
        entities.is_top_query = any(kw in query_lower for kw in self.TOP_KEYWORDS)
        
        # Extract potential keywords (filter short words)
        words = [w.strip("?,.'\"!()") for w in query.split()]
        keywords = [w for w in words if len(w) > 2]
        
        # Check for investor context
        if any(kw in query_lower for kw in self.INVESTOR_KEYWORDS):
            entities.query_types.add(EntityType.INVESTOR)
        
        # Check for sector context
        if any(kw in query_lower for kw in self.SECTOR_KEYWORDS):
            entities.query_types.add(EntityType.SECTOR)
        
        # Check for location context
        if any(kw in query_lower for kw in self.LOCATION_KEYWORDS):
            entities.query_types.add(EntityType.LOCATION)
        
        # Extract known investors
        for investor in self.KNOWN_INVESTORS:
            if investor in query_lower:
                entities.investors.append(investor.title())
                entities.query_types.add(EntityType.INVESTOR)
        
        # Extract known sectors
        for sector in self.KNOWN_SECTORS:
            if sector in query_lower:
                entities.sectors.append(sector.title())
                entities.query_types.add(EntityType.SECTOR)
        
        # Extract known locations
        for location in self.KNOWN_LOCATIONS:
            if location in query_lower:
                entities.locations.append(location.title())
                entities.query_types.add(EntityType.LOCATION)
        
        # Potential company names (capitalized words not in known lists)
        for word in keywords:
            word_lower = word.lower()
            if (word[0].isupper() and 
                word_lower not in self.KNOWN_INVESTORS and
                word_lower not in self.KNOWN_SECTORS and
                word_lower not in self.KNOWN_LOCATIONS and
                len(word) > 3):
                entities.companies.append(word)
                entities.query_types.add(EntityType.COMPANY)
        
        return entities
    
    def get_query_intent(self, entities: ExtractedEntities) -> str:
        """
        Determine the primary intent of the query.
        
        Args:
            entities: Extracted entities from the query
            
        Returns:
            String describing the query intent
        """
        if entities.is_comparison:
            return "comparison"
        elif entities.is_aggregation:
            return "aggregation"
        elif entities.is_top_query:
            return "top_ranking"
        elif EntityType.INVESTOR in entities.query_types:
            return "investor_info"
        elif EntityType.SECTOR in entities.query_types:
            return "sector_info"
        elif EntityType.LOCATION in entities.query_types:
            return "location_info"
        elif EntityType.COMPANY in entities.query_types:
            return "company_info"
        else:
            return "general"
