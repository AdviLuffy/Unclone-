import pytest
from backend.services.decision_engine import evaluate_authorization, DecisionOutcome

def test_rule_1_fake_audio_blocks_and_alerts():
    """Branch 1: FAKE audio detected by Aletheia must be BLOCKED with CRITICAL alert and threat report offer."""
    res = evaluate_authorization(
        aletheia_verdict="fake",
        aletheia_score=0.985,
        eidos_verdict="match",
        challenge_outcome="PASSED",
        speaker_id="spk_sarah_chen",
        speaker_name="Sarah Chen"
    )
    assert res["decision"] == DecisionOutcome.BLOCKED
    assert res["alert"] is True
    assert res["recommend_threat_report"] is True
    assert res["attack_type"] == "ai_clone"
    assert res["severity"] == "CRITICAL"
    assert "synthetic voice detected" in res["reason"]

def test_rule_2_inconclusive_aletheia_step_up():
    """Branch 2: Inconclusive Aletheia ('not_sure') requires step-up, not approved and not fake."""
    res = evaluate_authorization(
        aletheia_verdict="not_sure",
        aletheia_score=0.51,
        eidos_verdict="match",
        challenge_outcome="PASSED"
    )
    assert res["decision"] == DecisionOutcome.STEP_UP_REQUIRED
    assert res["alert"] is False
    assert res["recommend_threat_report"] is False
    assert "inconclusive" in res["reason"]

def test_rule_3_real_audio_speaker_mismatch_blocks():
    """Branch 3: Genuine human acoustics but voiceprint mismatch must be BLOCKED as Human Impostor."""
    res = evaluate_authorization(
        aletheia_verdict="real",
        aletheia_score=0.03,
        eidos_verdict="no_match",
        eidos_score=0.25,
        challenge_outcome="PASSED",
        speaker_name="Marcus Vance"
    )
    assert res["decision"] == DecisionOutcome.BLOCKED
    assert res["alert"] is True
    assert res["recommend_threat_report"] is True
    assert res["attack_type"] == "human_impostor"
    assert res["severity"] == "HIGH"
    assert "does not match the enrolled profile" in res["reason"]

def test_rule_4_real_speaker_match_challenge_failed_blocks():
    """Branch 4: Genuine acoustics + speaker match + FAILED challenge must be BLOCKED as Suspected Replay."""
    res = evaluate_authorization(
        aletheia_verdict="real",
        aletheia_score=0.02,
        eidos_verdict="match",
        eidos_score=0.92,
        challenge_outcome="FAILED",
        speaker_name="Dr. Elena Rostova"
    )
    assert res["decision"] == DecisionOutcome.BLOCKED
    assert res["alert"] is True
    assert res["recommend_threat_report"] is True
    assert res["attack_type"] == "replay"
    assert res["severity"] == "HIGH"
    assert "failed the fresh dynamic challenge phrase" in res["reason"]

def test_rule_5_all_factors_passed_approves():
    """Branch 5: REAL audio + EIDOS MATCH + CHALLENGE PASSED must APPROVE."""
    res = evaluate_authorization(
        aletheia_verdict="real",
        aletheia_score=0.015,
        eidos_verdict="match",
        eidos_score=0.95,
        challenge_outcome="PASSED",
        speaker_name="Sarah Chen"
    )
    assert res["decision"] == DecisionOutcome.APPROVED
    assert res["alert"] is False
    assert res["recommend_threat_report"] is False
    assert res["attack_type"] is None
    assert "Authorized:" in res["reason"]

def test_rule_5b_manual_verified_challenge_approves():
    """Branch 5b: MANUAL_VERIFIED challenge outcome also approves when clearly labeled."""
    res = evaluate_authorization(
        aletheia_verdict="real",
        aletheia_score=0.015,
        eidos_verdict="match",
        eidos_score=0.95,
        challenge_outcome="MANUAL_VERIFIED",
        speaker_name="Sarah Chen"
    )
    assert res["decision"] == DecisionOutcome.APPROVED
    assert res["alert"] is False

def test_rule_6_speaker_match_alone_does_not_approve():
    """Verification principle: Speaker match alone is NEVER proof that audio is genuine."""
    # Even if speaker matched, if Aletheia was FAKE, it MUST block:
    res = evaluate_authorization(
        aletheia_verdict="fake",
        aletheia_score=0.99,
        eidos_verdict="match",
        eidos_score=0.99,
        challenge_outcome="PASSED"
    )
    assert res["decision"] == DecisionOutcome.BLOCKED
    assert res["attack_type"] == "ai_clone"

def test_missing_or_error_verdicts_cannot_approve():
    """Any missing, unknown, or errored model response must not approve."""
    res1 = evaluate_authorization(aletheia_verdict="error", aletheia_score=0.0)
    assert res1["decision"] == DecisionOutcome.STEP_UP_REQUIRED

    res2 = evaluate_authorization(aletheia_verdict="real", aletheia_score=0.02, eidos_verdict="error")
    assert res2["decision"] == DecisionOutcome.STEP_UP_REQUIRED

    res3 = evaluate_authorization(aletheia_verdict="real", aletheia_score=0.02, eidos_verdict="match", challenge_outcome="SKIPPED")
    assert res3["decision"] == DecisionOutcome.BLOCKED
