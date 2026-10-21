import os
from pathlib import Path
import pytest
from starlette.testclient import TestClient

def test_vercel_entrypoint_import():
    """Verify that api/index.py successfully exports app for Vercel serverless runtime."""
    from api.index import app
    assert app is not None
    client = TestClient(app)
    
    # Root route serves frontend index.html
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "ALIBI" in res_root.text

    # Static files route serves assets
    res_static = client.get("/static/css/styles.css")
    assert res_static.status_code == 200
    assert "body" in res_static.text

def test_vercel_db_path_resolution(monkeypatch, tmp_path):
    """Verify that get_db_path properly switches to /tmp or custom DATABASE_PATH in Vercel environment."""
    from backend.database import get_db_path, init_db, get_connection

    # Test explicit DATABASE_PATH
    custom_db = tmp_path / "custom_alibi.db"
    monkeypatch.setenv("DATABASE_PATH", str(custom_db))
    assert get_db_path() == custom_db

    # Test Vercel environment variable
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    monkeypatch.setenv("VERCEL", "1")
    vercel_path = get_db_path()
    assert str(vercel_path).startswith(str(Path("/tmp")))

    # Verify init_db creates schema and seeds demo data on a new custom db
    monkeypatch.setenv("DATABASE_PATH", str(custom_db))
    init_db()
    assert custom_db.exists()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM speakers")
    count = cursor.fetchone()[0]
    assert count >= 3
    conn.close()

def test_serverless_env_reload(monkeypatch, tmp_path):
    """Verify that reload_settings detects environment variables directly from os.environ when no .env is on disk."""
    import backend.config as cfg
    # Simulate Vercel environment where .env is not committed to disk
    nonexistent_env = tmp_path / "nonexistent.env"
    monkeypatch.setattr(cfg, "env_path", nonexistent_env)
    monkeypatch.setenv("DETECTIF_API_KEY", "test_serverless_key_12345678")
    monkeypatch.setenv("ALIBI_MODE", "LIVE")
    s = cfg.reload_settings()
    assert s.detectif_api_key == "test_serverless_key_12345678"
    assert s.has_api_key is True

def test_public_static_assets_exist():
    """Verify that public/ directory contains index.html and static assets for Vercel CDN promotion."""
    root = Path(__file__).resolve().parent.parent
    public_index = root / "public" / "index.html"
    public_css = root / "public" / "static" / "css" / "styles.css"
    public_js = root / "public" / "static" / "js" / "app.js"

    assert public_index.exists(), "public/index.html must exist for Vercel CDN"
    assert public_css.exists(), "public/static/css/styles.css must exist for Vercel CDN"
    assert public_js.exists(), "public/static/js/app.js must exist for Vercel CDN"
    assert len(public_index.read_text(encoding="utf-8")) > 1000
    assert len(public_css.read_text(encoding="utf-8")) > 1000
    assert len(public_js.read_text(encoding="utf-8")) > 1000

def test_api_routes_and_docs():
    """Verify that API routes, health, and docs respond correctly on FastAPI app."""
    from api.index import app
    client = TestClient(app)

    # Root route serves HTML
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "ALIBI" in res_root.text

    # /api/health and /health
    res_api_health = client.get("/api/health")
    assert res_api_health.status_code == 200
    assert res_api_health.json()["status"] in ("healthy", "degraded")
    res_direct_health = client.get("/health")
    assert res_direct_health.status_code == 200

    # /api/config and /config
    res_api_config = client.get("/api/config")
    assert res_api_config.status_code == 200
    assert "mode" in res_api_config.json()
    res_direct_config = client.get("/config")
    assert res_direct_config.status_code == 200

    # /docs and /api/docs
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200
    res_api_docs = client.get("/api/docs")
    assert res_api_docs.status_code == 200

    # /openapi.json and /api/openapi.json
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    res_api_openapi = client.get("/api/openapi.json")
    assert res_api_openapi.status_code == 200

def test_root_main_entrypoint():
    """Verify that root main.py exports app and serves root correctly."""
    from main import app as root_app
    client = TestClient(root_app)
    res = client.get("/")
    assert res.status_code == 200
    assert "ALIBI" in res.text

def test_vercel_json_configuration():
    """Verify vercel.json rewrites for docs and openapi."""
    import json
    vercel_cfg_path = Path(__file__).resolve().parent.parent / "vercel.json"
    assert vercel_cfg_path.exists()
    with open(vercel_cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    
    assert "rewrites" in cfg
    rewrites = cfg["rewrites"]
    sources = [r.get("source") for r in rewrites]
    destinations = [r.get("destination") for r in rewrites]
    assert "/docs" in sources
    assert "/api/docs" in destinations
    assert "/openapi.json" in sources
    assert "/api/openapi.json" in destinations


