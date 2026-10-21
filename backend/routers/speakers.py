import uuid
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from backend.config import settings, reload_settings
from backend.database import get_connection
from backend.services.detectifai import detectifai_service, DetectifAIError

router = APIRouter(prefix="/api/speakers", tags=["Speaker Biometrics"])

@router.get("")
def list_speakers():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT speaker_id, display_name, role_title, consent_confirmed, 
               sample_count, enrolled_at, provenance, status, notes
        FROM speakers
        ORDER BY enrolled_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@router.post("/enroll")
async def enroll_speaker(
    display_name: str = Form(...),
    role_title: str = Form("Executive Signatory"),
    consent_confirmed: bool = Form(...),
    notes: str = Form(""),
    file: UploadFile = File(...)
):
    """
    Enrolls a speaker voice sample with biometric consent.
    Live mode: calls DetectifAI Eidos /v1/speakers/enroll. Never fabricates live enrollment.
    Demo mode: creates clearly labelled simulated profile.
    """
    reload_settings()
    if not consent_confirmed:
        raise HTTPException(
            status_code=400, 
            detail="Biometric voice enrollment requires explicit user consent confirmation."
        )

    if not display_name.strip():
        raise HTTPException(status_code=400, detail="Display name is required.")

    # Read audio bytes
    audio_bytes = await file.read()
    if len(audio_bytes) < 1000:
        raise HTTPException(status_code=400, detail="Audio file is empty or too short.")

    # Clean identifier
    clean_id = re.sub(r"[^A-Za-z0-9_]", "_", display_name.lower().strip())
    speaker_id = f"spk_{clean_id}_{uuid.uuid4().hex[:6]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    if settings.is_live_mode:
        try:
            # Call Eidos endpoint
            eidos_result = await detectifai_service.enroll_speaker(
                speaker_id=speaker_id,
                file_bytes=audio_bytes,
                filename=file.filename or "enroll.wav"
            )
            provenance = "LIVE"
            status = "active"
            sample_count = 1
            extra_note = f"Eidos Request ID: {eidos_result.get('request_id')}"
        except DetectifAIError as e:
            conn.close()
            raise HTTPException(status_code=e.status_code, detail=f"DetectifAI Eidos error: {e.message}")
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=500, detail=f"Unexpected enrollment failure: {str(e)}")
    else:
        # DEMO SIMULATION mode
        provenance = "DEMO"
        status = "active"
        sample_count = 1
        extra_note = "Simulated enrolled profile for hackathon demonstration."

    full_notes = f"{notes} | {extra_note}".strip(" |")

    cursor.execute("""
        INSERT INTO speakers (speaker_id, display_name, role_title, consent_confirmed, sample_count, enrolled_at, provenance, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (speaker_id, display_name.strip(), role_title.strip(), 1 if consent_confirmed else 0, sample_count, now_iso, provenance, status, full_notes))
    conn.commit()
    conn.close()

    return {
        "speaker_id": speaker_id,
        "display_name": display_name.strip(),
        "role_title": role_title.strip(),
        "consent_confirmed": True,
        "sample_count": sample_count,
        "enrolled_at": now_iso,
        "provenance": provenance,
        "status": status,
        "notes": full_notes,
        "message": f"Successfully enrolled voice profile for '{display_name}' [{provenance}]."
    }

@router.delete("/{speaker_id}")
def delete_speaker(speaker_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT speaker_id FROM speakers WHERE speaker_id = ?", (speaker_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Speaker profile not found.")

    cursor.execute("DELETE FROM speakers WHERE speaker_id = ?", (speaker_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted", "speaker_id": speaker_id}
