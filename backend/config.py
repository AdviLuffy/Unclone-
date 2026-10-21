import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseModel):
    app_name: str = "ALIBI - Voice Fraud Detection & Secure Authorization"
    version: str = "1.0.0"
    mode: str = os.getenv("ALIBI_MODE", "DEMO").upper()
    detectif_api_key: str = os.getenv("DETECTIF_API_KEY", "")
    detectif_base_url: str = os.getenv("DETECTIF_BASE_URL", "https://platform.detectif.ai").rstrip("/")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./alibi.db")
    challenge_verify_mode: str = os.getenv("CHALLENGE_VERIFY_MODE", "stt")
    request_timeout_seconds: float = 15.0
    
    # Thresholds
    fake_threshold: float = 0.50
    speaker_match_threshold: float = 0.70

    @property
    def is_live_mode(self) -> bool:
        return self.mode == "LIVE"

    @property
    def has_api_key(self) -> bool:
        return bool(self.detectif_api_key and len(self.detectif_api_key.strip()) > 8 and self.detectif_api_key != "your_detectif_api_key_here")

    def get_masked_api_key(self) -> str:
        if not self.detectif_api_key or self.detectif_api_key == "your_detectif_api_key_here":
            return "Not Configured"
        k = self.detectif_api_key.strip()
        if len(k) <= 8:
            return "********"
        return f"{k[:4]}...{k[-4:]}"

settings = Settings()

_runtime_mode_override = None

def set_runtime_mode(new_mode: str) -> str:
    global _runtime_mode_override
    cleaned = new_mode.upper()
    if cleaned in ("LIVE", "DEMO"):
        _runtime_mode_override = cleaned
        settings.mode = cleaned
        return settings.mode
    raise ValueError("Mode must be either 'LIVE' or 'DEMO'")

def reload_settings() -> Settings:
    global _runtime_mode_override
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    
    settings.detectif_api_key = os.getenv("DETECTIF_API_KEY", settings.detectif_api_key)
    settings.detectif_base_url = os.getenv("DETECTIF_BASE_URL", settings.detectif_base_url).rstrip("/")
    if _runtime_mode_override is not None:
        settings.mode = _runtime_mode_override
    else:
        mode_val = os.getenv("ALIBI_MODE")
        if mode_val and mode_val.upper() in ("LIVE", "DEMO"):
            settings.mode = mode_val.upper()
    return settings
