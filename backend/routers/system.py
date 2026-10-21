import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.config import settings, set_runtime_mode, reload_settings
from backend.services.demo_scenarios import list_demo_scenarios
from backend.database import get_connection

router = APIRouter(prefix="/api", tags=["System & Config"])

class ModeUpdateRequest(BaseModel):
    mode: str

@router.get("/health")
def get_health():
    db_ok = False
    try:
        conn = get_connection()
        conn.execute("SELECT 1").fetchone()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "healthy" if db_ok else "degraded",
        "app_name": settings.app_name,
        "version": settings.version,
        "database": "connected" if db_ok else "error",
        "current_mode": settings.mode,
        "detectifai_configured": settings.has_api_key
    }

@router.get("/config")
def get_config():
    reload_settings()
    return {
        "mode": settings.mode,
        "is_live_mode": settings.is_live_mode,
        "detectif_configured": settings.has_api_key,
        "detectif_masked_key": settings.get_masked_api_key(),
        "detectif_base_url": settings.detectif_base_url,
        "fake_threshold": settings.fake_threshold,
        "speaker_match_threshold": settings.speaker_match_threshold,
        "challenge_verify_mode": settings.challenge_verify_mode
    }

@router.post("/mode")
def update_mode(req: ModeUpdateRequest):
    reload_settings()
    target_mode = req.mode.upper()
    if target_mode not in ("LIVE", "DEMO"):
        raise HTTPException(status_code=400, detail="Mode must be either 'LIVE' or 'DEMO'")

    if target_mode == "LIVE" and not settings.has_api_key:
        raise HTTPException(
            status_code=400,
            detail="Cannot switch to LIVE mode: DetectifAI API key is not configured. Please set DETECTIF_API_KEY in .env before enabling Live mode."
        )

    new_mode = set_runtime_mode(target_mode)
    return {
        "mode": new_mode,
        "is_live_mode": new_mode == "LIVE",
        "has_api_key": settings.has_api_key,
        "message": f"Operating mode switched to {new_mode}."
    }

@router.post("/test-connection")
async def test_connection():
    """Pings the DetectifAI platform endpoint to check reachability and auth."""
    reload_settings()
    if not settings.has_api_key:
        return {
            "connected": False,
            "authenticated": False,
            "message": "No API key configured. Application running in DEMO SIMULATION mode."
        }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                f"{settings.detectif_base_url}/v1/speakers",
                headers={"Authorization": f"Bearer {settings.detectif_api_key.strip()}"}
            )
            if resp.status_code == 200:
                return {
                    "connected": True,
                    "authenticated": True,
                    "status_code": resp.status_code,
                    "message": "Successfully connected and authenticated with DetectifAI Platform."
                }
            elif resp.status_code in (401, 403):
                return {
                    "connected": True,
                    "authenticated": False,
                    "status_code": resp.status_code,
                    "message": "Connected to DetectifAI platform, but the API key was rejected (HTTP 401/403)."
                }
            else:
                return {
                    "connected": True,
                    "authenticated": False,
                    "status_code": resp.status_code,
                    "message": f"DetectifAI returned HTTP {resp.status_code}: {resp.text[:150]}"
                }
    except Exception as e:
        return {
            "connected": False,
            "authenticated": False,
            "message": f"Connection error: {str(e)}"
        }

@router.get("/scenarios")
def get_scenarios():
    return list_demo_scenarios()
