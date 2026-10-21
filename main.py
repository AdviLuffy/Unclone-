import sys
from pathlib import Path

# Add project root directory to sys.path for serverless module resolution
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.main import app

# Export ASGI application instance for Vercel
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
