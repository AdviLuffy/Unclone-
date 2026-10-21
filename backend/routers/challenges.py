from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.challenge_service import generate_challenge_phrase, validate_challenge

router = APIRouter(prefix="/api/challenges", tags=["Liveness Challenge"])

class ValidateChallengeRequest(BaseModel):
    expected_phrase: str
    transcribed_phrase: str
    verification_mode: str = "automated"  # "automated" or "manual"

@router.get("/generate")
def get_challenge():
    return generate_challenge_phrase()

@router.post("/validate")
def verify_challenge(req: ValidateChallengeRequest):
    result = validate_challenge(
        expected_phrase=req.expected_phrase,
        transcribed_phrase=req.transcribed_phrase,
        verification_mode=req.verification_mode
    )
    return result
