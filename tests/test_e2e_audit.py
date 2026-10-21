import io
import pytest
from starlette.testclient import TestClient
from backend.main import app
from backend.database import init_db
from backend.config import settings, set_runtime_mode

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_four_demo_scenarios(client):
    """Test all four demo scenarios through /api/verify."""
    set_runtime_mode("DEMO")

    # 1. AI Clone
    res1 = client.post("/api/verify", data={
        "demo_scenario_key": "ai_clone",
        "speaker_id": "spk_sarah_chen",
        "challenge_phrase": "Alpha Echo 4921 authorize transfer"
    })
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["decision"] == "BLOCKED"
    assert d1["attack_type"] == "ai_clone"
    assert d1["aletheia"]["verdict"] == "fake"
    assert d1["severity"] == "CRITICAL"
    assert d1["recommend_threat_report"] is True

    # 2. Genuine Voice + Matching Speaker
    res2 = client.post("/api/verify", data={
        "demo_scenario_key": "genuine_approved",
        "speaker_id": "spk_sarah_chen",
        "challenge_phrase": "Alpha Echo 4921 authorize transfer"
    })
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["decision"] == "APPROVED"
    assert d2["aletheia"]["verdict"] == "real"
    assert d2["eidos"]["verdict"] == "match"
    assert d2["challenge"]["outcome"] == "PASSED"
    assert d2["attack_type"] is None

    # 3. Human Impostor
    res3 = client.post("/api/verify", data={
        "demo_scenario_key": "human_impostor",
        "speaker_id": "spk_sarah_chen",
        "challenge_phrase": "Alpha Echo 4921 authorize transfer"
    })
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["decision"] == "BLOCKED"
    assert d3["attack_type"] == "human_impostor"
    assert d3["aletheia"]["verdict"] == "real"
    assert d3["eidos"]["verdict"] == "no_match"
    assert d3["severity"] == "HIGH"

    # 4. Inconclusive Detection
    res4 = client.post("/api/verify", data={
        "demo_scenario_key": "inconclusive",
        "speaker_id": "spk_sarah_chen",
        "challenge_phrase": "Alpha Echo 4921 authorize transfer"
    })
    assert res4.status_code == 200
    d4 = res4.json()
    assert d4["decision"] == "STEP_UP_REQUIRED"
    assert d4["aletheia"]["verdict"] == "not_sure"
    assert "inconclusive" in d4["reason"].lower()

def test_audio_upload_and_challenge_matching(client):
    """Test audio upload with matching vs mismatched challenge validation."""
    set_runtime_mode("DEMO")

    # Generate a challenge
    c_res = client.get("/api/challenges/generate")
    assert c_res.status_code == 200
    chal = c_res.json()
    phrase = chal["phrase"]

    dummy_wav = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x08\x00\x00" + (b"\x00" * 2000)

    # Valid matching challenge transcription -> APPROVED
    res_match = client.post(
        "/api/verify",
        data={
            "speaker_id": "spk_sarah_chen",
            "challenge_phrase": phrase,
            "transcribed_phrase": phrase,
            "challenge_verification_mode": "automated"
        },
        files={"file": ("recording.wav", dummy_wav, "audio/wav")}
    )
    assert res_match.status_code == 200
    d_match = res_match.json()
    assert d_match["decision"] == "APPROVED"
    assert d_match["challenge"]["outcome"] == "PASSED"

    # Mismatched challenge transcription -> BLOCKED (suspected replay attack)
    res_mismatch = client.post(
        "/api/verify",
        data={
            "speaker_id": "spk_sarah_chen",
            "challenge_phrase": phrase,
            "transcribed_phrase": "completely unrelated words here",
            "challenge_verification_mode": "automated"
        },
        files={"file": ("recording.wav", dummy_wav, "audio/wav")}
    )
    assert res_mismatch.status_code == 200
    d_mismatch = res_mismatch.json()
    assert d_mismatch["decision"] == "BLOCKED"
    assert d_mismatch["attack_type"] == "replay"
    assert d_mismatch["challenge"]["outcome"] == "FAILED"

def test_speaker_enrollment_lifecycle(client):
    """Test speaker enrollment with and without biometric consent, listing, and deletion."""
    set_runtime_mode("DEMO")
    dummy_wav = b"RIFF" + (b"\x00" * 1500)

    # Missing consent -> MUST FAIL with 400
    res_no_consent = client.post(
        "/api/speakers/enroll",
        data={"display_name": "Marcus Aurelius", "role_title": "Signatory", "consent_confirmed": "false"},
        files={"file": ("voice.wav", dummy_wav, "audio/wav")}
    )
    assert res_no_consent.status_code == 400
    assert "consent" in res_no_consent.json()["detail"].lower()

    # Empty audio -> MUST FAIL with 400
    res_empty_audio = client.post(
        "/api/speakers/enroll",
        data={"display_name": "Marcus Aurelius", "role_title": "Signatory", "consent_confirmed": "true"},
        files={"file": ("voice.wav", b"short", "audio/wav")}
    )
    assert res_empty_audio.status_code == 400

    # Valid enrollment -> SUCCESS
    res_ok = client.post(
        "/api/speakers/enroll",
        data={"display_name": "Marcus Aurelius", "role_title": "Signatory", "consent_confirmed": "true", "notes": "Audited profile"},
        files={"file": ("voice.wav", dummy_wav, "audio/wav")}
    )
    assert res_ok.status_code == 200
    enrolled = res_ok.json()
    speaker_id = enrolled["speaker_id"]
    assert enrolled["consent_confirmed"] is True
    assert "Marcus Aurelius" in enrolled["display_name"]

    # Verify speaker is in listing
    list_res = client.get("/api/speakers")
    assert list_res.status_code == 200
    speakers = list_res.json()
    assert any(s["speaker_id"] == speaker_id for s in speakers)

    # Delete speaker
    del_res = client.delete(f"/api/speakers/{speaker_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

def test_transaction_simulator_and_phantom_mode(client):
    """Test transaction simulation, Phantom Mode decoy protocol, and vault reset."""
    # 1. Approved transfer
    res_appr = client.post("/api/simulator/transfer", json={
        "beneficiary_name": "Approved Vendor Inc",
        "beneficiary_account": "ACC-APP-123",
        "amount": 75000.0,
        "verification_decision": "APPROVED",
        "reason": "Authentic voice approved"
    })
    assert res_appr.status_code == 200
    d_appr = res_appr.json()
    assert d_appr["status"] == "APPROVED"
    assert d_appr["phantom_triggered"] is False
    assert d_appr["decoy_receipt"] is None
    assert d_appr["internal_soc_state"]["real_outcome"] == "TRANSFER_EXECUTED"
    assert d_appr["fictional_notice"] is not None

    # 2. Blocked transfer -> Trigger Phantom Mode
    res_block = client.post("/api/simulator/transfer", json={
        "beneficiary_name": "Shadow Syndicate Accounts",
        "beneficiary_account": "ACC-SHADOW-999",
        "amount": 350000.0,
        "verification_decision": "BLOCKED",
        "incident_id": "INC-TEST-PHANTOM",
        "reason": "Synthetic voice clone detected",
        "attack_type": "ai_clone"
    })
    assert res_block.status_code == 200
    d_block = res_block.json()
    assert d_block["status"] == "BLOCKED_PHANTOM"
    assert d_block["phantom_triggered"] is True
    # Verify Decoy Receipt for attacker view
    decoy = d_block["decoy_receipt"]
    assert decoy is not None
    assert decoy["type"] == "DECOY_PHANTOM_RECEIPT"
    assert "TRANSFER DISPATCHED" in decoy["receipt_banner"]
    assert "FW-PHANTOM-" in decoy["wire_confirmation"]
    assert decoy["status"] == "SETTLED / PENDING CLEARING AGENT RELEASE"
    assert "Simulated" in decoy["clearing_network"]
    assert "Decoy telemetry" in decoy["attacker_view_notice"]

    # Verify Real Internal SOC state: funds NEVER left vault
    soc_state = d_block["internal_soc_state"]
    assert soc_state["real_outcome"] == "FUNDS_PRESERVED_IN_VAULT"
    assert soc_state["vault_locked"] is True
    assert soc_state["funds_dispatched"] == 0.0

    # Verify Vault status is in EMERGENCY_LOCKDOWN
    status_res = client.get("/api/simulator/status")
    assert status_res.status_code == 200
    v_data = status_res.json()
    assert v_data["vault_state"]["vault_status"] == "EMERGENCY_LOCKDOWN"
    assert "fictional_disclaimer" in v_data

    # Unlock vault
    unlock_res = client.post("/api/simulator/unlock-vault")
    assert unlock_res.status_code == 200
    assert unlock_res.json()["vault_status"] == "SECURE_ONLINE"

def test_threat_feed_and_moderation_e2e(client):
    """Test r/VoiceThreatNet dispatch lifecycle: listing, creation, upvoting, and moderation."""
    # Create dispatch
    c_res = client.post("/api/threats", json={
        "title": "E2E Audit Test Threat Dispatch",
        "summary": "Deepfake telemetry showing high synthetic probability.",
        "attack_type": "ai_clone",
        "severity": "CRITICAL",
        "provenance": "SIMULATED",
        "author": "u/Auditor_Bot"
    })
    assert c_res.status_code == 200
    report = c_res.json()
    report_id = report["id"]
    assert report["status"] == "Pending Review"

    # Upvote
    up_res = client.post(f"/api/threats/{report_id}/upvote")
    assert up_res.status_code == 200
    assert up_res.json()["upvotes"] >= 2

    # Moderate: Verify Incident
    mod_res = client.post(f"/api/threats/{report_id}/action", json={
        "action": "verify",
        "notes": "Verified by SOC test suite"
    })
    assert mod_res.status_code == 200
    assert mod_res.json()["status"] == "Verified SOC Alert"

    # Search query
    q_res = client.get(f"/api/threats?q=E2E+Audit+Test")
    assert q_res.status_code == 200
    results = q_res.json()
    assert any(r["id"] == report_id for r in results)

def test_audit_history_and_csv_export(client):
    """Test audit log inspection and CSV file export."""
    # List audit records
    list_res = client.get("/api/audit?limit=10")
    assert list_res.status_code == 200
    logs = list_res.json()
    assert len(logs) >= 1
    sample_incident = logs[0]["incident_id"]

    # Retrieve single record
    item_res = client.get(f"/api/audit/{sample_incident}")
    assert item_res.status_code == 200
    assert item_res.json()["incident_id"] == sample_incident

    # Export CSV
    csv_res = client.get("/api/audit/export/csv")
    assert csv_res.status_code == 200
    assert csv_res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=alibi_security_audit.csv" in csv_res.headers.get("content-disposition", "")
    content = csv_res.text
    assert "Incident ID,Timestamp,Operating Mode" in content
    assert sample_incident in content

def test_live_vs_demo_mode_boundaries(client, monkeypatch):
    """Verify system honors DEMO vs LIVE boundaries, persists mode switches, and rejects unauthenticated live calls."""
    # 1. Switch to DEMO mode
    demo_res = client.post("/api/mode", json={"mode": "DEMO"})
    assert demo_res.status_code == 200
    assert demo_res.json()["mode"] == "DEMO"

    # 2. Config immediately after must stay in DEMO (cannot be overwritten by .env)
    cfg_res = client.get("/api/config")
    assert cfg_res.status_code == 200
    assert cfg_res.json()["mode"] == "DEMO"

    # 3. In DEMO mode, verification uses SIMULATED provenance and does not call live endpoints
    verif_res = client.post("/api/verify", data={
        "demo_scenario_key": "genuine_approved",
        "speaker_id": "spk_sarah_chen",
        "challenge_phrase": "Alpha Bravo 1234 authorize transfer"
    })
    assert verif_res.status_code == 200
    assert verif_res.json()["provenance"] == "SIMULATED"
    assert verif_res.json()["mode"] == "DEMO"

    # 4. Attempting to switch to LIVE without API key must return 400 with clear error
    monkeypatch.setattr(settings.__class__, "has_api_key", False)
    bad_live_res = client.post("/api/mode", json={"mode": "LIVE"})
    assert bad_live_res.status_code == 400
    assert "Cannot switch to LIVE mode: DetectifAI API key is not configured" in bad_live_res.json()["detail"]

    # Ensure mode stayed in DEMO
    assert client.get("/api/config").json()["mode"] == "DEMO"

    # Calling live verify without key fails with 401
    set_runtime_mode("LIVE")
    live_verify = client.post(
        "/api/verify",
        data={"speaker_id": "spk_sarah_chen"},
        files={"file": ("test.wav", b"dummy" * 500, "audio/wav")}
    )
    assert live_verify.status_code == 401
    assert "API Key is not configured" in live_verify.json()["detail"]

    # 5. When key is present, switching to LIVE succeeds
    monkeypatch.undo()
    set_runtime_mode("DEMO")
    live_ok = client.post("/api/mode", json={"mode": "LIVE"})
    assert live_ok.status_code == 200
    assert live_ok.json()["mode"] == "LIVE"
    assert client.get("/api/config").json()["mode"] == "LIVE"

    # Switching back to DEMO succeeds and stays in DEMO
    back_demo = client.post("/api/mode", json={"mode": "DEMO"})
    assert back_demo.status_code == 200
    assert back_demo.json()["mode"] == "DEMO"
    assert client.get("/api/config").json()["mode"] == "DEMO"
