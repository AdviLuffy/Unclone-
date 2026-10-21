import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database import init_db
from backend.services.challenge_service import generate_challenge_phrase, validate_challenge

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert "current_mode" in data

def test_config_endpoint(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.json()
    assert "mode" in data
    assert "detectif_masked_key" in data
    # Ensure raw secret is never returned
    assert "your_detectif_api_key_here" not in data.get("detectif_masked_key", "")

def test_mode_switch(client):
    # Test setting to DEMO
    res = client.post("/api/mode", json={"mode": "DEMO"})
    assert res.status_code == 200
    assert res.json()["mode"] == "DEMO"

    # Test invalid mode
    res_bad = client.post("/api/mode", json={"mode": "INVALID_MODE"})
    assert res_bad.status_code == 400

def test_challenge_generation_and_validation():
    chal = generate_challenge_phrase()
    assert "phrase" in chal
    assert "digits" in chal
    assert "challenge_id" in chal

    # Validate correct automated speech
    val = validate_challenge(chal["phrase"], chal["phrase"], "automated")
    assert val["passed"] is True
    assert val["outcome"] == "PASSED"
    assert val["confidence"] >= 0.85

    # Validate empty speech fails
    val_empty = validate_challenge(chal["phrase"], "", "automated")
    assert val_empty["passed"] is False
    assert val_empty["outcome"] == "FAILED"

    # Validate manual verification
    val_manual = validate_challenge(chal["phrase"], "", "manual")
    assert val_manual["passed"] is True
    assert val_manual["outcome"] == "MANUAL_VERIFIED"
    assert val_manual["is_automated"] is False

def test_speakers_list(client):
    res = client.get("/api/speakers")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Check seeded demo speaker
    names = [s["display_name"] for s in data]
    assert "Sarah Chen" in names

def test_speaker_enrollment_consent_required(client):
    # Try enrolling without consent -> must return 400
    res = client.post(
        "/api/speakers/enroll",
        data={"display_name": "Test User", "role_title": "Analyst", "consent_confirmed": "false"},
        files={"file": ("test.wav", b"dummy_audio_bytes" * 100, "audio/wav")}
    )
    assert res.status_code == 400
    assert "consent" in res.json()["detail"].lower()

def test_phantom_mode_blocked_transfer(client):
    # Suspicious transfer: verification decision BLOCKED
    res = client.post("/api/simulator/transfer", json={
        "beneficiary_name": "Offshore Exfiltration Shell LLC",
        "beneficiary_account": "ACC-99201928",
        "beneficiary_bank": "Cayman Island Syndicate Bank",
        "amount": 250000.0,
        "currency": "USD",
        "verification_decision": "BLOCKED",
        "incident_id": "INC-TEST-001",
        "reason": "AI-generated synthetic voice detected.",
        "attack_type": "ai_clone"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["phantom_triggered"] is True
    assert data["status"] == "BLOCKED_PHANTOM"
    # Attacker decoy receipt present
    assert data["decoy_receipt"] is not None
    assert "TRANSFER DISPATCHED" in data["decoy_receipt"]["receipt_banner"]
    # Real SOC state shows funds secured
    assert data["internal_soc_state"]["real_outcome"] == "FUNDS_PRESERVED_IN_VAULT"
    assert data["internal_soc_state"]["vault_locked"] is True

def test_approved_transfer(client):
    res = client.post("/api/simulator/transfer", json={
        "beneficiary_name": "Vendor Payments Corp",
        "beneficiary_account": "ACC-11223344",
        "amount": 5000.0,
        "verification_decision": "APPROVED",
        "reason": "Voice verified"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "APPROVED"
    assert data["phantom_triggered"] is False
    assert data["decoy_receipt"] is None
    assert data["internal_soc_state"]["real_outcome"] == "TRANSFER_EXECUTED"

def test_threat_feed_crud_and_moderation(client):
    # List threats
    res = client.get("/api/threats")
    assert res.status_code == 200
    initial_reports = res.json()
    assert len(initial_reports) >= 1

    # Create safe report
    create_res = client.post("/api/threats", json={
        "title": "Suspected Neural Voice Stager targeting VP Treasury",
        "summary": "High-frequency vocoder artifacts observed in phone channel.",
        "attack_type": "ai_clone",
        "severity": "HIGH",
        "provenance": "SIMULATED",
        "author": "u/SOC_Analyst_9"
    })
    assert create_res.status_code == 200
    report_id = create_res.json()["id"]

    # Upvote
    up_res = client.post(f"/api/threats/{report_id}/upvote")
    assert up_res.status_code == 200
    assert up_res.json()["upvotes"] >= 2

    # Moderator verify action
    mod_res = client.post(f"/api/threats/{report_id}/action", json={
        "action": "verify",
        "notes": "Confirmed by SOC acoustic review."
    })
    assert mod_res.status_code == 200
    assert mod_res.json()["status"] == "Verified SOC Alert"

def test_audit_logs_and_csv_export(client):
    res = client.get("/api/audit")
    assert res.status_code == 200
    logs = res.json()
    assert len(logs) >= 1

    csv_res = client.get("/api/audit/export/csv")
    assert csv_res.status_code == 200
    assert "Incident ID" in csv_res.text
