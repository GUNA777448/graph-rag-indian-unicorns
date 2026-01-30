// ============================================================
// SAMPLE CYPHER QUERIES FOR INDIAN UNICORN STARTUPS KG
// ============================================================
// ------------------------------------------------------------
// BASIC EXPLORATION QUERIES
// ------------------------------------------------------------
// View all node labels and counts
CALL db.labels() YIELD label
CALL
  apoc.cypher.run(
    'MATCH (n:`' + label + '`) RETURN count(n) as count',
    {}
  )
  YIELD value
RETURN label, value.count AS count;

// Simple version - count all nodes by type
MATCH (n)
RETURN labels(n)[0] AS NodeType, count(n) AS Count
ORDER BY Count DESC;

// View all relationship types
MATCH ()-[r]->()
RETURN type(r) AS RelationshipType, count(r) AS Count
ORDER BY Count DESC;

// ------------------------------------------------------------
// COMPANY QUERIES
// ------------------------------------------------------------

// Get all companies with their valuations
MATCH (c:Company)
RETURN
  c.name AS Company,
  c.entryValuation AS EntryValuation,
  c.currentValuation AS CurrentValuation,
  c.entryDate AS EntryDate
ORDER BY c.currentValuation DESC
LIMIT 20;

// Top 10 companies by current valuation
MATCH (c:Company)
WHERE c.currentValuation IS NOT NULL
RETURN c.name AS Company, c.currentValuation AS Valuation
ORDER BY c.currentValuation DESC
LIMIT 10;

// Companies that increased valuation the most
MATCH (c:Company)
WHERE c.entryValuation IS NOT NULL AND c.currentValuation IS NOT NULL
RETURN
  c.name AS Company,
  c.entryValuation AS Entry,
  c.currentValuation AS Current,
  c.currentValuation - c.entryValuation AS Increase,
  round((c.currentValuation / c.entryValuation - 1) * 100) AS PercentGrowth
ORDER BY PercentGrowth DESC
LIMIT 10;

// ------------------------------------------------------------
// SECTOR ANALYSIS
// ------------------------------------------------------------

// Companies per sector
MATCH (c:Company)-[:OPERATES_IN]->(s:Sector)
RETURN s.name AS Sector, count(c) AS CompanyCount
ORDER BY CompanyCount DESC;

// Total valuation by sector
MATCH (c:Company)-[:OPERATES_IN]->(s:Sector)
WHERE c.currentValuation IS NOT NULL
RETURN
  s.name AS Sector,
  count(c) AS Companies,
  round(sum(c.currentValuation) * 10) / 10 AS TotalValuation,
  round(avg(c.currentValuation) * 10) / 10 AS AvgValuation
ORDER BY TotalValuation DESC;

// Sectors with their sub-sectors
MATCH (s:Sector)-[:HAS_SUBSECTOR]->(ss:SubSector)
RETURN s.name AS Sector, collect(ss.name) AS SubSectors;

// Companies in Fintech sector with sub-sectors
MATCH (c:Company)-[:OPERATES_IN]->(s:Sector {name: 'Fintech'})
OPTIONAL MATCH (c)-[:SPECIALIZES_IN]->(ss:SubSector)
RETURN c.name AS Company, ss.name AS SubSector, c.currentValuation AS Valuation
ORDER BY c.currentValuation DESC;

// ------------------------------------------------------------
// LOCATION ANALYSIS
// ------------------------------------------------------------

// Companies per city
MATCH (c:Company)-[:LOCATED_IN]->(l:Location)
RETURN l.city AS City, count(c) AS CompanyCount
ORDER BY CompanyCount DESC;

// Total valuation by city
MATCH (c:Company)-[:LOCATED_IN]->(l:Location)
WHERE c.currentValuation IS NOT NULL
RETURN
  l.city AS City,
  count(c) AS Companies,
  round(sum(c.currentValuation) * 10) / 10 AS TotalValuation
ORDER BY TotalValuation DESC;

// Companies with multiple locations (international presence)
MATCH (c:Company)-[:LOCATED_IN]->(l:Location)
WITH c, collect(l.city) AS cities
WHERE size(cities) > 1
RETURN c.name AS Company, cities AS Locations;

// ------------------------------------------------------------
// INVESTOR ANALYSIS
// ------------------------------------------------------------

// Most active investors (by number of investments)
MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)
RETURN i.name AS Investor, count(c) AS Investments
ORDER BY Investments DESC
LIMIT 20;

// Investors' portfolio value
MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)
WHERE c.currentValuation IS NOT NULL
RETURN
  i.name AS Investor,
  count(c) AS Companies,
  collect(c.name) AS Portfolio,
  round(sum(c.currentValuation) * 10) / 10 AS TotalPortfolioValue
ORDER BY TotalPortfolioValue DESC
LIMIT 15;

// Tiger Global's investments
MATCH (i:Investor {name: 'Tiger Global'})-[:INVESTED_IN]->(c:Company)
RETURN c.name AS Company, c.currentValuation AS Valuation
ORDER BY c.currentValuation DESC;

// SoftBank's investments
MATCH (i:Investor {name: 'SoftBank'})-[:INVESTED_IN]->(c:Company)
RETURN c.name AS Company, c.currentValuation AS Valuation
ORDER BY c.currentValuation DESC;

// Sequoia Capital India's portfolio
MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)
WHERE i.name CONTAINS 'Sequoia'
RETURN i.name AS Investor, c.name AS Company, c.currentValuation AS Valuation
ORDER BY c.currentValuation DESC;

// ------------------------------------------------------------
// CO-INVESTMENT ANALYSIS
// ------------------------------------------------------------

// Find co-investors (investors who invested together)
MATCH (i1:Investor)-[:INVESTED_IN]->(c:Company)<-[:INVESTED_IN]-(i2:Investor)
WHERE i1.name < i2.name
RETURN i1.name AS Investor1, i2.name AS Investor2, count(c) AS SharedInvestments
ORDER BY SharedInvestments DESC
LIMIT 20;

// Companies with Tiger Global and Sequoia co-investment
MATCH
  (i1:Investor {name: 'Tiger Global'})-[:INVESTED_IN]->
  (c:Company)<-[:INVESTED_IN]-
  (i2:Investor)
WHERE i2.name CONTAINS 'Sequoia'
RETURN c.name AS Company, c.currentValuation AS Valuation;

// ------------------------------------------------------------
// PATH QUERIES
// ------------------------------------------------------------

// Find all paths from Tiger Global to Bangalore
MATCH
  path =
    (i:Investor {name: 'Tiger Global'})-[:INVESTED_IN]->
    (c:Company)-[:LOCATED_IN]->
    (l:Location {city: 'Bangalore'})
RETURN path;

// Shortest path between two investors through companies
MATCH
  path =
    SHORTESTPATH
    (
    (i1:Investor {name: 'Tiger Global'})-[*]-
    (i2:Investor {name: 'SoftBank'}))
RETURN path;

// ------------------------------------------------------------
// GRAPH PATTERNS
// ------------------------------------------------------------

// Find all Fintech companies in Bangalore with their investors
MATCH
  (i:Investor)-[:INVESTED_IN]->
  (c:Company)-[:OPERATES_IN]->
  (s:Sector {name: 'Fintech'})
MATCH (c)-[:LOCATED_IN]->(l:Location {city: 'Bangalore'})
RETURN c.name AS Company, collect(DISTINCT i.name) AS Investors;

// E-commerce companies with their locations and investors
MATCH (c:Company)-[:OPERATES_IN]->(s:Sector {name: 'E-Commerce'})
MATCH (c)-[:LOCATED_IN]->(l:Location)
OPTIONAL MATCH (i:Investor)-[:INVESTED_IN]->(c)
RETURN
  c.name AS Company,
  collect(DISTINCT l.city) AS Locations,
  collect(DISTINCT i.name) AS Investors;

// ------------------------------------------------------------
// AGGREGATION QUERIES
// ------------------------------------------------------------

// Yearly unicorn entries
MATCH (c:Company)
WHERE c.entryDate IS NOT NULL
WITH c, split(c.entryDate, '/')[1] AS year
RETURN year AS Year, count(c) AS NewUnicorns
ORDER BY Year;

// Investors by sector preference
MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)-[:OPERATES_IN]->(s:Sector)
RETURN i.name AS Investor, s.name AS Sector, count(c) AS Investments
ORDER BY i.name, Investments DESC;

// ------------------------------------------------------------
// RECOMMENDATION QUERIES
// ------------------------------------------------------------

// Companies similar to CRED (same investors, same sector, same location)
MATCH (target:Company {name: 'CRED'})-[:OPERATES_IN]->(s:Sector)
MATCH (target)-[:LOCATED_IN]->(l:Location)
MATCH (i:Investor)-[:INVESTED_IN]->(target)
MATCH (similar:Company)
WHERE
  similar <> target AND
  ((similar)-[:OPERATES_IN]->(s) OR
    (similar)-[:LOCATED_IN]->(l) OR
    (i)-[:INVESTED_IN]->(similar))
WITH similar, count(*) AS similarity
RETURN similar.name AS Company, similarity AS SimilarityScore
ORDER BY similarity DESC
LIMIT 10;

// Find companies that share multiple investors with Flipkart
MATCH
  (target:Company {name: 'Flipkart^'})<-[:INVESTED_IN]-
  (i:Investor)-[:INVESTED_IN]->
  (other:Company)
WHERE other <> target
RETURN
  other.name AS Company,
  collect(i.name) AS SharedInvestors,
  count(i) AS CommonInvestors
ORDER BY CommonInvestors DESC
LIMIT 10;

// ------------------------------------------------------------
// VISUALIZATION QUERIES (for Neo4j Browser)
// ------------------------------------------------------------

// Visualize top investors and their investments
MATCH (i:Investor)-[r:INVESTED_IN]->(c:Company)
WITH i, count(r) AS investments
WHERE investments >= 5
MATCH (i)-[:INVESTED_IN]->(c:Company)
RETURN i, c
LIMIT 100;

// Visualize sector ecosystem
MATCH (s:Sector)-[:HAS_SUBSECTOR]->(ss:SubSector)
MATCH (c:Company)-[:OPERATES_IN]->(s)
OPTIONAL MATCH (c)-[:SPECIALIZES_IN]->(ss)
RETURN s, ss, c
LIMIT 100;

// Full graph for a specific company
MATCH (c:Company {name: 'Flipkart^'})
OPTIONAL MATCH (c)-[r1]-(n1)
OPTIONAL MATCH (n1)-[r2]-(n2)
RETURN c, r1, n1, r2, n2;