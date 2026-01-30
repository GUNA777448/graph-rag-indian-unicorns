"""
Graph RAG for Indian Unicorn Startups
Main entry point for the application
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.ui import run_app


if __name__ == "__main__":
    run_app()
