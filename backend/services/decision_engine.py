from typing import Dict, Any, Optional

class DecisionOutcome:
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    STEP_UP_REQUIRED = "STEP_UP_REQUIRED"

def evaluate_authorization(
    aletheia_verdict: str,
    aletheia_score: float,
    eidos_verdict: Optional[str] = None,
    eidos_score: Optional[float] = None,
    challenge_outcome: Optional[str] = None,
    transfer_amount: Optional[float] = None,
    speaker_id: Optional[str] = None,
    speaker_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluates multi-factor voice fraud detection rules according to strict policy:
    
    1. FAKE audio -> BLOCKED (AI Clone detected, raise CRITICAL alert, offer threat report).
    2. Inconclusive or Missing Aletheia -> STEP_UP_REQUIRED (Aletheia returned 'not_sure' or failed).
    3. REAL audio + EIDOS NO_MATCH -> BLOCKED (Human Impostor, raise HIGH alert, offer threat report).
    4. REAL audio + EIDOS MATCH + CHALLENGE FAILED -> BLOCKED (Suspected Replay Attack, raise HIGH alert).
    5. REAL audio + EIDOS MATCH + CHALLENGE PASSED -> APPROVED (Legitimate transaction authorization).
    6. Any other anomaly or incomplete check -> STEP_UP_REQUIRED (Cannot approve without full verification).
    """
    aletheia_verdict = (aletheia_verdict or "not_sure").lower()
    eidos_verdict = (eidos_verdict or "skipped").lower()
    challenge_outcome = (challenge_outcome or "SKIPPED").upper()

    # Rule 1: Aletheia detects synthetic/deepfake voice
    if aletheia_verdict == "fake":
        return {
            "decision": DecisionOutcome.BLOCKED,
            "alert": True,
            "recommend_threat_report": True,
            "attack_type": "ai_clone",
            "severity": "CRITICAL",
            "reason": f"AI-generated synthetic voice detected by Aletheia (confidence score: {aletheia_score:.3f}). Authorization terminated.",
            "stages": {
                "deepfake_detection": {"status": "FAILED", "detail": "Synthetic acoustic fingerprints detected."},
                "speaker_verification": {"status": "SKIPPED", "detail": "Halted due to synthetic audio detection."},
                "liveness_challenge": {"status": "SKIPPED", "detail": "Halted due to synthetic audio detection."}
            }
        }

    # Rule 2: Aletheia is inconclusive ('not_sure') or encountered an error
    if aletheia_verdict in ("not_sure", "error", "unknown"):
        return {
            "decision": DecisionOutcome.STEP_UP_REQUIRED,
            "alert": False,
            "recommend_threat_report": False,
            "attack_type": "unknown",
            "severity": "MEDIUM",
            "reason": "Deepfake detection verdict was inconclusive ('not_sure'). Additional acoustic sample or multi-factor authentication required.",
            "stages": {
                "deepfake_detection": {"status": "INCONCLUSIVE", "detail": "Aletheia returned 'not_sure' (audio quality or model confidence threshold)."},
                "speaker_verification": {"status": "PENDING", "detail": "Awaiting clear liveness check."},
                "liveness_challenge": {"status": "PENDING", "detail": "Awaiting re-test."}
            }
        }

    # If Aletheia is not 'real', we cannot proceed
    if aletheia_verdict != "real":
        return {
            "decision": DecisionOutcome.STEP_UP_REQUIRED,
            "alert": False,
            "recommend_threat_report": False,
            "attack_type": "unknown",
            "severity": "LOW",
            "reason": f"Aletheia returned unrecognized status '{aletheia_verdict}'. Re-verification required.",
            "stages": {
                "deepfake_detection": {"status": "ERROR", "detail": f"Unrecognized verdict: {aletheia_verdict}"},
                "speaker_verification": {"status": "SKIPPED", "detail": "Prerequisites not met."},
                "liveness_challenge": {"status": "SKIPPED", "detail": "Prerequisites not met."}
            }
        }

    # At this point, audio acoustics are genuine human speech ('real')
    # Rule 3: Check Speaker Verification (Eidos)
    if eidos_verdict in ("no_match", "mismatch"):
        return {
            "decision": DecisionOutcome.BLOCKED,
            "alert": True,
            "recommend_threat_report": True,
            "attack_type": "human_impostor",
            "severity": "HIGH",
            "reason": f"Audio is genuine human voice, but acoustic voiceprint does not match the enrolled profile for '{speaker_name or speaker_id}'.",
            "stages": {
                "deepfake_detection": {"status": "PASSED", "detail": "Natural human acoustic signature verified."},
                "speaker_verification": {"status": "FAILED", "detail": f"Voiceprint mismatch (score: {eidos_score or 0:.3f})."},
                "liveness_challenge": {"status": "SKIPPED", "detail": "Halted due to identity verification failure."}
            }
        }

    if eidos_verdict in ("error", "inconclusive", "skipped"):
        return {
            "decision": DecisionOutcome.STEP_UP_REQUIRED,
            "alert": False,
            "recommend_threat_report": False,
            "attack_type": "unknown",
            "severity": "LOW",
            "reason": "Speaker biometric verification could not be completed. Speaker identity unconfirmed.",
            "stages": {
                "deepfake_detection": {"status": "PASSED", "detail": "Natural human acoustics."},
                "speaker_verification": {"status": "INCONCLUSIVE", "detail": f"Speaker verification status: {eidos_verdict}"},
                "liveness_challenge": {"status": "SKIPPED", "detail": "Identity must be verified before approval."}
            }
        }

    # At this point, Aletheia is REAL and Eidos is MATCH.
    # Rule 4 & 5: Check Fresh Spoken Challenge
    # Speaker match alone is NEVER proof that audio is genuine or safe from replay.
    if challenge_outcome not in ("PASSED", "MANUAL_VERIFIED"):
        return {
            "decision": DecisionOutcome.BLOCKED,
            "alert": True,
            "recommend_threat_report": True,
            "attack_type": "replay",
            "severity": "HIGH",
            "reason": "Acoustic deepfake check and speaker biometric voiceprint passed, but the caller failed the fresh dynamic challenge phrase. Suspected replay attack or recorded snippet.",
            "stages": {
                "deepfake_detection": {"status": "PASSED", "detail": "Natural human acoustics."},
                "speaker_verification": {"status": "PASSED", "detail": f"Biometric voiceprint matched (score: {eidos_score or 1.0:.3f})."},
                "liveness_challenge": {"status": "FAILED", "detail": "Fresh spoken challenge response was missing, invalid, or mismatched."}
            }
        }

    # Rule 6: REAL + MATCH + CHALLENGE PASSED
    return {
        "decision": DecisionOutcome.APPROVED,
        "alert": False,
        "recommend_threat_report": False,
        "attack_type": None,
        "severity": None,
        "reason": f"Authorized: Genuine human voice verified by Aletheia, biometric identity confirmed by Eidos for '{speaker_name or speaker_id}', and dynamic spoken challenge validated.",
        "stages": {
            "deepfake_detection": {"status": "PASSED", "detail": "Authentic human speech verified."},
            "speaker_verification": {"status": "PASSED", "detail": f"Enrolled voiceprint matched (score: {eidos_score or 1.0:.3f})."},
            "liveness_challenge": {"status": "PASSED", "detail": f"Spoken phrase confirmed ({challenge_outcome})."}
        }
    }
