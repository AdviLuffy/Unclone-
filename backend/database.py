import sqlite3
import json
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import os
import shutil

REPO_DB_PATH = Path(__file__).parent.parent / "alibi.db"

def get_db_path() -> Path:
    if os.getenv("DATABASE_PATH"):
        return Path(os.environ["DATABASE_PATH"])
    if os.getenv("VERCEL"):
        tmp_db = Path("/tmp") / "alibi.db"
        if not tmp_db.exists():
            if REPO_DB_PATH.exists():
                try:
                    tmp_db.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(str(REPO_DB_PATH), str(tmp_db))
                except Exception:
                    pass
        return tmp_db
    return REPO_DB_PATH

DB_PATH = REPO_DB_PATH

def get_connection() -> sqlite3.Connection:
    target_path = get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Enrolled Speakers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS speakers (
        speaker_id TEXT PRIMARY KEY,
        display_name TEXT NOT NULL,
        role_title TEXT,
        consent_confirmed INTEGER NOT NULL DEFAULT 1,
        sample_count INTEGER NOT NULL DEFAULT 1,
        enrolled_at TEXT NOT NULL,
        provenance TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        notes TEXT
    )
    """)

    # Audit History
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        mode TEXT NOT NULL,
        speaker_id TEXT,
        speaker_name TEXT,
        aletheia_verdict TEXT,
        aletheia_score REAL,
        aletheia_request_id TEXT,
        eidos_verdict TEXT,
        eidos_score REAL,
        eidos_request_id TEXT,
        challenge_phrase TEXT,
        challenge_transcription TEXT,
        challenge_outcome TEXT,
        final_decision TEXT NOT NULL,
        decision_reason TEXT NOT NULL,
        threat_report_id TEXT,
        metadata_json TEXT
    )
    """)

    # Threat Intelligence Feed (r/VoiceThreatNet)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS threat_reports (
        id TEXT PRIMARY KEY,
        incident_id TEXT,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        attack_type TEXT NOT NULL,
        severity TEXT NOT NULL,
        provenance TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending Review',
        upvotes INTEGER NOT NULL DEFAULT 1,
        comments_count INTEGER NOT NULL DEFAULT 0,
        author TEXT NOT NULL DEFAULT 'SOC_Analyst',
        created_at TEXT NOT NULL,
        resolution_notes TEXT
    )
    """)

    # Transaction Simulator
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        beneficiary_name TEXT NOT NULL,
        beneficiary_account TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'USD',
        status TEXT NOT NULL,
        phantom_triggered INTEGER NOT NULL DEFAULT 0,
        incident_id TEXT,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    seed_demo_data(conn)
    conn.close()

def seed_demo_data(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # Seed demo speakers if empty
    cursor.execute("SELECT COUNT(*) FROM speakers")
    if cursor.fetchone()[0] == 0:
        demo_speakers = [
            ("spk_sarah_chen", "Sarah Chen", "Chief Financial Officer (CFO)", 1, 3, "2026-10-18T10:15:00Z", "DEMO", "active", "High-priority authorization executive"),
            ("spk_marcus_vance", "Marcus Vance", "VP Treasury & Global Wires", 1, 2, "2026-10-19T14:30:00Z", "DEMO", "active", "Authorized for transfers > $100,000"),
            ("spk_elena_rostova", "Dr. Elena Rostova", "Head of Digital Infrastructure", 1, 2, "2026-10-20T08:45:00Z", "DEMO", "active", "Secondary cryptographic signatory"),
        ]
        cursor.executemany("""
            INSERT INTO speakers (speaker_id, display_name, role_title, consent_confirmed, sample_count, enrolled_at, provenance, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_speakers)

    # Seed threat intelligence reports if empty
    cursor.execute("SELECT COUNT(*) FROM threat_reports")
    if cursor.fetchone()[0] == 0:
        demo_threats = [
            (
                "VTN-2026-8812",
                "INC-2026-0914",
                "ElevenLabs/XTTS voice clone attempting $450k urgent supplier wire",
                "Caller claimed to be CFO Sarah Chen authorizing emergency settlement. Aletheia detected synthetic acoustic artifacts (score: 0.985). Phantom Mode triggered; vault remained secure.",
                "ai_clone",
                "CRITICAL",
                "SIMULATED",
                "Verified SOC Alert",
                42,
                9,
                "u/CyberSecLead",
                "2026-10-20T16:22:10Z",
                "Origin IP blacklisted. Audio signature submitted to consortium."
            ),
            (
                "VTN-2026-7931",
                "INC-2026-0887",
                "Replay attack utilizing quarterly earnings call audio snippet",
                "Genuine voice acoustics detected by Aletheia, but caller failed dynamic challenge phrase validation. Liveness check caught out-of-context background cadence.",
                "replay",
                "HIGH",
                "SIMULATED",
                "Verified SOC Alert",
                29,
                4,
                "u/AudioForensicSpecialist",
                "2026-10-19T11:05:40Z",
                "Speaker confirmed authentic audio sampled from public YouTube broadcast."
            ),
            (
                "VTN-2026-6420",
                "INC-2026-0742",
                "Human voice impersonator mimicking treasury manager with accent modulation",
                "Natural human voice confirmed by deepfake detector, but Eidos biometric voiceprint rejected match against Marcus Vance profile (score: 0.22 vs 0.70 threshold).",
                "human_impostor",
                "HIGH",
                "SIMULATED",
                "Verified SOC Alert",
                35,
                7,
                "u/SOC_Guard_4",
                "2026-10-18T13:40:00Z",
                "Attempt escalated to fraud compliance unit."
            ),
            (
                "VTN-2026-5109",
                None,
                "Real-time low-latency neural vocoder detected in executive phone tree",
                "Observed phase inconsistencies typical of real-time stream voice changers. Flagged for review by community analysts.",
                "ai_clone",
                "MEDIUM",
                "SIMULATED",
                "Pending Review",
                14,
                2,
                "u/VoiceGuard_Watcher",
                "2026-10-17T09:12:15Z",
                None
            )
        ]
        cursor.executemany("""
            INSERT INTO threat_reports (id, incident_id, title, summary, attack_type, severity, provenance, status, upvotes, comments_count, author, created_at, resolution_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_threats)

    # Seed sample audit logs if empty
    cursor.execute("SELECT COUNT(*) FROM audit_logs")
    if cursor.fetchone()[0] == 0:
        demo_audits = [
            (
                "INC-2026-0914",
                "2026-10-20T16:22:10Z",
                "DEMO",
                "spk_sarah_chen",
                "Sarah Chen",
                "fake",
                0.985,
                "req_aletheia_demo_01",
                "skipped",
                0.0,
                None,
                "Bravo Sierra 9421 authorize wire",
                None,
                "SKIPPED",
                "BLOCKED",
                "AI-generated synthetic voice detected by Aletheia (score: 0.985). Simulated transaction aborted.",
                "VTN-2026-8812",
                json.dumps({"synthetic_confidence": 0.985, "model": "Aletheia-Audio-v1.4"})
            ),
            (
                "INC-2026-0887",
                "2026-10-19T11:05:40Z",
                "DEMO",
                "spk_marcus_vance",
                "Marcus Vance",
                "real",
                0.042,
                "req_aletheia_demo_02",
                "match",
                0.890,
                "req_eidos_demo_02",
                "Tango Delta 7731 authorization confirmed",
                "Tango Delta zero zero zero",
                "FAILED",
                "BLOCKED",
                "Speaker voice matched enrolled profile, but failed fresh spoken challenge phrase (suspected replay attack).",
                "VTN-2026-7931",
                json.dumps({"match_score": 0.89, "challenge_match_ratio": 0.35})
            ),
            (
                "INC-2026-0742",
                "2026-10-18T13:40:00Z",
                "DEMO",
                "spk_marcus_vance",
                "Marcus Vance",
                "real",
                0.038,
                "req_aletheia_demo_03",
                "no_match",
                0.220,
                "req_eidos_demo_03",
                "Victor Kilo 4412 confirm dispatch",
                "Victor Kilo 4412 confirm dispatch",
                "PASSED",
                "BLOCKED",
                "Voice is genuine human speech but biometric voiceprint does NOT match claimed speaker Marcus Vance.",
                "VTN-2026-6420",
                json.dumps({"match_score": 0.22, "threshold": 0.70})
            ),
            (
                "INC-2026-0611",
                "2026-10-17T18:04:12Z",
                "DEMO",
                "spk_elena_rostova",
                "Dr. Elena Rostova",
                "real",
                0.015,
                "req_aletheia_demo_04",
                "match",
                0.945,
                "req_eidos_demo_04",
                "Echo Uniform 8820 clearance granted",
                "Echo Uniform 8820 clearance granted",
                "PASSED",
                "APPROVED",
                "Voice verified authentic, biometric match confirmed, and fresh liveness challenge passed.",
                None,
                json.dumps({"match_score": 0.945, "transfer_amount": 75000})
            )
        ]
        cursor.executemany("""
            INSERT INTO audit_logs (incident_id, timestamp, mode, speaker_id, speaker_name, aletheia_verdict, aletheia_score, aletheia_request_id, eidos_verdict, eidos_score, eidos_request_id, challenge_phrase, challenge_transcription, challenge_outcome, final_decision, decision_reason, threat_report_id, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_audits)

    conn.commit()
