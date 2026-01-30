"""
Knowledge Graph Builder for Indian Unicorn Startups Dataset
Builds a Neo4j graph with Companies, Sectors, Locations, and Investors
"""

import pandas as pd
from neo4j import GraphDatabase
import re

# Neo4j Connection Configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "GRAPH-RAG"  # Change this to your Neo4j password

class UnicornKnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear all existing nodes and relationships"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Database cleared.")
    
    def create_constraints(self):
        """Create uniqueness constraints for better performance"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (ss:SubSector) REQUIRE ss.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.city IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Investor) REQUIRE i.name IS UNIQUE",
        ]
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    print(f"Constraint may already exist: {e}")
        print("Constraints created.")
    
    def parse_sector(self, sector_str):
        """Parse sector string into main sector and sub-sector"""
        if pd.isna(sector_str):
            return None, None
        
        if " - " in sector_str:
            parts = sector_str.split(" - ", 1)
            return parts[0].strip(), parts[1].strip()
        return sector_str.strip(), None
    
    def parse_locations(self, location_str):
        """Parse location string into list of cities"""
        if pd.isna(location_str):
            return []
        
        # Split by "/" and clean up
        locations = [loc.strip() for loc in location_str.split("/")]
        return locations
    
    def parse_investors(self, investors_str):
        """Parse investors string into list of investor names"""
        if pd.isna(investors_str):
            return []
        
        # Remove quotes and split by comma
        investors_str = investors_str.strip('"')
        investors = [inv.strip() for inv in investors_str.split(",")]
        return [inv for inv in investors if inv]  # Remove empty strings
    
    def parse_valuation(self, val):
        """Parse valuation to float"""
        if pd.isna(val):
            return None
        try:
            return float(val)
        except:
            return None
    
    def parse_entry_date(self, entry_str):
        """Parse entry date string"""
        if pd.isna(entry_str):
            return None
        return str(entry_str).strip()
    
    def load_data(self, csv_path):
        """Load and process the CSV data"""
        df = pd.read_csv(csv_path)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        print(f"Loaded {len(df)} companies from CSV")
        print(f"Columns: {list(df.columns)}")
        
        return df
    
    def build_graph(self, df):
        """Build the knowledge graph from dataframe"""
        with self.driver.session() as session:
            for _, row in df.iterrows():
                # Extract data
                company_name = str(row['Company']).strip()
                rank = int(row['No.']) if pd.notna(row['No.']) else None
                entry_val = self.parse_valuation(row['Entry Valuation^^ ($B)'])
                current_val = self.parse_valuation(row['Valuation ($B)'])
                entry_date = self.parse_entry_date(row['Entry'])
                
                sector, subsector = self.parse_sector(row['Sector'])
                locations = self.parse_locations(row['Location'])
                investors = self.parse_investors(row['Select Investors'])
                
                # Create Company node
                session.run("""
                    MERGE (c:Company {name: $name})
                    SET c.rank = $rank,
                        c.entryValuation = $entry_val,
                        c.currentValuation = $current_val,
                        c.entryDate = $entry_date
                """, name=company_name, rank=rank, entry_val=entry_val, 
                    current_val=current_val, entry_date=entry_date)
                
                # Create Sector and relationship
                if sector:
                    session.run("""
                        MERGE (s:Sector {name: $sector})
                        WITH s
                        MATCH (c:Company {name: $company})
                        MERGE (c)-[:OPERATES_IN]->(s)
                    """, sector=sector, company=company_name)
                    
                    # Create SubSector and relationships
                    if subsector:
                        session.run("""
                            MERGE (ss:SubSector {name: $subsector})
                            WITH ss
                            MATCH (c:Company {name: $company})
                            MERGE (c)-[:SPECIALIZES_IN]->(ss)
                            WITH ss
                            MATCH (s:Sector {name: $sector})
                            MERGE (s)-[:HAS_SUBSECTOR]->(ss)
                        """, subsector=subsector, company=company_name, sector=sector)
                
                # Create Location nodes and relationships
                for location in locations:
                    session.run("""
                        MERGE (l:Location {city: $city})
                        WITH l
                        MATCH (c:Company {name: $company})
                        MERGE (c)-[:LOCATED_IN]->(l)
                    """, city=location, company=company_name)
                
                # Create Investor nodes and relationships
                for investor in investors:
                    session.run("""
                        MERGE (i:Investor {name: $investor})
                        WITH i
                        MATCH (c:Company {name: $company})
                        MERGE (i)-[:INVESTED_IN]->(c)
                    """, investor=investor, company=company_name)
                
                print(f"Processed: {company_name}")
        
        print("\nGraph building complete!")
    
    def get_statistics(self):
        """Get statistics about the graph"""
        with self.driver.session() as session:
            stats = {}
            
            # Count nodes by label
            result = session.run("MATCH (c:Company) RETURN count(c) as count")
            stats['companies'] = result.single()['count']
            
            result = session.run("MATCH (s:Sector) RETURN count(s) as count")
            stats['sectors'] = result.single()['count']
            
            result = session.run("MATCH (ss:SubSector) RETURN count(ss) as count")
            stats['subsectors'] = result.single()['count']
            
            result = session.run("MATCH (l:Location) RETURN count(l) as count")
            stats['locations'] = result.single()['count']
            
            result = session.run("MATCH (i:Investor) RETURN count(i) as count")
            stats['investors'] = result.single()['count']
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            stats['relationships'] = result.single()['count']
            
            return stats


def main():
    # Path to CSV file
    csv_path = "Indian Unicorn startups 2023 updated.csv"
    
    print("=" * 60)
    print("Indian Unicorn Startups Knowledge Graph Builder")
    print("=" * 60)
    
    # Initialize connection
    kg = UnicornKnowledgeGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Clear existing data (optional - comment out to append)
        print("\n1. Clearing existing database...")
        kg.clear_database()
        
        # Create constraints
        print("\n2. Creating constraints...")
        kg.create_constraints()
        
        # Load CSV data
        print("\n3. Loading CSV data...")
        df = kg.load_data(csv_path)
        
        # Build the graph
        print("\n4. Building knowledge graph...")
        kg.build_graph(df)
        
        # Get statistics
        print("\n5. Graph Statistics:")
        stats = kg.get_statistics()
        print(f"   - Companies: {stats['companies']}")
        print(f"   - Sectors: {stats['sectors']}")
        print(f"   - SubSectors: {stats['subsectors']}")
        print(f"   - Locations: {stats['locations']}")
        print(f"   - Investors: {stats['investors']}")
        print(f"   - Total Relationships: {stats['relationships']}")
        
        print("\n" + "=" * 60)
        print("Knowledge Graph built successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure Neo4j is running and credentials are correct.")
    
    finally:
        kg.close()


if __name__ == "__main__":
    main()
