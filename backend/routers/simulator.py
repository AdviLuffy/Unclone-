import uuid
import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from backend.database import get_connection

router = APIRouter(prefix="/api/simulator", tags=["Transaction Simulator & Phantom Mode"])

# In-memory simulated vault telemetry
vault_state = {
    "vault_id": "VAULT-ALPHA-772",
    "institution_name": "Apex Horizon Trust (Simulated)",
    "vault_status": "SECURE_ONLINE",  # "SECURE_ONLINE" or "EMERGENCY_LOCKDOWN"
    "total_simulated_reserves": 10000000.00,
    "funds_blocked_from_fraud": 0.0,
    "last_alert": None
}

class TransferRequest(BaseModel):
    beneficiary_name: str
    beneficiary_account: str
    beneficiary_bank: str = "Offshore Capital Partners, Ltd."
    amount: float
    currency: str = "USD"
    speaker_id: Optional[str] = None
    verification_decision: str  # "APPROVED" or "BLOCKED" or "STEP_UP_REQUIRED"
    incident_id: Optional[str] = None
    reason: Optional[str] = None
    attack_type: Optional[str] = None

@router.get("/status")
def get_vault_status():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, beneficiary_name, beneficiary_account, amount, currency, status, phantom_triggered, incident_id, created_at
        FROM transactions
        ORDER BY created_at DESC LIMIT 10
    """)
    recent_txs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return {
        "vault_state": vault_state,
        "recent_transactions": recent_txs,
        "fictional_disclaimer": "Fictional banking sandbox for cybersecurity demonstration only. No real banking connections."
    }

@router.post("/transfer")
def process_simulated_transfer(req: TransferRequest):
    tx_id = f"TXN-{datetime.datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    phantom_ref = f"FW-PHANTOM-{uuid.uuid4().hex[:6].upper()}-TRACE"

    is_blocked = req.verification_decision != "APPROVED"
    phantom_triggered = 1 if is_blocked else 0

    conn = get_connection()
    cursor = conn.cursor()

    if is_blocked:
        # Trigger Phantom Mode
        vault_state["vault_status"] = "EMERGENCY_LOCKDOWN"
        vault_state["funds_blocked_from_fraud"] += req.amount
        vault_state["last_alert"] = {
            "incident_id": req.incident_id,
            "timestamp": now_iso,
            "blocked_amount": req.amount,
            "beneficiary": req.beneficiary_name,
            "reason": req.reason,
            "attack_type": req.attack_type
        }
        status = "BLOCKED_PHANTOM"

        # Attacker sees a convincing decoy receipt
        decoy_receipt = {
            "type": "DECOY_PHANTOM_RECEIPT",
            "receipt_banner": "TRANSFER DISPATCHED SUCCESSFULLY",
            "wire_confirmation": phantom_ref,
            "timestamp": now_iso,
            "beneficiary": req.beneficiary_name,
            "account_credited": req.beneficiary_account,
            "amount_credited": f"${req.amount:,.2f} {req.currency}",
            "clearing_network": "FedWire Global FastSettlement (Simulated)",
            "status": "SETTLED / PENDING CLEARING AGENT RELEASE",
            "attacker_view_notice": "Decoy telemetry delivered to caller session to delay attacker discovery."
        }

        # Real internal state for SOC dashboard
        internal_soc_state = {
            "real_outcome": "FUNDS_PRESERVED_IN_VAULT",
            "vault_locked": True,
            "funds_dispatched": 0.0,
            "alert_priority": "CRITICAL_FRAUD_PREVENTED",
            "reason": req.reason or "Voice authorization failed policy thresholds.",
            "recommended_action": "File incident report to r/VoiceThreatNet and freeze caller origin."
        }
    else:
        # Genuine transfer approved
        status = "APPROVED"
        decoy_receipt = None
        internal_soc_state = {
            "real_outcome": "TRANSFER_EXECUTED",
            "vault_locked": False,
            "funds_dispatched": req.amount,
            "alert_priority": "NONE",
            "reason": "Multi-factor voice biometrics and liveness challenge authenticated."
        }

    cursor.execute("""
        INSERT INTO transactions (id, beneficiary_name, beneficiary_account, amount, currency, status, phantom_triggered, incident_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, req.beneficiary_name, req.beneficiary_account, req.amount, req.currency, status, phantom_triggered, req.incident_id, now_iso))
    conn.commit()
    conn.close()

    return {
        "transaction_id": tx_id,
        "status": status,
        "phantom_triggered": bool(phantom_triggered),
        "amount": req.amount,
        "currency": req.currency,
        "timestamp": now_iso,
        "decoy_receipt": decoy_receipt,
        "internal_soc_state": internal_soc_state,
        "vault_status": vault_state["vault_status"],
        "fictional_notice": "Simulated banking transaction for demonstration purposes only."
    }

@router.post("/unlock-vault")
def unlock_vault():
    vault_state["vault_status"] = "SECURE_ONLINE"
    return {
        "vault_status": vault_state["vault_status"],
        "message": "Simulated vault emergency lockdown reset to SECURE_ONLINE."
    }
