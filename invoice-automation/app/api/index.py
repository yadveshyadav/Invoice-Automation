"""
Vercel serverless function entry point for FastAPI app.
"""

import sys
from pathlib import Path

# Add both app directory and the parent directory to path so package imports work.
api_dir = Path(__file__).resolve().parent
app_dir = api_dir.parent
repo_root = app_dir.parent
for path in (app_dir, repo_root):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Import the FastAPI app from main.py
from main import app

# Export for Vercel
__all__ = ['app']


