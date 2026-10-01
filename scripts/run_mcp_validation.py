"""
Start the Validation MCP server (stdio by default).

Prerequisites:
  1. venv activated
  2. Validation FastAPI running at VALIDATION_API_BASE_URL

Usage:
  python scripts/run_mcp_validation.py
  # or: python -m mcp_validation
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp_validation.server import main

if __name__ == "__main__":
    main()
