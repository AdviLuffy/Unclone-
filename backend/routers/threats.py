import uuid
import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from backend.database import get_connection

router = APIRouter(prefix="/api/threats", tags=["Threat Intelligence Feed (r/VoiceThreatNet)"])

class CreateThreatReportRequest(BaseModel):
    incident_id: Optional[str] = None
    title: str
    summary: str
    attack_type: str = "ai_clone"  # "ai_clone", "replay", "human_impostor", "unknown"
    severity: str = "HIGH"         # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    provenance: str = "SIMULATED"  # "LIVE" or "SIMULATED"
    author: str = "u/SOC_Analyst"

class ModeratorActionRequest(BaseModel):
    action: str  # "verify", "flag", "dismiss"
    notes: Optional[str] = None

@router.get("")
def list_threat_reports(
    attack_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None
):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM threat_reports WHERE 1=1"
    params = []

    if attack_type and attack_type != "all":
        query += " AND attack_type = ?"
        params.append(attack_type)

    if severity and severity != "all":
        query += " AND severity = ?"
        params.append(severity)

    if status and status != "all":
        query += " AND status = ?"
        params.append(status)

    if q and q.strip():
        query += " AND (title LIKE ? OR summary LIKE ?)"
        like_q = f"%{q.strip()}%"
        params.extend([like_q, like_q])

    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(r) for r in rows]

@router.get("/{report_id}")
def get_threat_report(report_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM threat_reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Threat report not found.")

    return dict(row)

@router.post("")
def create_threat_report(req: CreateThreatReportRequest):
    """
    Submits an incident report to r/VoiceThreatNet.
    Stores safe metadata only (no raw audio, API secrets, or PII).
    """
    report_id = f"VTN-{datetime.datetime.now().year}-{uuid.uuid4().hex[:4].upper()}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    conn = get_connection()
    cursor = conn.cursor()

    # Link report back to audit log if incident_id provided
    if req.incident_id:
        cursor.execute("UPDATE audit_logs SET threat_report_id = ? WHERE incident_id = ?", (report_id, req.incident_id))

    cursor.execute("""
        INSERT INTO threat_reports (
            id, incident_id, title, summary, attack_type, severity, provenance, status, upvotes, comments_count, author, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        req.incident_id,
        req.title.strip(),
        req.summary.strip(),
        req.attack_type,
        req.severity,
        req.provenance,
        "Pending Review",
        1,
        0,
        req.author,
        now_iso
    ))
    conn.commit()
    conn.close()

    return {
        "id": report_id,
        "incident_id": req.incident_id,
        "title": req.title,
        "status": "Pending Review",
        "created_at": now_iso,
        "message": "Report successfully filed to r/VoiceThreatNet. Awaiting SOC moderator review."
    }

@router.post("/{report_id}/upvote")
def upvote_threat_report(report_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE threat_reports SET upvotes = upvotes + 1 WHERE id = ?", (report_id,))
    conn.commit()
    cursor.execute("SELECT upvotes FROM threat_reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Threat report not found.")

    return {"id": report_id, "upvotes": row["upvotes"]}

@router.post("/{report_id}/action")
def moderator_action(report_id: str, req: ModeratorActionRequest):
    action = req.action.lower()
    if action == "verify":
        new_status = "Verified SOC Alert"
    elif action == "flag":
        new_status = "Flagged - Needs Telemetry"
    elif action == "dismiss":
        new_status = "Dismissed"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'verify', 'flag', or 'dismiss'.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE threat_reports
        SET status = ?, resolution_notes = ?
        WHERE id = ?
    """, (new_status, req.notes, report_id))
    conn.commit()
    conn.close()

    return {
        "id": report_id,
        "status": new_status,
        "resolution_notes": req.notes,
        "message": f"Threat report updated to '{new_status}'."
    }
