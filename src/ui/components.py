"""
Streamlit UI Components
Modular components for the Graph RAG interface
"""

import streamlit as st
from typing import List, Dict, Optional, Callable

from src.database import GraphQueries
from src.llm import get_ollama_client
from src.config import get_settings


def render_sidebar(
    graph_stats: Optional[Dict] = None,
    neo4j_connected: bool = False,
    ollama_connected: bool = False,
    on_sample_question: Optional[Callable[[str], None]] = None
) -> Dict:
    """
    Render the sidebar with settings and sample questions.
    
    Args:
        graph_stats: Optional graph statistics
        neo4j_connected: Neo4j connection status
        ollama_connected: Ollama connection status
        on_sample_question: Callback for sample question clicks
        
    Returns:
        Dict with sidebar settings
    """
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        
        # Connection status
        st.markdown("#### Connection Status")
        
        if neo4j_connected:
            st.success("✅ Neo4j Connected")
            if graph_stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Companies", graph_stats.get('companies', 0))
                    st.metric("Sectors", graph_stats.get('sectors', 0))
                with col2:
                    st.metric("Investors", graph_stats.get('investors', 0))
                    st.metric("Locations", graph_stats.get('locations', 0))
        else:
            st.error("❌ Neo4j not connected")
            st.caption("Check connection settings")
        
        if ollama_connected:
            st.success("✅ Ollama Connected")
        else:
            st.error("❌ Ollama not running")
            st.caption("Run: `ollama serve`")
        
        st.markdown("---")
        
        # Sample questions
        st.markdown("### 💡 Sample Questions")
        
        sample_questions = [
            "Tell me about Flipkart",
            "Which companies has Tiger Global invested in?",
            "List top 5 Fintech unicorns",
            "Companies located in Bangalore",
            "Compare CRED and PhonePe",
            "Who are the top investors?",
            "Show me EdTech companies",
            "What is the total valuation by sector?",
        ]
        
        for q in sample_questions:
            if st.button(q, key=f"sample_{q}", use_container_width=True):
                if on_sample_question:
                    on_sample_question(q)
                else:
                    st.session_state.sample_query = q
        
        st.markdown("---")
        
        # Settings
        show_context = st.checkbox("Show retrieved context", value=False)
        show_timing = st.checkbox("Show timing info", value=True)
        
        return {
            "show_context": show_context,
            "show_timing": show_timing
        }


def render_chat_message(
    role: str,
    content: str,
    context: Optional[str] = None,
    show_context: bool = False,
    timing_info: Optional[str] = None
) -> None:
    """
    Render a single chat message.
    
    Args:
        role: 'user' or 'assistant'
        content: Message content
        context: Optional retrieved context
        show_context: Whether to show context
        timing_info: Optional timing information
    """
    if role == "user":
        st.markdown(
            f'<div class="chat-message user-message">🧑 **You:** {content}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div class="chat-message assistant-message">🤖 **Assistant:** {content}</div>',
            unsafe_allow_html=True
        )
        
        if show_context and context:
            with st.expander("📊 Retrieved Context"):
                st.markdown(
                    f'<div class="context-box"><pre>{context}</pre></div>',
                    unsafe_allow_html=True
                )
        
        if timing_info:
            st.caption(timing_info)


def render_chat(
    messages: List[Dict],
    show_context: bool = False
) -> None:
    """
    Render the chat message history.
    
    Args:
        messages: List of message dictionaries
        show_context: Whether to show context for assistant messages
    """
    for msg in messages:
        render_chat_message(
            role=msg["role"],
            content=msg["content"],
            context=msg.get("context"),
            show_context=show_context,
            timing_info=msg.get("timing_info")
        )


def render_stats_dashboard(top_companies: List[Dict]) -> None:
    """
    Render the statistics dashboard with top companies.
    
    Args:
        top_companies: List of top companies by valuation
    """
    st.markdown("---")
    st.markdown("### 🏆 Top Unicorns by Valuation")
    
    if not top_companies:
        st.info("Connect to Neo4j to see statistics")
        return
    
    # Display top 5 as cards
    cols = st.columns(5)
    for i, comp in enumerate(top_companies[:5]):
        with cols[i]:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">${comp['valuation']}B</div>
                <div class="stat-label">{comp['company'][:15]}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Display rest as table
    if len(top_companies) > 5:
        st.markdown("#### More Top Companies")
        remaining = top_companies[5:10]
        for i, comp in enumerate(remaining, 6):
            st.markdown(f"{i}. **{comp['company']}** - ${comp['valuation']}B ({comp.get('sector', 'N/A')})")


def render_error_message(error: str, error_type: str = "error") -> None:
    """
    Render an error message with appropriate styling.
    
    Args:
        error: Error message
        error_type: 'error', 'warning', or 'info'
    """
    if error_type == "error":
        st.error(f"❌ {error}")
    elif error_type == "warning":
        st.warning(f"⚠️ {error}")
    else:
        st.info(f"ℹ️ {error}")


def render_loading_state(message: str = "Processing...") -> None:
    """Render a loading state"""
    with st.spinner(message):
        pass
