import uuid
from typing import Dict, Any

DEMO_SCENARIOS = {
    "ai_clone": {
        "id": "scenario_ai_clone",
        "name": "Scenario 1: AI Voice Deepfake Clone",
        "description": "Simulates an attacker using a fine-tuned XTTS/ElevenLabs voice clone of CFO Sarah Chen requesting an urgent $250,000 wire transfer.",
        "expected_verdict": "BLOCKED",
        "provenance": "SIMULATED",
        "aletheia": {
            "verdict": "fake",
            "score": 0.988,
            "request_id": "sim_aletheia_fake_9912",
            "raw": {"status": "success", "synthetic_probability": 0.988, "artifacts": ["vocoder_glitch", "phase_distortion"], "is_simulated": True}
        },
        "eidos": {
            "match": False,
            "verdict": "skipped",
            "score": 0.0,
            "threshold": 0.70,
            "request_id": None
        },
        "challenge": {
            "passed": False,
            "outcome": "SKIPPED",
            "transcription": "Halted by deepfake engine"
        }
    },
    "genuine_approved": {
        "id": "scenario_genuine_approved",
        "name": "Scenario 2: Genuine Speaker + Verified Liveness",
        "description": "Simulates genuine executive audio with authentic acoustics, matching biometric profile and fresh challenge response.",
        "expected_verdict": "APPROVED",
        "provenance": "SIMULATED",
        "aletheia": {
            "verdict": "real",
            "score": 0.021,
            "request_id": "sim_aletheia_real_4412",
            "raw": {"status": "success", "synthetic_probability": 0.021, "is_simulated": True}
        },
        "eidos": {
            "match": True,
            "verdict": "match",
            "score": 0.942,
            "threshold": 0.70,
            "request_id": "sim_eidos_match_3311"
        },
        "challenge": {
            "passed": True,
            "outcome": "PASSED",
            "transcription": "Matched dynamic security challenge"
        }
    },
    "human_impostor": {
        "id": "scenario_human_impostor",
        "name": "Scenario 3: Genuine Voice + Impostor Mismatch",
        "description": "Simulates natural human speech (passes deepfake detector), but acoustic voiceprint does not match the enrolled speaker.",
        "expected_verdict": "BLOCKED",
        "provenance": "SIMULATED",
        "aletheia": {
            "verdict": "real",
            "score": 0.035,
            "request_id": "sim_aletheia_real_7781",
            "raw": {"status": "success", "synthetic_probability": 0.035, "is_simulated": True}
        },
        "eidos": {
            "match": False,
            "verdict": "no_match",
            "score": 0.285,
            "threshold": 0.70,
            "request_id": "sim_eidos_mismatch_8819"
        },
        "challenge": {
            "passed": True,
            "outcome": "PASSED",
            "transcription": "Correct challenge spoken by unauthorized person"
        }
    },
    "inconclusive": {
        "id": "scenario_inconclusive",
        "name": "Scenario 4: Inconclusive Aletheia ('not_sure')",
        "description": "Simulates noisy acoustic environment where Aletheia returns inconclusive 'not_sure' verdict requiring step-up authentication.",
        "expected_verdict": "STEP_UP_REQUIRED",
        "provenance": "SIMULATED",
        "aletheia": {
            "verdict": "not_sure",
            "score": 0.512,
            "request_id": "sim_aletheia_inconclusive_1029",
            "raw": {"status": "inconclusive", "verdict": "not_sure", "confidence": 0.512, "is_simulated": True}
        },
        "eidos": {
            "match": False,
            "verdict": "inconclusive",
            "score": 0.0,
            "threshold": 0.70,
            "request_id": None
        },
        "challenge": {
            "passed": False,
            "outcome": "PENDING",
            "transcription": "Re-test required"
        }
    }
}

def get_demo_scenario(scenario_key: str) -> Dict[str, Any]:
    if scenario_key not in DEMO_SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario_key}'. Choose from: {list(DEMO_SCENARIOS.keys())}")
    return DEMO_SCENARIOS[scenario_key]

def list_demo_scenarios():
    return [
        {
            "key": k,
            "name": v["name"],
            "description": v["description"],
            "expected_verdict": v["expected_verdict"],
            "provenance": v["provenance"]
        }
        for k, v in DEMO_SCENARIOS.items()
    ]
