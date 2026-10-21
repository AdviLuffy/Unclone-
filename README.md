# ALIBI - Voice Fraud Firewall & Secure Authorization Engine

> **A high-security voice authorization platform built for hackathon demonstration.**  
> ALIBI protects high-value operations by detecting AI-generated synthetic speech, verifying speaker biometrics, enforcing dynamic spoken challenge liveness, and recording immutable audit decisions.

---

##  Architecture & Core Components

```
                   ┌──────────────────────────────────────────────┐
                   │          Browser Microphone / Audio          │
                   │      MediaRecorder API + Web Speech STT      │
                   └──────────────────────┬───────────────────────┘
                                          │ Audio (multipart/form-data)
                                          ▼
                   ┌──────────────────────────────────────────────┐
                   │             ALIBI API Firewall               │
                   │           (Python FastAPI Backend)           │
                   └──────┬───────────────┬────────────────┬──────┘
                          │               │                │
            Stage 1       │ Stage 2       │ Stage 3        │ Stage 4
            ▼             │ ▼             │ ▼              │ ▼
┌──────────────────────┐  │┌──────────────┴───────┐ ┌──────┴───────────────┐ ┌─────────────────────────┐
│  Aletheia Deepfake   │  ││   Eidos Biometrics   │ │   Dynamic Liveness   │ │   Decision Engine       │
│  Detection Engine    │  ││   Speaker Identity   │ │   Spoken Challenge   │ │   Multi-Factor Rules    │
│  (DetectifAI API)    │  ││   (DetectifAI API)   │ │   (Nonce Phrase STT) │ │   Zero-Trust Matrix     │
└──────────┬───────────┘  │└──────────────┬───────┘ └──────┬───────────────┘ └───────────┬─────────────┘
           │              │               │                │                             │
           └──────────────┴───────────────┴────────────────┴─────────────────────────────┤
                                                                                         ▼
                                                                       ┌─────────────────────────────────┐
                                                                       │       Authorization Verdict     │
                                                                       │  APPROVED  |  BLOCKED  | STEP-UP│
                                                                       └────────────────┬────────────────┘
                                                                                        │
                                               ┌────────────────────────────────────────┴────────────────────────────────┐
                                               ▼                                                                         ▼
                               ┌───────────────────────────────┐                                         ┌───────────────────────────────┐
                               │   Legitimate Authorization    │                                         │      Phantom Mode Trigger     │
                               │   Simulated Vault Transfer    │                                         │   Decoy Receipt (Attacker)    │
                               │   Funds Safely Settled        │                                         │   Internal Vault Lock (SOC)   │
                               └───────────────────────────────┘                                         │   Post to r/VoiceThreatNet    │
                                                                                                         └───────────────────────────────┘
```

---

##  Key Features

1. **Institutional Security Dashboard**:
   - Premium minimalist black design system (`#050505`, `#0A0A0A`, `#101010`, `#242424`), clean sans-serif typography, tabular numerals, monochrome SVG iconography, and responsive controls.
   - Operating mode switcher prominently displayed: **LIVE API** vs **DEMO SIMULATION**.
   - Real-time telemetry: funds protected, deepfakes intercepted, enrolled voiceprints.

2. **Multi-Factor Voice Verification Pipeline**:
   - Real browser microphone recording using HTML5 `MediaRecorder` with real-time waveform visualizer canvas and audio playback preview.
   - **Stage 1 (Aletheia)**: Deepfake detection analyzing vocoder artifacts, acoustic glitches, and synthetic probability.
   - **Stage 2 (Eidos)**: Voiceprint biometric match against enrolled executive profiles.
   - **Stage 3 (Dynamic Challenge)**: High-entropy phonetic nonce phrase (e.g. `Delta Falcon 4892 authorize transfer`) validated via speech-to-text recognition to neutralize recorded replay attacks.

3. **Strict Authorization Decision Matrix**:
   - **FAKE Audio** &rarr; Immediate `BLOCKED` with `CRITICAL` alert and prompt to file a threat report.
   - **Inconclusive (`not_sure`)** &rarr; `STEP_UP_REQUIRED`; never treats inconclusive audio as genuine.
   - **REAL Audio + Speaker Mismatch** &rarr; `BLOCKED` as Human Impostor with `HIGH` alert.
   - **REAL Audio + Speaker Match + Challenge Failed** &rarr; `BLOCKED` as Suspected Replay Attack with `HIGH` alert.
   - **REAL Audio + Speaker Match + Challenge Passed** &rarr; `APPROVED`.
   - *Speaker match alone is never treated as proof audio is genuine.*

4. **Speaker Biometric Enrollment**:
   - Enrolls authorized executives into Eidos with mandatory biometric consent verification.
   - Supports live microphone recording or file uploads.
   - Directory view displaying active signatories, sample counts, and enrollment timestamps.

5. **Phantom Mode (Deceptive Defense Bank Simulator)**:
   - Fictional banking sandbox (*Apex Horizon Trust* wire transfer simulator).
   - When voice fraud is intercepted, the attacker terminal receives a convincing **Decoy Phantom Receipt** (`FW-PHANTOM-XXXX-TRACE`), while the internal SOC vault is placed in **EMERGENCY LOCKDOWN** and funds remain safe.

6. **Threat Intelligence Feed (r/VoiceThreatNet)**:
   - Reddit-style consortium intelligence feed for audio deepfake signatures.
   - Upvoting, severity filters (`CRITICAL`, `HIGH`, `MEDIUM`), category tags, and search.
   - SOC moderator actions (`Verify Incident`, `Flag`, `Dismiss`).
   - Automatically sanitizes submissions to store safe metadata only (no raw audio or secrets).

7. **Persistent Audit History**:
   - SQLite-backed immutable security log tracking Incident ID, Timestamp, Mode, Aletheia verdict, Eidos score, Challenge outcome, and Final Policy Decision.
   - One-click CSV export for compliance and post-incident review.

---

## Tech Stack

- **Backend**: Python 3.14+, FastAPI, Starlette, Uvicorn, SQLite, HTTPX, Pydantic, Pytest.
- **Frontend**: Vanilla HTML5/CSS3/JavaScript (No complex build step, lightweight, low-latency, responsive).
- **APIs**: DetectifAI Platform (`https://platform.detectif.ai`) — Aletheia & Eidos.

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Git

### 2. Clone and Setup Environment

```bash
git clone https://github.com/your-org/alibi.git
cd alibi

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (CMD):
.\.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your credentials inside `.env`:

```env
# Operating Mode: "DEMO" or "LIVE"
ALIBI_MODE=DEMO

# DetectifAI Platform Credentials
# Get your API key from https://platform.detectif.ai
DETECTIF_API_KEY=your_detectif_api_key_here
DETECTIF_BASE_URL=https://platform.detectif.ai

# Server settings
HOST=127.0.0.1
PORT=8000
DATABASE_URL=sqlite:///./alibi.db
CHALLENGE_VERIFY_MODE=stt
```

---

##  Running the Application

### Single Command (FastAPI serves both API and Frontend):

```bash
# Windows
.\.venv\Scripts\uvicorn.exe backend.main:app --host 127.0.0.1 --port 8000 --reload

# Linux / macOS
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Open your browser and navigate to:  
 **`http://localhost:8000`**

---

## Running Tests

The test suite thoroughly covers all decision matrix branches, failure modes, and API routes:

```bash
# Run all tests
.\.venv\Scripts\pytest.exe -v
```

Test coverage includes:
- FAKE audio blocks and critical alert (`ai_clone`)
- Inconclusive Aletheia (`not_sure`) step-up requirement
- Genuine audio + speaker mismatch (`human_impostor`)
- Genuine audio + speaker match + challenge failed (`replay`)
- All factors verified &rarr; approved
- Biometric consent enforcement during enrollment
- Phantom Mode deceptive receipt and simulated vault lockdown
- Threat report creation and moderation
- Audit log tracking and CSV export

---

## 🔌 DetectifAI Platform API Integration Status

| Service | Endpoint | Method | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Aletheia Deepfake** | `/v1/deepfake/detect` | `POST` | **Fully Implemented** | Uses `multipart/form-data` with `file` field, `Idempotency-Key` header, and Bearer auth. Evaluated in Live mode when API key is set; simulated in Demo mode. |
| **Eidos Enrollment** | `/v1/speakers/enroll` | `POST` | **Fully Implemented** | Uses `speaker_id` & `file` fields with biometric consent validation. Enforces audio length rules (15-60s) in Live mode; creates clearly labeled fictional profiles in Demo mode. |
| **Eidos Verification**| `/v1/speakers/verify` | `POST` | **Fully Implemented** | Matches speaker voiceprint against enrolled profile. Returns match status, cosine score, and threshold. |
| **Speaker Directory** | `/v1/speakers` | `GET` | **Fully Implemented** | Used for connection ping and listing account speakers. |

> [!NOTE]  
> In DEMO mode, ALIBI runs 100% offline without requiring external API keys or network requests. In LIVE mode, requests are securely routed through server-side handlers to `platform.detectif.ai` with client-masked credentials.



 
