"""
API configuration for Nifty100 Financial Intelligence.
"""

from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parents[2]

# SQLite database
DB_PATH = BASE_DIR / "nifty100.db"
