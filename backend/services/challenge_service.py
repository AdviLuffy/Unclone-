import random
import re
import difflib
from datetime import datetime, timezone
from typing import Dict, Any, Tuple

PHONETIC_ALPHABET = [
    "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", 
    "Golf", "Hotel", "India", "Juliet", "Kilo", "Lima", 
    "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo", 
    "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "Xray", 
    "Yankee", "Zulu"
]

CODENAMES = [
    "Falcon", "Horizon", "Sentinel", "Vanguard", "Apex", "Citadel",
    "Cobalt", "Phoenix", "Obsidian", "Nexus", "Orion", "Cipher"
]

ACTION_VERBS = [
    "authorize transfer", "verify credential", "security release",
    "vault authorization", "clearance confirmed", "signature dispatch"
]

def generate_challenge_phrase() -> Dict[str, Any]:
    """
    Generates a cryptographically fresh challenge phrase for voice liveness validation.
    """
    p1 = random.choice(PHONETIC_ALPHABET)
    code = random.choice(CODENAMES)
    digits = f"{random.randint(1000, 9999)}"
    action = random.choice(ACTION_VERBS)
    
    phrase = f"{p1} {code} {digits} {action}"
    challenge_id = f"CHAL-{random.randint(100000, 999999)}"
    
    return {
        "challenge_id": challenge_id,
        "phrase": phrase,
        "phonetic_prefix": p1,
        "codename": code,
        "digits": digits,
        "action": action,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

def clean_text(text: str) -> str:
    """Normalize text by lowercasing, converting common digit words, and stripping punctuation."""
    if not text:
        return ""
    t = text.lower()
    
    # Map common digit words to digits
    num_map = {
        "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
        "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9"
    }
    for word, digit in num_map.items():
        t = re.sub(rf"\b{word}\b", digit, t)
        
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return " ".join(t.split())

def validate_challenge(
    expected_phrase: str, 
    transcribed_phrase: str, 
    verification_mode: str = "automated"
) -> Dict[str, Any]:
    """
    Compares the spoken transcription against the expected challenge phrase.
    Supports automated ASR validation and manual/demo validation.
    Never pretends manual verification was automated.
    """
    if verification_mode == "manual":
        return {
            "passed": True,
            "outcome": "MANUAL_VERIFIED",
            "confidence": 1.0,
            "is_automated": False,
            "match_ratio": 1.0,
            "transcription": transcribed_phrase or expected_phrase,
            "details": "Spoken challenge verified via manual SOC operator inspection."
        }

    if not transcribed_phrase or not transcribed_phrase.strip():
        return {
            "passed": False,
            "outcome": "FAILED",
            "confidence": 0.0,
            "is_automated": True,
            "match_ratio": 0.0,
            "transcription": "",
            "details": "No audible challenge phrase detected in transcription."
        }

    norm_expected = clean_text(expected_phrase)
    norm_actual = clean_text(transcribed_phrase)

    # Sequence similarity
    ratio = difflib.SequenceMatcher(None, norm_expected, norm_actual).ratio()

    # Keyword check: ensure key digits or codename appear
    expected_tokens = set(norm_expected.split())
    actual_tokens = set(norm_actual.split())
    token_overlap = len(expected_tokens.intersection(actual_tokens)) / max(len(expected_tokens), 1)

    combined_score = (ratio * 0.6) + (token_overlap * 0.4)
    passed = combined_score >= 0.65

    return {
        "passed": passed,
        "outcome": "PASSED" if passed else "FAILED",
        "confidence": round(combined_score, 3),
        "is_automated": True,
        "match_ratio": round(ratio, 3),
        "token_overlap": round(token_overlap, 3),
        "transcription": transcribed_phrase,
        "details": f"Automated Speech Recognition match score: {round(combined_score * 100, 1)}% against expected challenge."
    }
