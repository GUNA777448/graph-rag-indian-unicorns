"""
Graph RAG Chat Application
Streamlit UI + Neo4j Knowledge Graph + Ollama Mistral
"""

import streamlit as st
import requests
import json
from neo4j import GraphDatabase
from typing import List, Dict, Optional
import time

# =============================================================================
# CONFIGURATION
# =============================================================================
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "GRAPH-RAG"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "mistral"

# =============================================================================
# NEO4J CONNECTION (Cached for performance)
# =============================================================================
@st.cache_resource
def get_neo4j_driver():
    """Create a cached Neo4j driver connection"""
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_cypher(query: str, params: dict = None) -> List[Dict]:
    """Execute Cypher query and return results"""
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]

# =============================================================================
# KNOWLEDGE GRAPH QUERIES (Optimized & Indexed)
# =============================================================================
def search_companies(search_term: str) -> List[Dict]:
    """Search companies by name (case-insensitive)"""
    query = """
    MATCH (c:Company)
    WHERE toLower(c.name) CONTAINS toLower($term)
    OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
    OPTIONAL MATCH (c)-[:LOCATED_IN]->(l:Location)
    RETURN c.name as company, c.currentValuation as valuation, 
           s.name as sector, collect(DISTINCT l.city) as locations
    LIMIT 10
    """
    return run_cypher(query, {"term": search_term})

def get_company_details(company_name: str) -> Dict:
    """Get full details of a company"""
    query = """
    MATCH (c:Company)
    WHERE toLower(c.name) CONTAINS toLower($name)
    OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
    OPTIONAL MATCH (c)-[:SPECIALIZES_IN]->(ss:SubSector)
    OPTIONAL MATCH (c)-[:LOCATED_IN]->(l:Location)
    OPTIONAL MATCH (i:Investor)-[:INVESTED_IN]->(c)
    RETURN c.name as company, c.currentValuation as valuation,
           c.entryValuation as entryValuation, c.entryDate as entryDate,
           s.name as sector, ss.name as subsector,
           collect(DISTINCT l.city) as locations,
           collect(DISTINCT i.name) as investors
    LIMIT 1
    """
    results = run_cypher(query, {"name": company_name})
    return results[0] if results else {}

def get_investor_portfolio(investor_name: str) -> List[Dict]:
    """Get investor's portfolio"""
    query = """
    MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)
    WHERE toLower(i.name) CONTAINS toLower($name)
    OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
    RETURN i.name as investor, c.name as company, 
           c.currentValuation as valuation, s.name as sector
    ORDER BY c.currentValuation DESC
    LIMIT 20
    """
    return run_cypher(query, {"name": investor_name})

def get_sector_companies(sector_name: str) -> List[Dict]:
    """Get companies in a sector"""
    query = """
    MATCH (c:Company)-[:OPERATES_IN]->(s:Sector)
    WHERE toLower(s.name) CONTAINS toLower($sector)
    RETURN c.name as company, c.currentValuation as valuation
    ORDER BY c.currentValuation DESC
    LIMIT 15
    """
    return run_cypher(query, {"sector": sector_name})

def get_city_companies(city: str) -> List[Dict]:
    """Get companies in a city"""
    query = """
    MATCH (c:Company)-[:LOCATED_IN]->(l:Location)
    WHERE toLower(l.city) CONTAINS toLower($city)
    OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
    RETURN c.name as company, c.currentValuation as valuation, s.name as sector
    ORDER BY c.currentValuation DESC
    LIMIT 15
    """
    return run_cypher(query, {"city": city})

def get_graph_stats() -> Dict:
    """Get graph statistics"""
    query = """
    MATCH (c:Company) WITH count(c) as companies
    MATCH (i:Investor) WITH companies, count(i) as investors
    MATCH (s:Sector) WITH companies, investors, count(s) as sectors
    MATCH (l:Location) WITH companies, investors, sectors, count(l) as locations
    RETURN companies, investors, sectors, locations
    """
    results = run_cypher(query)
    return results[0] if results else {}

def get_top_companies(limit: int = 10) -> List[Dict]:
    """Get top companies by valuation"""
    query = """
    MATCH (c:Company)
    WHERE c.currentValuation IS NOT NULL
    OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
    RETURN c.name as company, c.currentValuation as valuation, s.name as sector
    ORDER BY c.currentValuation DESC
    LIMIT $limit
    """
    return run_cypher(query, {"limit": limit})

def get_top_investors(limit: int = 10) -> List[Dict]:
    """Get most active investors"""
    query = """
    MATCH (i:Investor)-[:INVESTED_IN]->(c:Company)
    RETURN i.name as investor, count(c) as investments,
           round(sum(c.currentValuation) * 10) / 10 as portfolioValue
    ORDER BY investments DESC
    LIMIT $limit
    """
    return run_cypher(query, {"limit": limit})

# =============================================================================
# CONTEXT BUILDER (RAG)
# =============================================================================
def build_context(user_query: str) -> str:
    """Build context from KG based on user query"""
    context_parts = []
    query_lower = user_query.lower()
    
    # Extract potential entity mentions
    keywords = [w.strip("?,.'\"") for w in user_query.split() if len(w) > 2]
    
    # Search for companies mentioned
    for kw in keywords:
        if len(kw) > 3:
            companies = search_companies(kw)
            if companies:
                for comp in companies[:3]:
                    details = get_company_details(comp['company'])
                    if details:
                        context_parts.append(
                            f"Company: {details.get('company', 'N/A')}\n"
                            f"  Sector: {details.get('sector', 'N/A')}\n"
                            f"  Valuation: ${details.get('valuation', 'N/A')}B\n"
                            f"  Locations: {', '.join(details.get('locations', []))}\n"
                            f"  Investors: {', '.join(details.get('investors', [])[:5])}"
                        )
    
    # Check for investor queries
    investor_keywords = ["investor", "invested", "portfolio", "fund", "vc", "capital"]
    if any(kw in query_lower for kw in investor_keywords):
        for kw in keywords:
            if len(kw) > 3:
                portfolio = get_investor_portfolio(kw)
                if portfolio:
                    inv_name = portfolio[0]['investor']
                    companies = [f"{p['company']} (${p['valuation']}B)" for p in portfolio[:5]]
                    context_parts.append(
                        f"Investor: {inv_name}\n"
                        f"  Portfolio: {', '.join(companies)}"
                    )
    
    # Check for sector queries
    sector_keywords = ["sector", "industry", "fintech", "edtech", "ecommerce", "e-commerce", "saas"]
    if any(kw in query_lower for kw in sector_keywords):
        for kw in keywords:
            sector_companies = get_sector_companies(kw)
            if sector_companies:
                companies = [f"{c['company']} (${c['valuation']}B)" for c in sector_companies[:5]]
                context_parts.append(
                    f"Sector '{kw}' companies: {', '.join(companies)}"
                )
    
    # Check for location queries
    city_keywords = ["bangalore", "mumbai", "delhi", "gurgaon", "pune", "chennai", "hyderabad", "city", "located"]
    if any(kw in query_lower for kw in city_keywords):
        for kw in keywords:
            city_companies = get_city_companies(kw)
            if city_companies:
                companies = [f"{c['company']} ({c['sector']})" for c in city_companies[:5]]
                context_parts.append(
                    f"Companies in {kw}: {', '.join(companies)}"
                )
    
    # Add top companies if asking about top/best/highest
    if any(kw in query_lower for kw in ["top", "best", "highest", "largest", "biggest"]):
        top_companies = get_top_companies(5)
        companies = [f"{c['company']} (${c['valuation']}B - {c['sector']})" for c in top_companies]
        context_parts.append(f"Top Unicorns by Valuation: {', '.join(companies)}")
    
    # Default context if nothing found
    if not context_parts:
        stats = get_graph_stats()
        top = get_top_companies(5)
        top_str = ', '.join([f"{c['company']} (${c['valuation']}B)" for c in top])
        context_parts.append(
            f"Indian Unicorn Startups Database:\n"
            f"  Total Companies: {stats.get('companies', 'N/A')}\n"
            f"  Total Investors: {stats.get('investors', 'N/A')}\n"
            f"  Sectors: {stats.get('sectors', 'N/A')}\n"
            f"  Top 5 by Valuation: {top_str}"
        )
    
    return "\n\n".join(context_parts)

# =============================================================================
# OLLAMA INTEGRATION
# =============================================================================
def query_ollama(prompt: str, context: str) -> str:
    """Query Ollama with context"""
    system_prompt = """You are an expert analyst for Indian Unicorn Startups. 
Use the provided context from the knowledge graph to answer questions accurately.
Be concise and specific. If data is not in context, say so.
Format numbers nicely (e.g., $5.6B for valuation)."""

    full_prompt = f"""Context from Knowledge Graph:
{context}

User Question: {prompt}

Answer based on the context above:"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": full_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 500
                }
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get("response", "No response generated.")
        else:
            return f"Error: Ollama returned status {response.status_code}"
    
    except requests.exceptions.ConnectionError:
        return "⚠️ Cannot connect to Ollama. Make sure it's running: `ollama serve`"
    except Exception as e:
        return f"Error: {str(e)}"

# =============================================================================
# STREAMLIT UI
# =============================================================================
def main():
    # Page config
    st.set_page_config(
        page_title="Indian Unicorns Graph RAG",
        page_icon="🦄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: #1a1a1a !important;
    }
    .chat-message * {
        color: #1a1a1a !important;
    }
    .user-message {
        background-color: #d4edfc !important;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #e8d5f0 !important;
        border-left: 4px solid #9c27b0;
    }
    .context-box {
        background-color: #ffecd2 !important;
        padding: 1rem;
        border-radius: 8px;
        font-size: 0.85rem;
        border-left: 4px solid #ff9800;
        color: #333 !important;
    }
    .context-box * {
        color: #333 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<p class="main-header">🦄 Indian Unicorns Graph RAG</p>', unsafe_allow_html=True)
    st.markdown("*Chat with the Knowledge Graph of 102 Indian Unicorn Startups*")
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # Connection status
        try:
            stats = get_graph_stats()
            st.success("✅ Neo4j Connected")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Companies", stats.get('companies', 0))
                st.metric("Sectors", stats.get('sectors', 0))
            with col2:
                st.metric("Investors", stats.get('investors', 0))
                st.metric("Locations", stats.get('locations', 0))
        except Exception as e:
            st.error("❌ Neo4j not connected")
            st.caption(str(e))
        
        # Ollama status
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            if r.status_code == 200:
                st.success("✅ Ollama Connected")
            else:
                st.warning("⚠️ Ollama issue")
        except:
            st.error("❌ Ollama not running")
            st.caption("Run: `ollama serve`")
        
        st.markdown("---")
        st.markdown("### 💡 Sample Questions")
        sample_questions = [
            "Tell me about Flipkart",
            "Which companies has Tiger Global invested in?",
            "List top 5 Fintech unicorns",
            "Companies located in Bangalore",
            "Compare CRED and PhonePe",
            "Who are the top investors?",
        ]
        for q in sample_questions:
            if st.button(q, key=f"sample_{q}", use_container_width=True):
                st.session_state.sample_query = q
        
        st.markdown("---")
        show_context = st.checkbox("Show retrieved context", value=False)
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Main chat area
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-message user-message">🧑 **You:** {msg["content"]}</div>', 
                           unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message">🤖 **Assistant:** {msg["content"]}</div>', 
                           unsafe_allow_html=True)
                if show_context and "context" in msg:
                    with st.expander("📊 Retrieved Context"):
                        st.markdown(f'<div class="context-box">{msg["context"]}</div>', 
                                   unsafe_allow_html=True)
    
    # Chat input
    if "sample_query" in st.session_state:
        user_input = st.session_state.sample_query
        del st.session_state.sample_query
        st.session_state.process_query = user_input
        st.rerun()
    
    user_input = st.chat_input("Ask about Indian Unicorn Startups...")
    
    if "process_query" in st.session_state:
        user_input = st.session_state.process_query
        del st.session_state.process_query
    
    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get context and response
        with st.spinner("🔍 Searching knowledge graph..."):
            start_time = time.time()
            context = build_context(user_input)
            kg_time = time.time() - start_time
        
        with st.spinner("🤔 Generating response..."):
            start_time = time.time()
            response = query_ollama(user_input, context)
            llm_time = time.time() - start_time
        
        # Add assistant message
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "context": context
        })
        
        # Show latency
        st.caption(f"⚡ KG: {kg_time:.2f}s | LLM: {llm_time:.2f}s")
        
        st.rerun()
    
    # Quick stats at bottom
    if not st.session_state.messages:
        st.markdown("---")
        st.markdown("### 🏆 Top Unicorns by Valuation")
        
        try:
            top_companies = get_top_companies(10)
            cols = st.columns(5)
            for i, comp in enumerate(top_companies[:5]):
                with cols[i]:
                    st.markdown(f"""
                    <div class="stat-card">
                        <div class="stat-number">${comp['valuation']}B</div>
                        <div class="stat-label">{comp['company'][:15]}</div>
                    </div>
                    """, unsafe_allow_html=True)
        except:
            st.info("Connect to Neo4j to see statistics")

if __name__ == "__main__":
    main()
