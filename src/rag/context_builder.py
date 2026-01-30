"""
Context Builder
Builds structured context from Knowledge Graph for LLM consumption
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from src.database import GraphQueries
from src.config import get_settings
from .retriever import GraphRetriever, ExtractedEntities, EntityType


@dataclass
class RetrievalResult:
    """Result of context retrieval"""
    context: str
    entities_found: int
    retrieval_time_ms: float
    sources: List[str]


class ContextBuilder:
    """
    Builds context from the Knowledge Graph based on query analysis.
    Implements retrieval strategies for different query types.
    """
    
    def __init__(self):
        self._queries = GraphQueries()
        self._retriever = GraphRetriever()
        self._settings = get_settings()
    
    def build_context(self, user_query: str) -> RetrievalResult:
        """
        Build context from KG based on user query.
        
        Args:
            user_query: User's natural language query
            
        Returns:
            RetrievalResult with context and metadata
        """
        start_time = time.time()
        context_parts = []
        sources = []
        entities_found = 0
        
        # Extract entities from query
        entities = self._retriever.extract_entities(user_query)
        intent = self._retriever.get_query_intent(entities)
        
        # Build context based on intent
        if intent == "comparison":
            context_parts, sources, entities_found = self._build_comparison_context(entities)
        elif intent == "top_ranking":
            context_parts, sources, entities_found = self._build_top_ranking_context(entities)
        elif intent == "aggregation":
            context_parts, sources, entities_found = self._build_aggregation_context(entities)
        elif intent == "investor_info":
            context_parts, sources, entities_found = self._build_investor_context(entities)
        elif intent == "sector_info":
            context_parts, sources, entities_found = self._build_sector_context(entities)
        elif intent == "location_info":
            context_parts, sources, entities_found = self._build_location_context(entities)
        elif intent == "company_info":
            context_parts, sources, entities_found = self._build_company_context(entities)
        else:
            context_parts, sources, entities_found = self._build_general_context()
        
        # Fallback to general context if nothing found
        if not context_parts:
            context_parts, sources, entities_found = self._build_general_context()
        
        retrieval_time = (time.time() - start_time) * 1000
        
        return RetrievalResult(
            context="\n\n".join(context_parts),
            entities_found=entities_found,
            retrieval_time_ms=retrieval_time,
            sources=sources
        )
    
    def _build_company_context(self, entities: ExtractedEntities) -> tuple:
        """Build context for company-related queries"""
        context_parts = []
        sources = []
        count = 0
        
        # Search for mentioned companies
        for company_name in entities.companies[:3]:
            details = self._queries.get_company_details(company_name)
            if details:
                context_parts.append(self._format_company_details(details))
                sources.append(f"company:{details['company']}")
                count += 1
        
        # Also search investors if mentioned
        for investor in entities.investors:
            portfolio = self._queries.get_investor_portfolio(investor, limit=5)
            if portfolio:
                context_parts.append(self._format_investor_portfolio(portfolio))
                sources.append(f"investor:{investor}")
                count += len(portfolio)
        
        return context_parts, sources, count
    
    def _build_investor_context(self, entities: ExtractedEntities) -> tuple:
        """Build context for investor-related queries"""
        context_parts = []
        sources = []
        count = 0
        
        for investor in entities.investors[:3]:
            portfolio = self._queries.get_investor_portfolio(investor, limit=10)
            if portfolio:
                context_parts.append(self._format_investor_portfolio(portfolio))
                sources.append(f"investor:{investor}")
                count += len(portfolio)
                
                # Add co-investors
                co_investors = self._queries.get_co_investors(investor, limit=5)
                if co_investors:
                    context_parts.append(self._format_co_investors(investor, co_investors))
        
        # If no specific investor, show top investors
        if not entities.investors:
            top_investors = self._queries.get_top_investors(10)
            if top_investors:
                context_parts.append(self._format_top_investors(top_investors))
                sources.append("top_investors")
                count += len(top_investors)
        
        return context_parts, sources, count
    
    def _build_sector_context(self, entities: ExtractedEntities) -> tuple:
        """Build context for sector-related queries"""
        context_parts = []
        sources = []
        count = 0
        
        for sector in entities.sectors[:3]:
            companies = self._queries.get_sector_companies(sector, limit=10)
            if companies:
                context_parts.append(self._format_sector_companies(sector, companies))
                sources.append(f"sector:{sector}")
                count += len(companies)
        
        # Add sector stats
        sector_stats = self._queries.get_sector_stats()
        if sector_stats:
            context_parts.append(self._format_sector_stats(sector_stats))
            sources.append("sector_stats")
        
        return context_parts, sources, count
    
    def _build_location_context(self, entities: ExtractedEntities) -> tuple:
        """Build context for location-related queries"""
        context_parts = []
        sources = []
        count = 0
        
        for location in entities.locations[:3]:
            companies = self._queries.get_city_companies(location, limit=10)
            if companies:
                context_parts.append(self._format_city_companies(location, companies))
                sources.append(f"city:{location}")
                count += len(companies)
        
        # Add location stats
        location_stats = self._queries.get_location_stats()
        if location_stats:
            context_parts.append(self._format_location_stats(location_stats[:10]))
            sources.append("location_stats")
        
        return context_parts, sources, count
    
    def _build_comparison_context(self, entities: ExtractedEntities) -> tuple:
        """Build context for comparison queries"""
        context_parts = []
        sources = []
        count = 0
        
        # Get details for all mentioned companies
        for company_name in entities.companies[:5]:
            details = self._queries.get_company_details(company_name)
            if details:
                context_parts.append(self._format_company_details(details))
                sources.append(f"company:{details['company']}")
                count += 1
        
        # Compare sectors if mentioned
        for sector in entities.sectors[:3]:
            companies = self._queries.get_sector_companies(sector, limit=5)
            if companies:
                context_parts.append(self._format_sector_companies(sector, companies))
                sources.append(f"sector:{sector}")
                count += len(companies)
        
        # Compare locations if mentioned
        for location in entities.locations[:3]:
            companies = self._queries.get_city_companies(location, limit=5)
            if companies:
                context_parts.append(self._format_city_companies(location, companies))
                sources.append(f"city:{location}")
                count += len(companies)
        
        return context_parts, sources, count
    
    def _build_top_ranking_context(self, entities: ExtractedEntities) -> tuple:
        """Build context for top/ranking queries"""
        context_parts = []
        sources = []
        count = 0
        
        # Top companies
        top_companies = self._queries.get_top_companies(10)
        if top_companies:
            context_parts.append(self._format_top_companies(top_companies))
            sources.append("top_companies")
            count += len(top_companies)
        
        # Top investors
        top_investors = self._queries.get_top_investors(10)
        if top_investors:
            context_parts.append(self._format_top_investors(top_investors))
            sources.append("top_investors")
            count += len(top_investors)
        
        # Filter by sector if mentioned
        for sector in entities.sectors[:2]:
            companies = self._queries.get_sector_companies(sector, limit=5)
            if companies:
                context_parts.append(self._format_sector_companies(sector, companies))
                sources.append(f"sector:{sector}")
        
        return context_parts, sources, count
    
    def _build_aggregation_context(self, entities: ExtractedEntities) -> tuple:
        """Build context for aggregation queries"""
        context_parts = []
        sources = []
        count = 0
        
        # Graph stats
        stats = self._queries.get_graph_stats()
        if stats:
            context_parts.append(self._format_graph_stats(stats))
            sources.append("graph_stats")
            count += 1
        
        # Sector stats
        sector_stats = self._queries.get_sector_stats()
        if sector_stats:
            context_parts.append(self._format_sector_stats(sector_stats))
            sources.append("sector_stats")
            count += len(sector_stats)
        
        # Location stats
        location_stats = self._queries.get_location_stats()
        if location_stats:
            context_parts.append(self._format_location_stats(location_stats[:10]))
            sources.append("location_stats")
        
        return context_parts, sources, count
    
    def _build_general_context(self) -> tuple:
        """Build general context when no specific entities found"""
        context_parts = []
        sources = []
        
        # Graph stats
        stats = self._queries.get_graph_stats()
        if stats:
            context_parts.append(self._format_graph_stats(stats))
            sources.append("graph_stats")
        
        # Top companies
        top_companies = self._queries.get_top_companies(5)
        if top_companies:
            context_parts.append(self._format_top_companies(top_companies))
            sources.append("top_companies")
        
        return context_parts, sources, len(top_companies) if top_companies else 0
    
    # =========================================================================
    # FORMATTING METHODS
    # =========================================================================
    
    def _format_company_details(self, details: Dict) -> str:
        """Format company details for context"""
        investors = details.get('investors', [])
        investor_str = ', '.join(investors[:7]) if investors else 'N/A'
        if len(investors) > 7:
            investor_str += f" (+{len(investors) - 7} more)"
        
        return f"""**Company: {details.get('company', 'N/A')}**
- Sector: {details.get('sector', 'N/A')} {f"({details.get('subsector')})" if details.get('subsector') else ''}
- Current Valuation: ${details.get('valuation', 'N/A')}B
- Entry Valuation: ${details.get('entryValuation', 'N/A')}B
- Entry Date: {details.get('entryDate', 'N/A')}
- Locations: {', '.join(details.get('locations', [])) or 'N/A'}
- Key Investors: {investor_str}"""
    
    def _format_investor_portfolio(self, portfolio: List[Dict]) -> str:
        """Format investor portfolio for context"""
        if not portfolio:
            return ""
        
        investor_name = portfolio[0].get('investor', 'Unknown')
        companies = [f"{p['company']} (${p['valuation']}B - {p.get('sector', 'N/A')})" 
                    for p in portfolio]
        
        return f"""**Investor: {investor_name}**
- Portfolio ({len(portfolio)} companies): {', '.join(companies)}"""
    
    def _format_co_investors(self, investor: str, co_investors: List[Dict]) -> str:
        """Format co-investors for context"""
        lines = [f"**Co-investors of {investor}:**"]
        for ci in co_investors:
            lines.append(f"- {ci['coInvestor']}: {ci['sharedInvestments']} shared investments")
        return '\n'.join(lines)
    
    def _format_sector_companies(self, sector: str, companies: List[Dict]) -> str:
        """Format sector companies for context"""
        company_lines = [f"{c['company']} (${c['valuation']}B)" for c in companies]
        return f"""**{sector} Sector Companies:**
{', '.join(company_lines)}"""
    
    def _format_city_companies(self, city: str, companies: List[Dict]) -> str:
        """Format city companies for context"""
        company_lines = [f"{c['company']} ({c.get('sector', 'N/A')}, ${c['valuation']}B)" 
                        for c in companies]
        return f"""**Companies in {city}:**
{', '.join(company_lines)}"""
    
    def _format_top_companies(self, companies: List[Dict]) -> str:
        """Format top companies for context"""
        lines = ["**Top Unicorns by Valuation:**"]
        for i, c in enumerate(companies, 1):
            lines.append(f"{i}. {c['company']} - ${c['valuation']}B ({c.get('sector', 'N/A')})")
        return '\n'.join(lines)
    
    def _format_top_investors(self, investors: List[Dict]) -> str:
        """Format top investors for context"""
        lines = ["**Most Active Investors:**"]
        for i, inv in enumerate(investors, 1):
            lines.append(f"{i}. {inv['investor']} - {inv['investments']} investments (${inv.get('portfolioValue', 'N/A')}B total)")
        return '\n'.join(lines)
    
    def _format_sector_stats(self, stats: List[Dict]) -> str:
        """Format sector statistics for context"""
        lines = ["**Sector Statistics:**"]
        for s in stats[:8]:
            lines.append(f"- {s['sector']}: {s['companyCount']} companies, ${s['totalValuation']}B total")
        return '\n'.join(lines)
    
    def _format_location_stats(self, stats: List[Dict]) -> str:
        """Format location statistics for context"""
        lines = ["**Location Statistics:**"]
        for s in stats[:8]:
            lines.append(f"- {s['city']}: {s['companyCount']} companies, ${s['totalValuation']}B total")
        return '\n'.join(lines)
    
    def _format_graph_stats(self, stats: Dict) -> str:
        """Format graph statistics for context"""
        return f"""**Indian Unicorn Startups Database:**
- Total Companies: {stats.get('companies', 'N/A')}
- Total Investors: {stats.get('investors', 'N/A')}
- Sectors: {stats.get('sectors', 'N/A')}
- Locations: {stats.get('locations', 'N/A')}
- Total Relationships: {stats.get('relationships', 'N/A')}"""
