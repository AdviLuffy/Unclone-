import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from backend.config import settings, reload_settings
from backend.database import get_connection
from backend.services.detectifai import detectifai_service, DetectifAIError
from backend.services.challenge_service import validate_challenge
from backend.services.decision_engine import evaluate_authorization, DecisionOutcome
from backend.services.demo_scenarios import get_demo_scenario, DEMO_SCENARIOS

router = APIRouter(prefix="/api/verify", tags=["Voice Verification Pipeline"])

@router.post("")
async def verify_voice(
    file: Optional[UploadFile] = File(None),
    speaker_id: Optional[str] = Form(None),
    challenge_phrase: Optional[str] = Form(None),
    transcribed_phrase: Optional[str] = Form(None),
    challenge_verification_mode: Optional[str] = Form("automated"),
    demo_scenario_key: Optional[str] = Form(None),
    transfer_amount: Optional[float] = Form(None)
):
    """
    Executes the multi-factor ALIBI voice verification pipeline:
    1. Aletheia Audio Deepfake Analysis
    2. Eidos Speaker Biometric Voiceprint Verification
    3. Spoken Challenge Liveness Validation
    4. Multi-Factor Decision Authorization & Audit Logging
    """
    reload_settings()
    incident_id = f"INC-{datetime.now().year}-{uuid.uuid4().hex[:6].upper()}"
    timestamp_iso = datetime.now(timezone.utc).isoformat()
    current_mode = settings.mode

    # Fetch speaker info if provided
    speaker_name = None
    if speaker_id:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT display_name FROM speakers WHERE speaker_id = ?", (speaker_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            speaker_name = row["display_name"]

    # =========================================================================
    # LIVE API EXECUTION BRANCH
    # =========================================================================
    if current_mode == "LIVE":
        if not file:
            raise HTTPException(status_code=400, detail="Audio file recording is required for live verification.")
        
        audio_bytes = await file.read()
        if len(audio_bytes) < 800:
            raise HTTPException(status_code=400, detail="Audio recording is empty or insufficient duration.")

        # Stage 1: Aletheia Deepfake Detection
        try:
            aletheia_res = await detectifai_service.detect_deepfake(
                file_bytes=audio_bytes, 
                filename=file.filename or "recording.wav"
            )
            aletheia_verdict = aletheia_res["verdict"]
            aletheia_score = aletheia_res["score"]
            aletheia_request_id = aletheia_res["request_id"]
            aletheia_raw = aletheia_res.get("raw", {})
        except DetectifAIError as e:
            # Audit the failure
            log_audit_record(
                incident_id=incident_id,
                timestamp=timestamp_iso,
                mode="LIVE",
                speaker_id=speaker_id,
                speaker_name=speaker_name,
                aletheia_verdict="error",
                aletheia_score=0.0,
                aletheia_request_id=None,
                eidos_verdict="skipped",
                eidos_score=0.0,
                eidos_request_id=None,
                challenge_phrase=challenge_phrase,
                challenge_transcription=transcribed_phrase,
                challenge_outcome="SKIPPED",
                final_decision=DecisionOutcome.STEP_UP_REQUIRED,
                decision_reason=f"Aletheia call failed: {e.message}",
                metadata_json=json.dumps({"error": e.message, "error_code": e.error_code})
            )
            raise HTTPException(status_code=e.status_code, detail=f"DetectifAI Error: {e.message}")

        # Stage 2: Eidos Speaker Verification (Only if Aletheia detects genuine human speech)
        eidos_verdict = "skipped"
        eidos_score = 0.0
        eidos_request_id = None
        eidos_raw = {}

        if aletheia_verdict == "real" and speaker_id:
            try:
                eidos_res = await detectifai_service.verify_speaker(
                    speaker_id=speaker_id,
                    file_bytes=audio_bytes,
                    filename=file.filename or "recording.wav"
                )
                eidos_verdict = eidos_res["verdict"]
                eidos_score = eidos_res["score"]
                eidos_request_id = eidos_res["request_id"]
                eidos_raw = eidos_res.get("raw", {})
            except DetectifAIError as e:
                eidos_verdict = "error"
                eidos_raw = {"error": e.message}

        # Stage 3: Liveness Challenge Validation
        challenge_outcome = "SKIPPED"
        challenge_details = {}
        if challenge_phrase:
            challenge_details = validate_challenge(
                expected_phrase=challenge_phrase,
                transcribed_phrase=transcribed_phrase or "",
                verification_mode=challenge_verification_mode or "automated"
            )
            challenge_outcome = challenge_details.get("outcome", "FAILED")

        # Stage 4: Decision Engine Evaluation
        eval_result = evaluate_authorization(
            aletheia_verdict=aletheia_verdict,
            aletheia_score=aletheia_score,
            eidos_verdict=eidos_verdict,
            eidos_score=eidos_score,
            challenge_outcome=challenge_outcome,
            transfer_amount=transfer_amount,
            speaker_id=speaker_id,
            speaker_name=speaker_name
        )

        provenance = "LIVE"

    # =========================================================================
    # DEMO SIMULATION EXECUTION BRANCH
    # =========================================================================
    else:
        # User specified a preset scenario OR uploaded live audio in demo mode
        if demo_scenario_key and demo_scenario_key in DEMO_SCENARIOS:
            sc = get_demo_scenario(demo_scenario_key)
            aletheia_verdict = sc["aletheia"]["verdict"]
            aletheia_score = sc["aletheia"]["score"]
            aletheia_request_id = sc["aletheia"]["request_id"]
            aletheia_raw = sc["aletheia"]["raw"]

            eidos_verdict = sc["eidos"]["verdict"]
            eidos_score = sc["eidos"]["score"]
            eidos_request_id = sc["eidos"]["request_id"]
            eidos_raw = sc["eidos"]

            challenge_outcome = sc["challenge"]["outcome"]
            challenge_details = {
                "outcome": challenge_outcome,
                "passed": sc["challenge"]["passed"],
                "transcription": sc["challenge"]["transcription"],
                "is_automated": True,
                "details": f"Simulated challenge verification for {sc['name']}"
            }
        else:
            # Interactive audio recording tested in DEMO mode:
            # If user spoke and provided transcription, perform real challenge match!
            # If challenge phrase is provided and matched, treat as genuine approved demo;
            # If challenge is failed, test replay detection rule!
            has_valid_challenge = False
            if challenge_phrase:
                challenge_details = validate_challenge(
                    expected_phrase=challenge_phrase,
                    transcribed_phrase=transcribed_phrase or "",
                    verification_mode=challenge_verification_mode or "automated"
                )
                challenge_outcome = challenge_details.get("outcome", "FAILED")
                has_valid_challenge = challenge_details.get("passed", False)
            else:
                challenge_outcome = "PASSED"
                has_valid_challenge = True
                challenge_details = {"outcome": "PASSED", "passed": True, "details": "No challenge specified."}

            aletheia_verdict = "real"
            aletheia_score = 0.032
            aletheia_request_id = f"sim_aletheia_{uuid.uuid4().hex[:8]}"
            aletheia_raw = {"verdict": "real", "confidence": 0.032, "simulated": True}

            eidos_verdict = "match" if speaker_id else "skipped"
            eidos_score = 0.915 if speaker_id else 0.0
            eidos_request_id = f"sim_eidos_{uuid.uuid4().hex[:8]}"
            eidos_raw = {"match": bool(speaker_id), "score": eidos_score, "simulated": True}

        eval_result = evaluate_authorization(
            aletheia_verdict=aletheia_verdict,
            aletheia_score=aletheia_score,
            eidos_verdict=eidos_verdict,
            eidos_score=eidos_score,
            challenge_outcome=challenge_outcome,
            transfer_amount=transfer_amount,
            speaker_id=speaker_id,
            speaker_name=speaker_name
        )

        provenance = "SIMULATED"

    # Save to persistent audit log
    audit_id = log_audit_record(
        incident_id=incident_id,
        timestamp=timestamp_iso,
        mode=current_mode,
        speaker_id=speaker_id,
        speaker_name=speaker_name,
        aletheia_verdict=aletheia_verdict,
        aletheia_score=aletheia_score,
        aletheia_request_id=aletheia_request_id,
        eidos_verdict=eidos_verdict,
        eidos_score=eidos_score,
        eidos_request_id=eidos_request_id,
        challenge_phrase=challenge_phrase,
        challenge_transcription=transcribed_phrase,
        challenge_outcome=challenge_outcome,
        final_decision=eval_result["decision"],
        decision_reason=eval_result["reason"],
        metadata_json=json.dumps({
            "provenance": provenance,
            "stages": eval_result.get("stages", {}),
            "challenge_details": challenge_details,
            "attack_type": eval_result.get("attack_type"),
            "severity": eval_result.get("severity")
        })
    )

    return {
        "incident_id": incident_id,
        "audit_id": audit_id,
        "timestamp": timestamp_iso,
        "mode": current_mode,
        "provenance": provenance,
        "speaker": {
            "speaker_id": speaker_id,
            "display_name": speaker_name or "Unassigned Speaker"
        },
        "aletheia": {
            "verdict": aletheia_verdict,
            "score": round(aletheia_score, 4),
            "request_id": aletheia_request_id,
            "raw": aletheia_raw
        },
        "eidos": {
            "verdict": eidos_verdict,
            "score": round(eidos_score, 4) if eidos_score else 0.0,
            "request_id": eidos_request_id,
            "raw": eidos_raw
        },
        "challenge": {
            "phrase": challenge_phrase,
            "transcription": transcribed_phrase,
            "outcome": challenge_outcome,
            "details": challenge_details
        },
        "decision": eval_result["decision"],
        "reason": eval_result["reason"],
        "alert": eval_result["alert"],
        "recommend_threat_report": eval_result["recommend_threat_report"],
        "attack_type": eval_result.get("attack_type"),
        "severity": eval_result.get("severity"),
        "stages": eval_result.get("stages", {})
    }

def log_audit_record(
    incident_id: str,
    timestamp: str,
    mode: str,
    speaker_id: Optional[str],
    speaker_name: Optional[str],
    aletheia_verdict: str,
    aletheia_score: float,
    aletheia_request_id: Optional[str],
    eidos_verdict: Optional[str],
    eidos_score: Optional[float],
    eidos_request_id: Optional[str],
    challenge_phrase: Optional[str],
    challenge_transcription: Optional[str],
    challenge_outcome: Optional[str],
    final_decision: str,
    decision_reason: str,
    threat_report_id: Optional[str] = None,
    metadata_json: Optional[str] = None
) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (
            incident_id, timestamp, mode, speaker_id, speaker_name,
            aletheia_verdict, aletheia_score, aletheia_request_id,
            eidos_verdict, eidos_score, eidos_request_id,
            challenge_phrase, challenge_transcription, challenge_outcome,
            final_decision, decision_reason, threat_report_id, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        incident_id, timestamp, mode, speaker_id, speaker_name,
        aletheia_verdict, aletheia_score, aletheia_request_id,
        eidos_verdict, eidos_score or 0.0, eidos_request_id,
        challenge_phrase, challenge_transcription, challenge_outcome,
        final_decision, decision_reason, threat_report_id, metadata_json
    ))
    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()
    return inserted_id
