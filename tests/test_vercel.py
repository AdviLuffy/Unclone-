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

def test_vercel_json_rewrites():
    """Verify vercel.json structure, function includes, and rewrite rules."""
    import json
    vercel_cfg_path = Path(__file__).resolve().parent.parent / "vercel.json"
    assert vercel_cfg_path.exists()
    with open(vercel_cfg_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    
    assert "rewrites" in cfg
    rewrites = cfg["rewrites"]
    sources = [r["source"] for r in rewrites]
    destinations = [r["destination"] for r in rewrites]

    # Verify critical rewrites are present
    assert "/api/(.*)" in sources
    assert "/" in sources
    assert "/static/(.*)" in sources
    assert "/api/index.py" in destinations
    assert "/frontend/index.html" in destinations

    # Verify functions includes
    assert "functions" in cfg
    assert "api/index.py" in cfg["functions"]
    assert cfg["functions"]["api/index.py"]["includeFiles"] == "frontend/**"

