from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
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
    lifespan=lifespan,
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers (all start with /api)
app.include_router(system.router)
app.include_router(speakers.router)
app.include_router(challenges.router)
app.include_router(verify.router)
app.include_router(simulator.router)
app.include_router(threats.router)
app.include_router(audit.router)

# Compatibility direct routes (for environments that route /health or /config directly)
@app.get("/health", tags=["System & Config"], include_in_schema=False)
def direct_health():
    return system.get_health()

@app.get("/config", tags=["System & Config"], include_in_schema=False)
def direct_config():
    return system.get_config()

# Dual docs endpoints (/docs and /api/docs)
@app.get("/api/docs", include_in_schema=False)
def serve_api_docs():
    from fastapi.openapi.docs import get_swagger_ui_html
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title=settings.app_name + " - API Docs")

@app.get("/api/openapi.json", include_in_schema=False)
def serve_api_openapi():
    return app.openapi()

# Frontend Static Assets & Root Handler (for local development or direct serverless execution)
candidate_static_dirs = [
    Path(__file__).resolve().parent.parent / "public" / "static",
    Path(__file__).resolve().parent.parent / "frontend",
    Path.cwd() / "public" / "static",
    Path.cwd() / "frontend"
]
static_dir = None
for c in candidate_static_dirs:
    if c.exists():
        static_dir = c
        break

if static_dir:
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

candidate_index_files = [
    Path(__file__).resolve().parent.parent / "public" / "index.html",
    Path(__file__).resolve().parent.parent / "frontend" / "index.html",
    Path.cwd() / "public" / "index.html",
    Path.cwd() / "frontend" / "index.html"
]

@app.get("/")
@app.get("/index.html")
def serve_root():
    for f in candidate_index_files:
        if f.exists():
            return FileResponse(f)
    return {"status": "ALIBI Voice Security Engine Online", "mode": settings.mode}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
