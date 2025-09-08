"""
Environment and configuration management.

Responsibilities:
- Load environment variables from `.env` if present.
- Expose constants used across the application.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

# Load variables from .env into the process environment if present
load_dotenv()

# API configuration
STOCK_API_BASE: str = os.getenv("STOCK_API_BASE", "https://stockdata-api-6xok.onrender.com/")
API_KEY: str = os.getenv("API_KEY", "")  # Reserved for future use

# Fixed values
TIMEOUT: int = 30  # seconds
MAX_TICKERS: int = 5

