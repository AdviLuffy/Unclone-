import uuid
import logging
import httpx
from typing import Dict, Any, Optional
from backend.config import settings

logger = logging.getLogger("alibi.detectifai")

class DetectifAIError(Exception):
    def __init__(self, message: str, status_code: int = 500, error_code: str = "detectif_error", details: Any = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details

class DetectifAIService:
    def __init__(self):
        self.base_url = settings.detectif_base_url
        self.timeout = settings.request_timeout_seconds

    def _get_headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        headers = {}
        if settings.detectif_api_key:
            headers["Authorization"] = f"Bearer {settings.detectif_api_key.strip()}"
        headers["Idempotency-Key"] = idempotency_key or str(uuid.uuid4())
        return headers

    async def detect_deepfake(self, file_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
        """
        Calls DetectifAI Aletheia: POST /v1/deepfake/detect
        Multipart field: 'file'
        Returns normalized representation:
        {
            "verdict": "real" | "fake" | "not_sure" | "error",
            "score": float,
            "request_id": str,
            "raw": dict,
            "error": Optional[str]
        }
        """
        if not settings.has_api_key:
            raise DetectifAIError("DetectifAI API Key is not configured. Switch to DEMO mode or configure DETECTIF_API_KEY in .env.", status_code=401, error_code="missing_credentials")

        url = f"{self.base_url}/v1/deepfake/detect"
        headers = self._get_headers()
        files = {"file": (filename, file_bytes, "audio/wav")}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, files=files)
                
            if response.status_code == 401 or response.status_code == 403:
                raise DetectifAIError("DetectifAI Authorization Failed: Invalid or expired API key", status_code=response.status_code, error_code="auth_failed")
            
            if response.status_code == 402 or response.status_code == 429:
                raise DetectifAIError("DetectifAI Platform limit: Insufficient credits or rate limit exceeded", status_code=response.status_code, error_code="quota_exceeded")
            
            if response.status_code == 422 or response.status_code == 400:
                err_text = response.text
                raise DetectifAIError(f"DetectifAI Rejected Audio: {err_text}", status_code=response.status_code, error_code="invalid_audio_input")

            if response.status_code >= 500:
                raise DetectifAIError(f"DetectifAI Service Unavailable (HTTP {response.status_code})", status_code=response.status_code, error_code="service_unavailable")

            data = response.json()
            request_id = data.get("request_id") or response.headers.get("x-request-id") or str(uuid.uuid4())
            result = data.get("result", {})
            
            raw_verdict = str(result.get("verdict", "")).lower()
            if raw_verdict in ("real", "fake", "not_sure"):
                verdict = raw_verdict
            else:
                verdict = "not_sure"

            score = float(result.get("score", result.get("confidence", 0.5)))

            return {
                "verdict": verdict,
                "score": score,
                "request_id": request_id,
                "raw": data
            }

        except httpx.TimeoutException:
            logger.error("DetectifAI Aletheia request timed out")
            raise DetectifAIError("DetectifAI API request timed out after 15 seconds", status_code=504, error_code="api_timeout")
        except httpx.RequestError as e:
            logger.error(f"DetectifAI connection failure: {e}")
            raise DetectifAIError(f"Failed to connect to DetectifAI platform: {str(e)}", status_code=502, error_code="connection_error")

    async def enroll_speaker(self, speaker_id: str, file_bytes: bytes, filename: str = "enroll.wav") -> Dict[str, Any]:
        """
        Calls DetectifAI Eidos: POST /v1/speakers/enroll
        Multipart fields: 'speaker_id', 'file'
        """
        if not settings.has_api_key:
            raise DetectifAIError("DetectifAI API Key is not configured for Live enrollment.", status_code=401, error_code="missing_credentials")

        url = f"{self.base_url}/v1/speakers/enroll"
        headers = self._get_headers()
        files = {"file": (filename, file_bytes, "audio/wav")}
        data_payload = {"speaker_id": speaker_id}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, data=data_payload, files=files)

            if response.status_code in (401, 403):
                raise DetectifAIError("DetectifAI Authorization Failed", status_code=response.status_code, error_code="auth_failed")
            if response.status_code == 409:
                raise DetectifAIError(f"Speaker '{speaker_id}' has reached the maximum of 5 enrolled voice samples", status_code=409, error_code="too_many_samples")
            if response.status_code == 422:
                raise DetectifAIError(f"Audio does not meet enrollment criteria: {response.text}. (Enrollment audio must be 15-60s with >=10s active speech)", status_code=422, error_code="invalid_enrollment_audio")
            if response.status_code >= 400:
                raise DetectifAIError(f"Eidos enrollment failed (HTTP {response.status_code}): {response.text}", status_code=response.status_code, error_code="enrollment_error")

            res_json = response.json()
            return {
                "speaker_id": speaker_id,
                "status": "enrolled",
                "request_id": res_json.get("request_id") or response.headers.get("x-request-id") or str(uuid.uuid4()),
                "raw": res_json
            }
        except httpx.TimeoutException:
            raise DetectifAIError("Eidos enrollment request timed out", status_code=504, error_code="api_timeout")
        except httpx.RequestError as e:
            raise DetectifAIError(f"Failed to connect to Eidos service: {str(e)}", status_code=502, error_code="connection_error")

    async def verify_speaker(self, speaker_id: str, file_bytes: bytes, filename: str = "verify.wav") -> Dict[str, Any]:
        """
        Calls DetectifAI Eidos: POST /v1/speakers/verify
        Multipart fields: 'speaker_id', 'file'
        Returns normalized representation:
        {
            "match": bool,
            "verdict": "match" | "no_match" | "inconclusive",
            "score": float,
            "threshold": float,
            "request_id": str,
            "raw": dict
        }
        """
        if not settings.has_api_key:
            raise DetectifAIError("DetectifAI API Key is not configured for Live verification.", status_code=401, error_code="missing_credentials")

        url = f"{self.base_url}/v1/speakers/verify"
        headers = self._get_headers()
        files = {"file": (filename, file_bytes, "audio/wav")}
        data_payload = {"speaker_id": speaker_id}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, data=data_payload, files=files)

            if response.status_code in (401, 403):
                raise DetectifAIError("DetectifAI Authorization Failed", status_code=response.status_code, error_code="auth_failed")
            if response.status_code == 404:
                raise DetectifAIError(f"Speaker '{speaker_id}' not found on Eidos voiceprint registry", status_code=404, error_code="speaker_not_found")
            if response.status_code >= 400:
                raise DetectifAIError(f"Eidos verification failed (HTTP {response.status_code}): {response.text}", status_code=response.status_code, error_code="verification_error")

            data = response.json()
            result = data.get("result", {})
            score = float(result.get("score", 0.0))
            threshold = float(result.get("threshold", settings.speaker_match_threshold))
            
            # Check match boolean or score against threshold
            is_match = bool(result.get("match", score >= threshold))
            verdict = "match" if is_match else "no_match"

            return {
                "match": is_match,
                "verdict": verdict,
                "score": score,
                "threshold": threshold,
                "request_id": data.get("request_id") or response.headers.get("x-request-id") or str(uuid.uuid4()),
                "raw": data
            }
        except httpx.TimeoutException:
            raise DetectifAIError("Eidos verification timed out", status_code=504, error_code="api_timeout")
        except httpx.RequestError as e:
            raise DetectifAIError(f"Failed to connect to Eidos service: {str(e)}", status_code=502, error_code="connection_error")

detectifai_service = DetectifAIService()
