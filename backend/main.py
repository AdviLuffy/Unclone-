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
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(frontend_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
