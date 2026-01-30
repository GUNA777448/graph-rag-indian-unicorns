"""
Neo4j Cypher Queries for Knowledge Graph
Optimized queries with parameterization for security and performance
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .connection import get_connection


@dataclass
class QueryResult:
    """Wrapper for query results with metadata"""
    data: List[Dict[str, Any]]
    count: int
    query_time_ms: float = 0.0


class GraphQueries:
    """
    Repository class for all Knowledge Graph queries.
    Implements the Repository pattern for clean separation of concerns.
    """
    
    def __init__(self):
        self._conn = get_connection()
    
    # =========================================================================
    # COMPANY QUERIES
    # =========================================================================
    
    def search_companies(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Search companies by name (case-insensitive partial match).
        
        Args:
            search_term: Search string
            limit: Maximum results to return
            
        Returns:
            List of matching companies with basic info
        """
        query = """
        MATCH (c:Company)
        WHERE toLower(c.name) CONTAINS toLower($term)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
        OPTIONAL MATCH (c)-[:LOCATED_IN]->(l:Location)
        RETURN c.name as company, 
               c.currentValuation as valuation, 
               s.name as sector, 
               collect(DISTINCT l.city) as locations
        ORDER BY c.currentValuation DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"term": search_term, "limit": limit})
    
    def get_company_details(self, company_name: str) -> Optional[Dict]:
        """
        Get comprehensive details for a specific company.
        
        Args:
            company_name: Company name to search
            
        Returns:
            Company details with all relationships
        """
        query = """
        MATCH (c:Company)
        WHERE toLower(c.name) CONTAINS toLower($name)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
        OPTIONAL MATCH (c)-[:SPECIALIZES_IN]->(ss:SubSector)
        OPTIONAL MATCH (c)-[:LOCATED_IN]->(l:Location)
        OPTIONAL MATCH (i:Investor)-[:INVESTED_IN]->(c)
        RETURN c.name as company, 
               c.currentValuation as valuation,
               c.entryValuation as entryValuation, 
               c.entryDate as entryDate,
               c.rank as rank,
               s.name as sector, 
               ss.name as subsector,
               collect(DISTINCT l.city) as locations,
               collect(DISTINCT i.name) as investors
        LIMIT 1
        """
        results = self._conn.execute_query(query, {"name": company_name})
        return results[0] if results else None
    
    def get_top_companies(self, limit: int = 10) -> List[Dict]:
        """Get top companies by current valuation"""
        query = """
        MATCH (c:Company)
        WHERE c.currentValuation IS NOT NULL
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
        RETURN c.name as company, 
               c.currentValuation as valuation, 
               s.name as sector
        ORDER BY c.currentValuation DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"limit": limit})
    
    def get_companies_by_valuation_growth(self, limit: int = 10) -> List[Dict]:
        """Get companies with highest valuation growth"""
        query = """
        MATCH (c:Company)
        WHERE c.entryValuation IS NOT NULL AND c.currentValuation IS NOT NULL
        RETURN c.name as company,
               c.entryValuation as entryValuation,
               c.currentValuation as currentValuation,
               round((c.currentValuation / c.entryValuation - 1) * 100) as growthPercent
        ORDER BY growthPercent DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"limit": limit})
    
    # =========================================================================
    # INVESTOR QUERIES
    # =========================================================================
    
    def get_investor_portfolio(self, investor_name: str, limit: int = 20) -> List[Dict]:
        """
        Get all companies an investor has invested in.
        
        Args:
            investor_name: Investor name to search
            limit: Maximum results
            
        Returns:
            List of portfolio companies
        """
        query = """
        MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)
        WHERE toLower(i.name) CONTAINS toLower($name)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
        RETURN i.name as investor, 
               c.name as company, 
               c.currentValuation as valuation, 
               s.name as sector
        ORDER BY c.currentValuation DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"name": investor_name, "limit": limit})
    
    def get_top_investors(self, limit: int = 10) -> List[Dict]:
        """Get most active investors by investment count"""
        query = """
        MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)
        RETURN i.name as investor, 
               count(c) as investments,
               round(sum(c.currentValuation) * 10) / 10 as portfolioValue
        ORDER BY investments DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"limit": limit})
    
    def get_co_investors(self, investor_name: str, limit: int = 10) -> List[Dict]:
        """Find investors who co-invested with a specific investor"""
        query = """
        MATCH (i1:Investor)-[:INVESTED_IN]->(c:Company)<-[:INVESTED_IN]-(i2:Investor)
        WHERE toLower(i1.name) CONTAINS toLower($name) AND i1 <> i2
        RETURN i2.name as coInvestor, 
               count(c) as sharedInvestments,
               collect(c.name)[0..5] as sampleCompanies
        ORDER BY sharedInvestments DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"name": investor_name, "limit": limit})
    
    # =========================================================================
    # SECTOR QUERIES
    # =========================================================================
    
    def get_sector_companies(self, sector_name: str, limit: int = 15) -> List[Dict]:
        """Get companies in a specific sector"""
        query = """
        MATCH (c:Company)-[:OPERATES_IN]->(s:Sector)
        WHERE toLower(s.name) CONTAINS toLower($sector)
        OPTIONAL MATCH (c)-[:SPECIALIZES_IN]->(ss:SubSector)
        RETURN c.name as company, 
               c.currentValuation as valuation,
               ss.name as subsector
        ORDER BY c.currentValuation DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"sector": sector_name, "limit": limit})
    
    def get_sector_stats(self) -> List[Dict]:
        """Get aggregated statistics by sector"""
        query = """
        MATCH (c:Company)-[:OPERATES_IN]->(s:Sector)
        WHERE c.currentValuation IS NOT NULL
        RETURN s.name as sector,
               count(c) as companyCount,
               round(sum(c.currentValuation) * 10) / 10 as totalValuation,
               round(avg(c.currentValuation) * 10) / 10 as avgValuation
        ORDER BY totalValuation DESC
        """
        return self._conn.execute_query(query)
    
    def get_all_sectors(self) -> List[Dict]:
        """Get all sectors with subsectors"""
        query = """
        MATCH (s:Sector)
        OPTIONAL MATCH (s)-[:HAS_SUBSECTOR]->(ss:SubSector)
        RETURN s.name as sector, collect(ss.name) as subsectors
        ORDER BY s.name
        """
        return self._conn.execute_query(query)
    
    # =========================================================================
    # LOCATION QUERIES
    # =========================================================================
    
    def get_city_companies(self, city: str, limit: int = 15) -> List[Dict]:
        """Get companies located in a specific city"""
        query = """
        MATCH (c:Company)-[:LOCATED_IN]->(l:Location)
        WHERE toLower(l.city) CONTAINS toLower($city)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
        RETURN c.name as company, 
               c.currentValuation as valuation, 
               s.name as sector
        ORDER BY c.currentValuation DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"city": city, "limit": limit})
    
    def get_location_stats(self) -> List[Dict]:
        """Get aggregated statistics by location"""
        query = """
        MATCH (c:Company)-[:LOCATED_IN]->(l:Location)
        WHERE c.currentValuation IS NOT NULL
        RETURN l.city as city,
               count(c) as companyCount,
               round(sum(c.currentValuation) * 10) / 10 as totalValuation
        ORDER BY companyCount DESC
        """
        return self._conn.execute_query(query)
    
    # =========================================================================
    # GRAPH STATISTICS
    # =========================================================================
    
    def get_graph_stats(self) -> Dict:
        """Get overall graph statistics"""
        query = """
        MATCH (c:Company) WITH count(c) as companies
        MATCH (i:Investor) WITH companies, count(i) as investors
        MATCH (s:Sector) WITH companies, investors, count(s) as sectors
        MATCH (l:Location) WITH companies, investors, sectors, count(l) as locations
        MATCH ()-[r]->() WITH companies, investors, sectors, locations, count(r) as relationships
        RETURN companies, investors, sectors, locations, relationships
        """
        results = self._conn.execute_query(query)
        return results[0] if results else {}
    
    # =========================================================================
    # SIMILARITY & RECOMMENDATIONS
    # =========================================================================
    
    def find_similar_companies(self, company_name: str, limit: int = 5) -> List[Dict]:
        """Find companies similar to a given company based on shared attributes"""
        query = """
        MATCH (target:Company)
        WHERE toLower(target.name) CONTAINS toLower($name)
        WITH target
        LIMIT 1
        
        OPTIONAL MATCH (target)-[:OPERATES_IN]->(s:Sector)
        OPTIONAL MATCH (target)-[:LOCATED_IN]->(l:Location)
        OPTIONAL MATCH (i:Investor)-[:INVESTED_IN]->(target)
        
        WITH target, s, collect(DISTINCT l) as locations, collect(DISTINCT i) as investors
        
        MATCH (similar:Company)
        WHERE similar <> target
        
        OPTIONAL MATCH (similar)-[:OPERATES_IN]->(s)
        OPTIONAL MATCH (similar)-[:LOCATED_IN]->(sl:Location) WHERE sl IN locations
        OPTIONAL MATCH (si:Investor)-[:INVESTED_IN]->(similar) WHERE si IN investors
        
        WITH similar, 
             CASE WHEN s IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN sl IS NOT NULL THEN 1 ELSE 0 END +
             CASE WHEN si IS NOT NULL THEN 1 ELSE 0 END as score
        WHERE score > 0
        
        RETURN similar.name as company, 
               similar.currentValuation as valuation,
               score as similarityScore
        ORDER BY score DESC, similar.currentValuation DESC
        LIMIT $limit
        """
        return self._conn.execute_query(query, {"name": company_name, "limit": limit})
