import csv
import io
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from backend.database import get_connection

router = APIRouter(prefix="/api/audit", tags=["Audit History"])

@router.get("")
def list_audit_logs(
    decision: Optional[str] = None,
    mode: Optional[str] = None,
    limit: int = 50
):
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []

    if decision and decision != "all":
        query += " AND final_decision = ?"
        params.append(decision)

    if mode and mode != "all":
        query += " AND mode = ?"
        params.append(mode)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        if d.get("metadata_json"):
            try:
                d["metadata"] = json.loads(d["metadata_json"])
            except Exception:
                d["metadata"] = {}
        results.append(d)

    return results

@router.get("/{incident_id}")
def get_audit_log(incident_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_logs WHERE incident_id = ?", (incident_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Audit incident not found.")

    d = dict(row)
    if d.get("metadata_json"):
        try:
            d["metadata"] = json.loads(d["metadata_json"])
        except Exception:
            d["metadata"] = {}
    return d

@router.get("/export/csv")
def export_audit_csv():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT incident_id, timestamp, mode, speaker_name, aletheia_verdict, 
               aletheia_score, aletheia_request_id, eidos_verdict, eidos_score, 
               eidos_request_id, challenge_outcome, final_decision, decision_reason, threat_report_id
        FROM audit_logs
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Incident ID", "Timestamp", "Operating Mode", "Speaker", 
        "Aletheia Verdict", "Aletheia Score", "Aletheia Req ID",
        "Eidos Verdict", "Eidos Score", "Eidos Req ID",
        "Challenge Outcome", "Final Decision", "Policy Reason", "Threat Report Ref"
    ])

    for r in rows:
        writer.writerow([
            r["incident_id"], r["timestamp"], r["mode"], r["speaker_name"] or "N/A",
            r["aletheia_verdict"], r["aletheia_score"], r["aletheia_request_id"] or "N/A",
            r["eidos_verdict"], r["eidos_score"], r["eidos_request_id"] or "N/A",
            r["challenge_outcome"], r["final_decision"], r["decision_reason"], r["threat_report_id"] or "None"
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=alibi_security_audit.csv"}
    )
