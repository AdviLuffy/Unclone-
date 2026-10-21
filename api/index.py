import sys
from pathlib import Path

# Add project root directory to sys.path for serverless module resolution
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.main import app

# Vercel Serverless Function entry point
# Exports the ASGI app instance for @vercel/python runtime
