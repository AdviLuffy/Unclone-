from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import settings
from backend.database import init_db
from backend.routers import (
    system,
    speakers,
    challenges,
    verify,
    simulator,
    threats,
    audit
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database and seed demo data
    init_db()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="ALIBI - Voice Fraud Detection & Secure Authorization Engine",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(system.router)
app.include_router(speakers.router)
app.include_router(challenges.router)
app.include_router(verify.router)
app.include_router(simulator.router)
app.include_router(threats.router)
app.include_router(audit.router)

# Mount Frontend Static Assets
candidate_frontend_dirs = [
    Path(__file__).resolve().parent.parent / "frontend",
    Path.cwd() / "frontend",
    Path("/var/task/frontend")
]
frontend_dir = None
for candidate in candidate_frontend_dirs:
    if candidate.exists() and (candidate / "index.html").exists():
        frontend_dir = candidate
        break

if frontend_dir:
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(frontend_dir / "index.html")
else:
    @app.get("/")
    def serve_fallback_index():
        for candidate in candidate_frontend_dirs:
            p = candidate / "index.html"
            if p.exists():
                return FileResponse(p)
        return {"status": "ALIBI Voice Security Engine Online", "mode": settings.mode}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
