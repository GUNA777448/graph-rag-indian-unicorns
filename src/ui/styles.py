"""
Custom CSS Styles for Streamlit UI
Provides consistent theming and styling
"""


def get_custom_css() -> str:
    """Get custom CSS for the Streamlit app"""
    return """
    <style>
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    
    /* Stat cards */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    
    /* Chat messages */
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
    
    /* Context box */
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
    
    /* Status indicators */
    .status-connected {
        color: #4caf50;
        font-weight: bold;
    }
    
    .status-disconnected {
        color: #f44336;
        font-weight: bold;
    }
    
    /* Sample question buttons */
    .sample-btn {
        background-color: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .sample-btn:hover {
        background-color: #e0e0e0;
        border-color: #667eea;
    }
    
    /* Metrics */
    .metric-container {
        background-color: #f8f9fa;
        padding: 0.75rem;
        border-radius: 8px;
        text-align: center;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #888;
        font-size: 0.8rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #eee;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Improve scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    </style>
    """


def get_loading_spinner_css() -> str:
    """Get CSS for custom loading spinner"""
    return """
    <style>
    .loader {
        border: 4px solid #f3f3f3;
        border-top: 4px solid #667eea;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """
