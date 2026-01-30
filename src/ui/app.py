"""
Main Streamlit Application
Entry point for the Graph RAG UI
"""

import streamlit as st
import time
from typing import Optional

from src.config import get_settings
from src.database import GraphQueries, get_connection
from src.llm import get_ollama_client
from src.rag import ContextBuilder
from .styles import get_custom_css
from .components import (
    render_sidebar,
    render_chat,
    render_stats_dashboard,
    render_chat_message
)


def initialize_session_state() -> None:
    """Initialize Streamlit session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "sample_query" not in st.session_state:
        st.session_state.sample_query = None


def check_connections() -> tuple:
    """
    Check Neo4j and Ollama connections.
    
    Returns:
        Tuple of (neo4j_connected, ollama_connected, graph_stats)
    """
    neo4j_connected = False
    ollama_connected = False
    graph_stats = None
    
    # Check Neo4j
    try:
        conn = get_connection()
        neo4j_connected = conn.verify_connectivity()
        if neo4j_connected:
            queries = GraphQueries()
            graph_stats = queries.get_graph_stats()
    except Exception:
        pass
    
    # Check Ollama
    try:
        client = get_ollama_client()
        ollama_connected = client.is_available()
    except Exception:
        pass
    
    return neo4j_connected, ollama_connected, graph_stats


def process_query(user_input: str) -> dict:
    """
    Process a user query through the RAG pipeline.
    
    Args:
        user_input: User's question
        
    Returns:
        Dict with response, context, and timing info
    """
    # Build context from KG
    context_builder = ContextBuilder()
    start_time = time.time()
    retrieval_result = context_builder.build_context(user_input)
    kg_time = time.time() - start_time
    
    # Generate response from LLM
    client = get_ollama_client()
    start_time = time.time()
    llm_response = client.generate(user_input, retrieval_result.context)
    llm_time = time.time() - start_time
    
    # Prepare response
    if llm_response.success:
        response = llm_response.content
    else:
        response = f"⚠️ {llm_response.error}"
    
    timing_info = f"⚡ KG: {kg_time:.2f}s | LLM: {llm_time:.2f}s | Entities: {retrieval_result.entities_found}"
    
    return {
        "response": response,
        "context": retrieval_result.context,
        "timing_info": timing_info,
        "kg_time": kg_time,
        "llm_time": llm_time
    }


def run_app() -> None:
    """Main application entry point"""
    settings = get_settings()
    
    # Page configuration
    st.set_page_config(
        page_title=settings.ui.page_title,
        page_icon=settings.ui.page_icon,
        layout=settings.ui.layout,
        initial_sidebar_state=settings.ui.initial_sidebar_state
    )
    
    # Apply custom CSS
    st.markdown(get_custom_css(), unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Check connections
    neo4j_connected, ollama_connected, graph_stats = check_connections()
    
    # Header
    st.markdown(
        '<p class="main-header">🦄 Indian Unicorns Graph RAG</p>',
        unsafe_allow_html=True
    )
    st.markdown("*Chat with the Knowledge Graph of 102 Indian Unicorn Startups*")
    
    # Sidebar
    sidebar_settings = render_sidebar(
        graph_stats=graph_stats,
        neo4j_connected=neo4j_connected,
        ollama_connected=ollama_connected
    )
    
    # Main chat area
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        render_chat(
            st.session_state.messages,
            show_context=sidebar_settings.get("show_context", False)
        )
    
    # Handle sample query from sidebar
    if st.session_state.sample_query:
        user_input = st.session_state.sample_query
        st.session_state.sample_query = None
        st.session_state.process_query = user_input
        st.rerun()
    
    # Chat input
    user_input = st.chat_input("Ask about Indian Unicorn Startups...")
    
    # Process pending query from sample button
    if "process_query" in st.session_state:
        user_input = st.session_state.process_query
        del st.session_state.process_query
    
    if user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Process query
        if neo4j_connected and ollama_connected:
            with st.spinner("🔍 Searching knowledge graph..."):
                result = process_query(user_input)
            
            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["response"],
                "context": result["context"],
                "timing_info": result["timing_info"] if sidebar_settings.get("show_timing") else None
            })
        else:
            error_msg = []
            if not neo4j_connected:
                error_msg.append("Neo4j not connected")
            if not ollama_connected:
                error_msg.append("Ollama not running")
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"⚠️ Cannot process query: {', '.join(error_msg)}"
            })
        
        st.rerun()
    
    # Show dashboard if no messages
    if not st.session_state.messages and neo4j_connected:
        try:
            queries = GraphQueries()
            top_companies = queries.get_top_companies(10)
            render_stats_dashboard(top_companies)
        except Exception:
            pass


if __name__ == "__main__":
    run_app()
