/**
 * ALIBI - Voice Fraud Detection & Secure Authorization Engine
 * Frontend Controller & Real-Time Orchestration
 */

// Application State
const state = {
  mode: "DEMO",
  isLive: false,
  hasApiKey: false,
  activePage: "page-overview",
  enrolledSpeakers: [],
  currentChallenge: null,
  recordedBlob: null,
  recordedAudioUrl: null,
  mediaRecorder: null,
  audioChunks: [],
  recordingTimer: null,
  recordingSeconds: 0,
  maxRecordingSeconds: 15,
  speechRecognition: null,
  speechTranscript: "",
  lastVerificationResult: null,
  audioContext: null,
  analyser: null,
  animFrameId: null
};

// DOM Elements & Initialization
document.addEventListener("DOMContentLoaded", async () => {
  setupNavigation();
  setupAudioRecorder();
  setupSpeechRecognition();
  setupModals();
  setupEventListeners();
  setupKineticTypography();

  // Load initial backend telemetry & data
  await refreshSystemConfig();
  await refreshSpeakers();
  await fetchNewChallenge();
  await refreshThreatFeed();
  await refreshAuditLogs();
  await refreshSimulatorVault();
});

// ============================================================================
// 1. TWO-TIER NAVIGATION & CONSOLE ROUTING
// ============================================================================
function setupNavigation() {
  // Console tab navigation
  const consoleTabs = document.querySelectorAll(".console-tab");
  consoleTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetPageId = tab.getAttribute("data-page");
      navigateToPage(targetPageId);
    });
  });

  // Legacy nav tabs if present
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetPageId = tab.getAttribute("data-page");
      navigateToPage(targetPageId);
    });
  });
}

function openSecurityConsole(subpageId = "page-overview") {
  const landingView = document.getElementById("view-landing");
  const consoleView = document.getElementById("view-console");
  const toggleLabel = document.getElementById("dockConsoleToggleLabel");
  const toggleBtn = document.getElementById("dockBtnConsoleToggle");

  if (landingView) landingView.style.display = "none";
  if (consoleView) {
    consoleView.classList.add("active");
    consoleView.style.display = "block";
  }
  if (toggleLabel) toggleLabel.textContent = "Overview";
  if (toggleBtn) toggleBtn.classList.add("active");

  navigateToPage(subpageId);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function exitSecurityConsole() {
  const landingView = document.getElementById("view-landing");
  const consoleView = document.getElementById("view-console");
  const toggleLabel = document.getElementById("dockConsoleToggleLabel");
  const toggleBtn = document.getElementById("dockBtnConsoleToggle");

  if (consoleView) {
    consoleView.classList.remove("active");
    consoleView.style.display = "none";
  }
  if (landingView) {
    landingView.style.display = "block";
  }
  if (toggleLabel) toggleLabel.textContent = "Console";
  if (toggleBtn) toggleBtn.classList.remove("active");

  updateDockActive("home");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function toggleSecurityConsoleView() {
  const consoleView = document.getElementById("view-console");
  const isConsoleActive = consoleView && (consoleView.classList.contains("active") || consoleView.style.display === "block");
  if (isConsoleActive) {
    exitSecurityConsole();
  } else {
    openSecurityConsole(state.activePage || "page-overview");
  }
}

function handleDockNav(targetKey) {
  updateDockActive(targetKey);

  if (targetKey === "home") {
    const consoleView = document.getElementById("view-console");
    if (consoleView && (consoleView.classList.contains("active") || consoleView.style.display === "block")) {
      exitSecurityConsole();
    } else {
      const hero = document.getElementById("hero");
      if (hero) hero.scrollIntoView({ behavior: "smooth" });
    }
  } else if (targetKey === "how-it-works") {
    const consoleView = document.getElementById("view-console");
    if (consoleView && (consoleView.classList.contains("active") || consoleView.style.display === "block")) {
      exitSecurityConsole();
    }
    const section = document.getElementById("how-it-works");
    if (section) section.scrollIntoView({ behavior: "smooth" });
  } else if (targetKey === "verify") {
    openSecurityConsole("page-verify");
  } else if (targetKey === "simulator") {
    openSecurityConsole("page-simulator");
  } else if (targetKey === "threats") {
    openSecurityConsole("page-threats");
  } else if (targetKey === "audit") {
    openSecurityConsole("page-audit");
  }
}

function updateDockActive(targetKey) {
  const dockMap = {
    "home": "dockBtnHome",
    "how-it-works": "dockBtnHowItWorks",
    "verify": "dockBtnVerify",
    "simulator": "dockBtnSimulator",
    "threats": "dockBtnThreats",
    "audit": "dockBtnAudit"
  };

  document.querySelectorAll(".dock-btn").forEach(btn => {
    if (btn.id !== "dockBtnConsoleToggle") {
      btn.classList.remove("active");
    }
  });

  const activeId = dockMap[targetKey];
  if (activeId) {
    const btn = document.getElementById(activeId);
    if (btn) btn.classList.add("active");
  }
}

function navigateToPage(pageId) {
  state.activePage = pageId;

  // If navigating from landing to a console subpage, ensure console wrapper is active
  const consoleView = document.getElementById("view-console");
  const landingView = document.getElementById("view-landing");
  if (consoleView && (!consoleView.classList.contains("active") || consoleView.style.display === "none")) {
    consoleView.classList.add("active");
    consoleView.style.display = "block";
    if (landingView) landingView.style.display = "none";
    const toggleLabel = document.getElementById("dockConsoleToggleLabel");
    if (toggleLabel) toggleLabel.textContent = "Overview";
    const toggleBtn = document.getElementById("dockBtnConsoleToggle");
    if (toggleBtn) toggleBtn.classList.add("active");
  }

  // Update tabs (.console-tab and legacy .nav-tab)
  document.querySelectorAll(".console-tab").forEach(tab => {
    tab.classList.toggle("active", tab.getAttribute("data-page") === pageId);
  });
  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.classList.toggle("active", tab.getAttribute("data-page") === pageId);
  });

  // Update page visibility (.console-subpage and legacy .page-view)
  document.querySelectorAll(".console-subpage").forEach(view => {
    view.classList.toggle("active", view.id === pageId);
  });
  document.querySelectorAll(".page-view").forEach(view => {
    view.classList.toggle("active", view.id === pageId);
  });

  // Sync dock button highlights
  if (pageId === "page-verify") updateDockActive("verify");
  else if (pageId === "page-simulator") updateDockActive("simulator");
  else if (pageId === "page-threats") updateDockActive("threats");
  else if (pageId === "page-audit") updateDockActive("audit");

  // Page-specific refreshes
  if (pageId === "page-threats") refreshThreatFeed();
  if (pageId === "page-audit") refreshAuditLogs();
  if (pageId === "page-simulator") refreshSimulatorVault();
  if (pageId === "page-enrollment") refreshSpeakers();
}

// Kinetic typography decode animation
function setupKineticTypography() {
  const title = document.getElementById("kineticAlibiTitle");
  if (!title) return;

  const originalWord = "ALIBI";
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789%#$&";
  const letters = title.querySelectorAll(".letter");

  function triggerDecode() {
    letters.forEach((el, index) => {
      let iteration = 0;
      const targetChar = originalWord[index] || el.textContent;
      const interval = setInterval(() => {
        el.textContent = chars[Math.floor(Math.random() * chars.length)];
        if (iteration >= 6 + index * 3) {
          clearInterval(interval);
          el.textContent = targetChar;
        }
        iteration++;
      }, 35);
    });
  }

  // Initial trigger after brief delay
  setTimeout(triggerDecode, 350);

  // Trigger on hover
  title.addEventListener("mouseenter", triggerDecode);
}

// Expose handlers to global window scope for inline onclick handlers
window.openSecurityConsole = openSecurityConsole;
window.exitSecurityConsole = exitSecurityConsole;
window.toggleSecurityConsoleView = toggleSecurityConsoleView;
window.handleDockNav = handleDockNav;
window.updateDockActive = updateDockActive;
window.navigateToPage = navigateToPage;
window.loadScenario = loadScenario;
window.deleteSpeaker = deleteSpeaker;
window.upvoteThreat = upvoteThreat;
window.openThreatDetail = openThreatDetail;
window.moderateThreat = moderateThreat;
window.resetVaultLockdown = resetVaultLockdown;
window.loadScenarioAndTransfer = loadScenarioAndTransfer;
window.sendApprovalToSimulator = sendApprovalToSimulator;
window.fetchNewChallenge = fetchNewChallenge;
window.openModal = openModal;
window.closeModal = closeModal;
window.inspectAuditJson = inspectAuditJson;
window.exportAuditCsv = exportAuditCsv;

// ============================================================================
// 2. SYSTEM CONFIG & OPERATING MODE
// ============================================================================
async function refreshSystemConfig() {
  try {
    const res = await fetch("/api/config");
    const data = await res.json();
    state.mode = data.mode;
    state.isLive = data.is_live_mode;
    state.hasApiKey = data.detectif_configured;

    updateModeUI(data);
  } catch (err) {
    console.error("Failed to load system config:", err);
  }
}

function updateModeUI(config) {
  const badge = document.getElementById("currentModeBadge");
  const text = document.getElementById("currentModeText");
  const btnToggle = document.getElementById("btnHeaderToggleMode");
  const overviewMode = document.getElementById("overviewModeText");
  const settingsBadge = document.getElementById("settingsCurrentModeBadge");
  const maskedKeyInput = document.getElementById("settingsMaskedKey");
  const verifyBadge = document.getElementById("verifyModeBadge");
  const enrollBadge = document.getElementById("enrollModeBadge");
  const apiStatusCircle = document.getElementById("apiStatusCircle");
  const apiStatusText = document.getElementById("apiStatusText");

  if (config.mode === "LIVE") {
    badge.className = "mode-badge live";
    text.textContent = "LIVE API";
    btnToggle.textContent = "Switch to DEMO";
    if (overviewMode) { overviewMode.className = "badge badge-live"; overviewMode.textContent = "LIVE API"; }
    if (settingsBadge) { settingsBadge.className = "badge badge-live"; settingsBadge.textContent = "LIVE API"; }
    if (verifyBadge) { verifyBadge.className = "badge badge-live"; verifyBadge.textContent = "LIVE API MODE"; }
    if (enrollBadge) { enrollBadge.className = "badge badge-live"; enrollBadge.textContent = "LIVE EIDOS REGISTRY"; }

    if (config.detectif_configured) {
      apiStatusCircle.className = "circle green";
      apiStatusText.textContent = "DetectifAI: Connected";
    } else {
      apiStatusCircle.className = "circle red";
      apiStatusText.textContent = "DetectifAI: Key Missing";
    }
  } else {
    badge.className = "mode-badge demo";
    text.textContent = "DEMO SIMULATION";
    btnToggle.textContent = "Switch to LIVE";
    if (overviewMode) { overviewMode.className = "badge badge-simulated"; overviewMode.textContent = "DEMO SIMULATION"; }
    if (settingsBadge) { settingsBadge.className = "badge badge-simulated"; settingsBadge.textContent = "DEMO SIMULATION"; }
    if (verifyBadge) { verifyBadge.className = "badge badge-simulated"; verifyBadge.textContent = "DEMO MODE ACTIVE"; }
    if (enrollBadge) { enrollBadge.className = "badge badge-simulated"; enrollBadge.textContent = "DEMO MODE"; }

    apiStatusCircle.className = "circle yellow";
    apiStatusText.textContent = "DetectifAI: Standby (Demo)";
  }

  const consolePill = document.getElementById("consoleModePill");
  if (consolePill) {
    if (config.mode === "LIVE") {
      consolePill.className = "badge badge-live";
      consolePill.textContent = "LIVE API";
    } else {
      consolePill.className = "badge badge-simulated";
      consolePill.textContent = "DEMO SIMULATION";
    }
  }

  const btnSetDemo = document.getElementById("btnSetDemoMode");
  const btnSetLive = document.getElementById("btnSetLiveMode");
  if (btnSetDemo && btnSetLive) {
    if (config.mode === "LIVE") {
      btnSetDemo.className = "btn btn-secondary";
      btnSetLive.className = "btn btn-primary";
    } else {
      btnSetDemo.className = "btn btn-primary";
      btnSetLive.className = "btn btn-secondary";
    }
  }

  if (maskedKeyInput) maskedKeyInput.value = config.detectif_masked_key || "Not Configured";
}

async function toggleOperatingMode(targetMode) {
  if (targetMode === "LIVE" && !state.hasApiKey) {
    alert("Cannot switch to LIVE API mode: DetectifAI API key is not configured.\n\nPlease configure DETECTIF_API_KEY in your .env file before switching to Live mode.");
    return;
  }

  try {
    const res = await fetch("/api/mode", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: targetMode })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Failed to switch operating mode.");
    }
    await refreshSystemConfig();
  } catch (err) {
    alert(`Mode switch error: ${err.message}`);
  }
}

// ============================================================================
// 3. AUDIO RECORDING & VISUALIZER (MediaRecorder)
// ============================================================================
function setupAudioRecorder() {
  const btnStart = document.getElementById("btnStartRecord");
  const btnStop = document.getElementById("btnStopRecord");
  const btnRetry = document.getElementById("btnRetryRecord");
  const btnExecute = document.getElementById("btnExecuteVerify");
  const fileInput = document.getElementById("audioFileInput");

  btnStart.addEventListener("click", startRecording);
  btnStop.addEventListener("click", stopRecording);
  btnRetry.addEventListener("click", resetRecording);
  btnExecute.addEventListener("click", runVerificationFromRecording);

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (file) {
        state.recordedBlob = file;
        state.recordedAudioUrl = URL.createObjectURL(file);
        const player = document.getElementById("audioPlayback");
        player.src = state.recordedAudioUrl;
        document.getElementById("audioPlaybackContainer").style.display = "block";
        document.getElementById("btnExecuteVerify").style.display = "inline-flex";
        document.getElementById("btnRetryRecord").style.display = "inline-flex";
        document.getElementById("btnStartRecord").style.display = "none";
        document.getElementById("recordingStatusText").textContent = `Loaded sample: ${file.name} (${Math.round(file.size / 1024)} KB)`;
      }
    });
  }

  // Draw initial canvas wave idle
  drawIdleVisualizer();
}

async function startRecording() {
  const statusText = document.getElementById("recordingStatusText");
  const btnStart = document.getElementById("btnStartRecord");
  const btnStop = document.getElementById("btnStopRecord");
  const btnRetry = document.getElementById("btnRetryRecord");
  const btnExecute = document.getElementById("btnExecuteVerify");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.audioChunks = [];
    state.recordedBlob = null;

    // Setup MediaRecorder
    let mimeType = "audio/webm";
    if (!MediaRecorder.isTypeSupported("audio/webm")) {
      if (MediaRecorder.isTypeSupported("audio/mp4")) mimeType = "audio/mp4";
      else mimeType = "";
    }

    state.mediaRecorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);

    state.mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        state.audioChunks.push(e.data);
      }
    };

    state.mediaRecorder.onstop = () => {
      stream.getTracks().forEach(track => track.stop());
      state.recordedBlob = new Blob(state.audioChunks, { type: state.mediaRecorder.mimeType || "audio/wav" });
      state.recordedAudioUrl = URL.createObjectURL(state.recordedBlob);

      const player = document.getElementById("audioPlayback");
      player.src = state.recordedAudioUrl;
      document.getElementById("audioPlaybackContainer").style.display = "block";

      btnStop.style.display = "none";
      btnRetry.style.display = "inline-flex";
      btnExecute.style.display = "inline-flex";
      statusText.textContent = `Recording complete (${state.recordingSeconds}s). Ready to analyze.`;

      stopVisualizer();
    };

    state.mediaRecorder.start();

    // Start Web Speech Recognition if available
    startSpeechRecognition();

    // Start timer & UI
    state.recordingSeconds = 0;
    updateTimerDisplay();
    state.recordingTimer = setInterval(() => {
      state.recordingSeconds++;
      updateTimerDisplay();
      if (state.recordingSeconds >= state.maxRecordingSeconds) {
        stopRecording();
      }
    }, 1000);

    btnStart.style.display = "none";
    btnStop.style.display = "inline-flex";
    btnRetry.style.display = "none";
    btnExecute.style.display = "none";
    document.getElementById("audioPlaybackContainer").style.display = "none";
    statusText.textContent = "Listening... Speak the challenge phrase clearly.";

    startVisualizer(stream);

  } catch (err) {
    console.error("Microphone access error:", err);
    let msg = "Microphone error: " + err.message;
    if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
      msg = "Microphone permission denied by browser. Please allow microphone access in browser settings or use file upload.";
    } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
      msg = "No microphone hardware detected. You can use the file upload fallback or test with Hackathon Presets.";
    }
    statusText.innerHTML = `<span style="color:var(--danger);">${msg}</span>`;
  }
}

function stopRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== "inactive") {
    state.mediaRecorder.stop();
  }
  if (state.recordingTimer) {
    clearInterval(state.recordingTimer);
    state.recordingTimer = null;
  }
  stopSpeechRecognition();
}

function resetRecording() {
  state.recordedBlob = null;
  state.recordingSeconds = 0;
  updateTimerDisplay();
  document.getElementById("audioPlaybackContainer").style.display = "none";
  document.getElementById("btnStartRecord").style.display = "inline-flex";
  document.getElementById("btnStopRecord").style.display = "none";
  document.getElementById("btnRetryRecord").style.display = "none";
  document.getElementById("btnExecuteVerify").style.display = "none";
  document.getElementById("recordingStatusText").textContent = "Microphone idle. Click Start Recording to authorize.";
  drawIdleVisualizer();
}

function updateTimerDisplay() {
  const mins = Math.floor(state.recordingSeconds / 60).toString().padStart(2, "0");
  const secs = (state.recordingSeconds % 60).toString().padStart(2, "0");
  document.getElementById("recordingTimer").textContent = `${mins}:${secs}`;
}

// Visualizer Waveform Logic
function startVisualizer(stream) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    state.audioContext = new AudioCtx();
    const source = state.audioContext.createMediaStreamSource(stream);
    state.analyser = state.audioContext.createAnalyser();
    state.analyser.fftSize = 128;
    source.connect(state.analyser);

    const canvas = document.getElementById("visualizerCanvas");
    const ctx = canvas.getContext("2d");
    const bufferLength = state.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
      state.animFrameId = requestAnimationFrame(draw);
      state.analyser.getByteFrequencyData(dataArray);

      ctx.fillStyle = "#0A0A0A";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.85;
        ctx.fillStyle = "#929292";
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 1, barHeight);
        x += barWidth;
      }
    }
    draw();
  } catch (e) {
    console.warn("Visualizer init skipped:", e);
  }
}

function stopVisualizer() {
  if (state.animFrameId) cancelAnimationFrame(state.animFrameId);
  if (state.audioContext && state.audioContext.state !== "closed") {
    state.audioContext.close();
  }
  drawIdleVisualizer();
}

function drawIdleVisualizer() {
  const canvas = document.getElementById("visualizerCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#0A0A0A";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "#242424";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(0, canvas.height / 2);
  ctx.lineTo(canvas.width, canvas.height / 2);
  ctx.stroke();
}

// ============================================================================
// 4. SPEECH RECOGNITION (Dynamic Liveness STT)
// ============================================================================
function setupSpeechRecognition() {
  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const sttStatus = document.getElementById("sttStatusIndicator");

  if (SpeechRec) {
    state.speechRecognition = new SpeechRec();
    state.speechRecognition.continuous = true;
    state.speechRecognition.interimResults = true;
    state.speechRecognition.lang = "en-US";

    state.speechRecognition.onresult = (event) => {
      let finalTranscript = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      if (finalTranscript) {
        document.getElementById("transcriptionInput").value = finalTranscript.trim();
        state.speechTranscript = finalTranscript.trim();
      }
    };

    state.speechRecognition.onerror = (e) => {
      console.warn("Speech recognition error:", e.error);
    };

    if (sttStatus) sttStatus.textContent = "STT: Web Speech API Armed";
  } else {
    if (sttStatus) sttStatus.textContent = "STT: Manual/Demo fallback";
  }
}

function startSpeechRecognition() {
  if (state.speechRecognition) {
    try {
      state.speechRecognition.start();
    } catch (e) {
      // already active
    }
  }
}

function stopSpeechRecognition() {
  if (state.speechRecognition) {
    try {
      state.speechRecognition.stop();
    } catch (e) {}
  }
}

// ============================================================================
// 5. CHALLENGES & SPEAKERS
// ============================================================================
async function fetchNewChallenge() {
  try {
    const res = await fetch("/api/challenges/generate");
    const data = await res.json();
    state.currentChallenge = data;

    const display = document.getElementById("challengeDisplayPhrase");
    const meta = document.getElementById("challengeMetaInfo");

    if (display) display.textContent = data.phrase;
    if (meta) meta.textContent = `Challenge Nonce: ${data.challenge_id} // UTC Nonce`;
  } catch (err) {
    console.error("Failed to fetch challenge:", err);
  }
}

async function refreshSpeakers() {
  try {
    const res = await fetch("/api/speakers");
    const speakers = await res.json();
    state.enrolledSpeakers = speakers;

    // Update Select Dropdowns
    const verifySelect = document.getElementById("verifySpeakerSelect");
    const wireSelect = document.getElementById("wireAuthorizerSelect");
    const dirList = document.getElementById("speakerDirectoryList");
    const statEnrolled = document.getElementById("statEnrolledSpeakers");

    if (statEnrolled) statEnrolled.textContent = `${speakers.length} Profiles`;

    if (verifySelect) {
      verifySelect.innerHTML = speakers.map(s => `
        <option value="${s.speaker_id}">${s.display_name} (${s.role_title || 'Signatory'}) [${s.provenance}]</option>
      `).join("");
    }

    if (wireSelect) {
      wireSelect.innerHTML = speakers.map(s => `
        <option value="${s.speaker_id}">${s.display_name} (${s.role_title || 'Signatory'})</option>
      `).join("");
    }

    // Render Directory Cards
    if (dirList) {
      if (speakers.length === 0) {
        dirList.innerHTML = `<p style="color:var(--text-dim); padding:20px;">No speakers enrolled yet.</p>`;
      } else {
        dirList.innerHTML = speakers.map(s => `
          <div class="speaker-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div style="display:flex; gap:10px; align-items:center;">
                <div class="speaker-avatar">${s.display_name.slice(0, 2).toUpperCase()}</div>
                <div>
                  <h4 style="color:var(--text-primary); font-size:0.84rem; font-weight:600;">${s.display_name}</h4>
                  <p style="color:var(--text-secondary); font-size:0.72rem;">${s.role_title || 'Executive'}</p>
                </div>
              </div>
              <span class="badge ${s.provenance === 'LIVE' ? 'badge-live' : 'badge-simulated'}">${s.provenance}</span>
            </div>
            <div style="margin-top:10px; font-size:0.7rem; color:var(--text-muted); display:flex; justify-content:space-between; align-items:center; border-top:1px solid var(--border-subtle); padding-top:8px;">
              <span>Enrolled: ${new Date(s.enrolled_at).toLocaleDateString()}</span>
              <button class="btn btn-secondary btn-sm" style="color:var(--danger); border-color:var(--danger-border);" onclick="deleteSpeaker('${s.speaker_id}')">Revoke</button>
            </div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Failed to load speakers:", err);
  }
}

async function deleteSpeaker(speakerId) {
  if (!confirm("Revoke this biometric voice profile?")) return;
  try {
    const res = await fetch(`/api/speakers/${speakerId}`, { method: "DELETE" });
    if (res.ok) {
      await refreshSpeakers();
    }
  } catch (err) {
    alert("Failed to delete speaker: " + err.message);
  }
}

// ============================================================================
// 6. PIPELINE VERIFICATION EXECUTION
// ============================================================================
async function runVerificationFromRecording() {
  if (!state.recordedBlob) {
    alert("No recorded audio sample found.");
    return;
  }

  const speakerId = document.getElementById("verifySpeakerSelect").value;
  const challengePhrase = state.currentChallenge ? state.currentChallenge.phrase : "";
  const transcription = document.getElementById("transcriptionInput").value;

  const formData = new FormData();
  formData.append("file", state.recordedBlob, "verification.wav");
  formData.append("speaker_id", speakerId);
  formData.append("challenge_phrase", challengePhrase);
  formData.append("transcribed_phrase", transcription);
  formData.append("challenge_verification_mode", transcription ? "automated" : "manual");

  const btnExecute = document.getElementById("btnExecuteVerify");
  btnExecute.disabled = true;
  btnExecute.textContent = "Analyzing Audio...";

  try {
    const res = await fetch("/api/verify", {
      method: "POST",
      body: formData
    });
    const result = await res.json();
    renderVerificationDecision(result);
  } catch (err) {
    alert("Verification pipeline failure: " + err.message);
  } finally {
    btnExecute.disabled = false;
    btnExecute.textContent = "Run Verification Pipeline";
  }
}

// Hackathon 1-Click Preset Scenario Loader
async function loadScenario(scenarioKey) {
  const speakerId = document.getElementById("verifySpeakerSelect").value || "spk_sarah_chen";
  const challengePhrase = state.currentChallenge ? state.currentChallenge.phrase : "Delta Falcon 4892 authorize transfer";

  const formData = new FormData();
  formData.append("demo_scenario_key", scenarioKey);
  formData.append("speaker_id", speakerId);
  formData.append("challenge_phrase", challengePhrase);

  // Set preset transcription based on scenario
  let simTranscription = challengePhrase;
  if (scenarioKey === "ai_clone") simTranscription = "Halted by deepfake engine";
  if (scenarioKey === "inconclusive") simTranscription = "noisy background";
  formData.append("transcribed_phrase", simTranscription);

  try {
    const res = await fetch("/api/verify", {
      method: "POST",
      body: formData
    });
    const result = await res.json();
    renderVerificationDecision(result);
  } catch (err) {
    alert("Scenario execution error: " + err.message);
  }
}

function renderVerificationDecision(result) {
  state.lastVerificationResult = result;

  document.getElementById("decisionPlaceholder").style.display = "none";
  const card = document.getElementById("decisionCard");
  card.style.display = "block";

  // Banner status
  const bannerBadge = document.getElementById("decisionProvenanceBadge");
  bannerBadge.className = result.provenance === "LIVE" ? "badge badge-live" : "badge badge-simulated";
  bannerBadge.textContent = result.provenance;

  const outcomeText = document.getElementById("decisionOutcomeText");
  const icon = document.getElementById("decisionIcon");
  const reasonText = document.getElementById("decisionReasonText");
  const actionArea = document.getElementById("decisionActionArea");

  card.className = "decision-card";

  if (result.decision === "APPROVED") {
    card.classList.add("approved");
    outcomeText.textContent = "VERIFIED // AUTHORIZED";
    outcomeText.style.color = "var(--success)";
    icon.textContent = "";
    actionArea.innerHTML = `
      <button class="btn btn-primary btn-sm" onclick="sendApprovalToSimulator()">
        Proceed to Simulator
      </button>
    `;
  } else if (result.decision === "BLOCKED") {
    card.classList.add("blocked");
    outcomeText.textContent = "SECURITY INTERCEPTION // BLOCKED";
    outcomeText.style.color = "var(--danger)";
    icon.textContent = "";
    actionArea.innerHTML = `
      <button class="btn btn-danger btn-sm" onclick="openThreatReportModalFromBlocked('${result.incident_id}', '${result.attack_type}', '${result.reason.replace(/'/g, "\\'")}')">
        File to r/VoiceThreatNet
      </button>
    `;
  } else {
    card.classList.add("step_up");
    outcomeText.textContent = "STEP-UP AUTHENTICATION REQUIRED";
    outcomeText.style.color = "var(--warning)";
    icon.textContent = "";
    actionArea.innerHTML = `
      <button class="btn btn-secondary btn-sm" onclick="fetchNewChallenge()">
        Retry with New Nonce
      </button>
    `;
  }

  reasonText.textContent = result.reason;

  // Stages Breakdown
  const aletheiaVerdict = document.getElementById("stageAletheiaVerdict");
  const aletheiaScore = document.getElementById("stageAletheiaScore");
  const aletheiaDetail = document.getElementById("stageAletheiaDetail");

  aletheiaVerdict.textContent = result.aletheia.verdict.toUpperCase();
  aletheiaVerdict.style.color = result.aletheia.verdict === "real" ? "var(--success)" : (result.aletheia.verdict === "fake" ? "var(--danger)" : "var(--warning)");
  aletheiaScore.textContent = `Score: ${result.aletheia.score}`;
  aletheiaDetail.textContent = result.stages.deepfake_detection ? result.stages.deepfake_detection.detail : "--";

  const eidosVerdict = document.getElementById("stageEidosVerdict");
  const eidosScore = document.getElementById("stageEidosScore");
  const eidosDetail = document.getElementById("stageEidosDetail");

  eidosVerdict.textContent = result.eidos.verdict.toUpperCase();
  eidosVerdict.style.color = result.eidos.verdict === "match" ? "var(--success)" : "var(--text-muted)";
  eidosScore.textContent = result.eidos.score ? `Match: ${result.eidos.score}` : "N/A";
  eidosDetail.textContent = result.stages.speaker_verification ? result.stages.speaker_verification.detail : "--";

  const chalVerdict = document.getElementById("stageChallengeVerdict");
  const chalOutcome = document.getElementById("stageChallengeOutcome");
  const chalDetail = document.getElementById("stageChallengeDetail");

  chalVerdict.textContent = result.challenge.outcome;
  chalVerdict.style.color = result.challenge.outcome === "PASSED" ? "var(--success)" : "var(--text-muted)";
  chalOutcome.textContent = result.challenge.details.confidence ? `Conf: ${result.challenge.details.confidence}` : "--";
  chalDetail.textContent = result.stages.liveness_challenge ? result.stages.liveness_challenge.detail : "--";

  // Telemetry footer
  document.getElementById("telemetryAletheiaReqId").textContent = result.aletheia.request_id || "None";
  document.getElementById("telemetryEidosReqId").textContent = result.eidos.request_id || "None";
  document.getElementById("telemetryTargetSpeaker").textContent = result.speaker.display_name || "Unassigned";
  document.getElementById("verifIncidentIdBadge").textContent = result.incident_id;

  // Refresh Audit & Overview
  refreshAuditLogs();
}

function sendApprovalToSimulator() {
  navigateToPage("page-simulator");
  const authStatus = document.getElementById("simVoiceAuthText");
  const authDetail = document.getElementById("simVoiceAuthDetail");
  authStatus.textContent = "Voice Verified & Authorized";
  authStatus.style.color = "var(--success)";
  authDetail.textContent = `Incident ID: ${state.lastVerificationResult.incident_id} | Mode: ${state.lastVerificationResult.mode}`;
}

// ============================================================================
// 7. TRANSACTION SIMULATOR & PHANTOM MODE
// ============================================================================
async function refreshSimulatorVault() {
  try {
    const res = await fetch("/api/simulator/status");
    const data = await res.json();
    const vault = data.vault_state;

    const statusBadge = document.getElementById("socVaultStatusBadge");
    const reservesText = document.getElementById("socVaultReserves");
    const blockedText = document.getElementById("socFundsBlocked");
    const alertBox = document.getElementById("socAlertBox");
    const statFunds = document.getElementById("statFundsProtected");

    if (reservesText) reservesText.textContent = `$${vault.total_simulated_reserves.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    if (blockedText) blockedText.textContent = `$${vault.funds_blocked_from_fraud.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    if (statFunds) statFunds.textContent = `$${vault.funds_blocked_from_fraud.toLocaleString('en-US')}`;

    if (statusBadge) {
      if (vault.vault_status === "EMERGENCY_LOCKDOWN") {
        statusBadge.className = "badge badge-blocked";
        statusBadge.textContent = "EMERGENCY_LOCKDOWN";
      } else {
        statusBadge.className = "badge badge-approved";
        statusBadge.textContent = "SECURE_ONLINE";
      }
    }

    if (alertBox && vault.last_alert) {
      alertBox.innerHTML = `
        <div style="color:var(--danger); font-weight:600; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.04em;">Phantom Mode Protocol Triggered</div>
        <div style="margin-top:2px;">Blocked Transfer: $${vault.last_alert.blocked_amount.toLocaleString()} to ${vault.last_alert.beneficiary}</div>
        <div style="font-size:0.7rem; color:var(--text-muted); margin-top:2px;">Reason: ${vault.last_alert.reason} (Incident: ${vault.last_alert.incident_id})</div>
      `;
    }
  } catch (err) {
    console.error("Failed to load vault status:", err);
  }
}

async function handleWireTransferSubmit(e) {
  e.preventDefault();

  const beneficiaryName = document.getElementById("wireBeneficiaryName").value;
  const beneficiaryAccount = document.getElementById("wireAccount").value;
  const beneficiaryBank = document.getElementById("wireBank").value;
  const amount = parseFloat(document.getElementById("wireAmount").value) || 250000;
  const speakerId = document.getElementById("wireAuthorizerSelect").value;

  // Determine verification decision from last verification result or prompt
  let decision = "APPROVED";
  let incidentId = null;
  let reason = "Voice verified authentic.";
  let attackType = null;

  if (state.lastVerificationResult) {
    decision = state.lastVerificationResult.decision;
    incidentId = state.lastVerificationResult.incident_id;
    reason = state.lastVerificationResult.reason;
    attackType = state.lastVerificationResult.attack_type;
  }

  const payload = {
    beneficiary_name: beneficiaryName,
    beneficiary_account: beneficiaryAccount,
    beneficiary_bank: beneficiaryBank,
    amount: amount,
    currency: "USD",
    speaker_id: speakerId,
    verification_decision: decision,
    incident_id: incidentId,
    reason: reason,
    attack_type: attackType
  };

  try {
    const res = await fetch("/api/simulator/transfer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const tx = await res.json();
    renderTransferResult(tx);
    await refreshSimulatorVault();
  } catch (err) {
    alert("Transaction execution failure: " + err.message);
  }
}

function renderTransferResult(tx) {
  const card = document.getElementById("attackerReceiptCard");
  const placeholder = document.getElementById("attackerPlaceholder");
  const noticeBadge = document.getElementById("attackerNoticeBadge");

  placeholder.style.display = "none";
  card.style.display = "block";

  if (tx.phantom_triggered) {
    // PHANTOM MODE: Render convincing decoy receipt for attacker!
    card.className = "receipt-card phantom-decoy";
    noticeBadge.className = "badge badge-blocked";
    noticeBadge.textContent = "DECOY PHANTOM DELIVERED";

    document.getElementById("decoyStatusText").textContent = "SETTLED / RELEASED";
    document.getElementById("decoyStatusText").style.color = "var(--success)";
    document.getElementById("decoyReceiptDate").textContent = new Date().toLocaleTimeString();
    document.getElementById("decoyWireRef").textContent = tx.decoy_receipt.wire_confirmation;
    document.getElementById("decoyBeneficiary").textContent = tx.decoy_receipt.beneficiary;
    document.getElementById("decoyAmount").textContent = tx.decoy_receipt.amount_credited;
  } else {
    // Normal approved transfer
    card.className = "receipt-card";
    noticeBadge.className = "badge badge-approved";
    noticeBadge.textContent = "GENUINE SETTLEMENT";

    document.getElementById("decoyStatusText").textContent = "APPROVED & DISPATCHED";
    document.getElementById("decoyStatusText").style.color = "var(--success)";
    document.getElementById("decoyReceiptDate").textContent = new Date().toLocaleTimeString();
    document.getElementById("decoyWireRef").textContent = `FW-${tx.transaction_id}`;
    document.getElementById("decoyBeneficiary").textContent = document.getElementById("wireBeneficiaryName").value;
    document.getElementById("decoyAmount").textContent = `$${tx.amount.toLocaleString()} ${tx.currency}`;
  }
}

async function loadScenarioAndTransfer(scenarioKey) {
  await loadScenario(scenarioKey);
  navigateToPage("page-simulator");
  const authStatus = document.getElementById("simVoiceAuthText");
  const authDetail = document.getElementById("simVoiceAuthDetail");
  authStatus.textContent = "Voice Fraud Intercepted (Fake Audio)";
  authStatus.style.color = "var(--danger)";
  authDetail.textContent = `Triggering Phantom Mode Decoy Protocol...`;

  // Trigger transfer immediately to demo Phantom Mode
  document.getElementById("btnExecuteTransfer").click();
}

async function resetVaultLockdown() {
  try {
    const res = await fetch("/api/simulator/unlock-vault", { method: "POST" });
    if (res.ok) {
      await refreshSimulatorVault();
      alert("Simulated vault reset to SECURE_ONLINE.");
    }
  } catch (err) {
    alert("Reset failed: " + err.message);
  }
}

// ============================================================================
// 8. THREAT INTELLIGENCE FEED (r/VoiceThreatNet)
// ============================================================================
async function refreshThreatFeed() {
  const attackType = document.getElementById("threatFilterType")?.value || "all";
  const severity = document.getElementById("threatFilterSeverity")?.value || "all";
  const status = document.getElementById("threatFilterStatus")?.value || "all";
  const q = document.getElementById("threatSearchInput")?.value || "";

  const params = new URLSearchParams();
  if (attackType !== "all") params.append("attack_type", attackType);
  if (severity !== "all") params.append("severity", severity);
  if (status !== "all") params.append("status", status);
  if (q.trim()) params.append("q", q.trim());

  try {
    const res = await fetch(`/api/threats?${params.toString()}`);
    const threats = await res.json();

    const feedList = document.getElementById("threatFeedList");
    const overviewSnippets = document.getElementById("overviewThreatSnippets");
    const landingThreatPreview = document.getElementById("landingThreatFeedPreview");

    if (feedList) {
      if (threats.length === 0) {
        feedList.innerHTML = `<p style="padding:40px; text-align:center; color:var(--text-dim);">No threat reports matching your filter criteria.</p>`;
      } else {
        feedList.innerHTML = threats.map(t => renderThreatCard(t)).join("");
      }
    }

    if (landingThreatPreview) {
      if (threats.length === 0) {
        landingThreatPreview.innerHTML = `<p style="padding:24px; text-align:center; color:var(--text-dim);">No threat dispatches recorded yet.</p>`;
      } else {
        landingThreatPreview.innerHTML = threats.slice(0, 3).map(t => `
          <div style="border-bottom:1px solid var(--border-subtle); padding:16px 0; display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
            <div style="flex:1;">
              <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                <span class="badge ${t.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}">${t.severity}</span>
                <span class="badge ${t.provenance === 'LIVE' ? 'badge-live' : 'badge-simulated'}">${t.provenance}</span>
                <span style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">${t.id} &bull; ${new Date(t.created_at).toLocaleDateString()}</span>
              </div>
              <h4 style="font-size:0.95rem; font-weight:600; color:var(--text-primary); margin-bottom:4px; cursor:pointer;" onclick="openSecurityConsole('page-threats')">${t.title}</h4>
              <p style="font-size:0.8rem; color:var(--text-secondary); line-height:1.45; margin:0;">${t.summary.slice(0, 160)}...</p>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="openSecurityConsole('page-threats')" style="white-space:nowrap; margin-top:4px;">
              View Intel &rarr;
            </button>
          </div>
        `).join("");
      }
    }

    if (overviewSnippets) {
      overviewSnippets.innerHTML = threats.slice(0, 3).map(t => `
        <div style="border-bottom:1px solid var(--border-subtle); padding:10px 0;">
          <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
            <strong style="font-size:0.82rem; color:var(--text-primary); cursor:pointer;" onclick="openThreatDetail('${t.id}')">${t.title}</strong>
            <span class="badge ${t.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}">${t.severity}</span>
          </div>
          <div style="font-size:0.75rem; color:var(--text-secondary); line-height:1.4;">${t.summary.slice(0, 110)}...</div>
          <div style="font-size:0.68rem; color:var(--text-muted); margin-top:4px;">${t.id} &bull; ${new Date(t.created_at).toLocaleDateString()}</div>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Failed to load threats:", err);
  }
}

function renderThreatCard(t) {
  const typeMap = {
    "ai_clone": "AI Voice Clone",
    "replay": "Replay Attack",
    "human_impostor": "Human Impostor",
    "unknown": "Unknown"
  };

  const sevBadge = t.severity === "CRITICAL" ? "badge-critical" : (t.severity === "HIGH" ? "badge-high" : "badge-medium");
  const provBadge = t.provenance === "LIVE" ? "badge-live" : "badge-simulated";

  return `
    <div class="threat-card" id="card-${t.id}">
      <div class="threat-vote-col">
        <button class="vote-btn" onclick="upvoteThreat('${t.id}')" title="Upvote dispatch">
          <svg viewBox="0 0 24 24" style="width:12px; height:12px; stroke:currentColor; fill:none; stroke-width:2;"><polyline points="18 15 12 9 6 15"/></svg>
        </button>
        <span class="vote-count tabular" id="votes-${t.id}">${t.upvotes}</span>
      </div>
      <div class="threat-body-col">
        <div class="threat-meta">
          <span class="badge ${provBadge}">${t.provenance}</span>
          <span class="badge ${sevBadge}">${t.severity}</span>
          <span class="badge badge-low">${typeMap[t.attack_type] || t.attack_type}</span>
          <span>${t.author} &bull; ${new Date(t.created_at).toLocaleDateString()}</span>
          <span class="badge badge-low">${t.status}</span>
        </div>

        <h3 class="threat-title" onclick="openThreatDetail('${t.id}')">${t.title}</h3>
        <p class="threat-summary">${t.summary}</p>

        <div class="threat-actions">
          <button class="threat-action-link" onclick="openThreatDetail('${t.id}')">${t.comments_count} comments</button>
          <button class="threat-action-link" onclick="moderateThreat('${t.id}', 'verify')">Verify Incident</button>
          <button class="threat-action-link" onclick="moderateThreat('${t.id}', 'dismiss')">Dismiss</button>
          <span style="margin-left:auto; font-size:0.7rem; color:var(--text-muted);" class="mono">${t.id}</span>
        </div>
      </div>
    </div>
  `;
}

async function upvoteThreat(threatId) {
  try {
    const res = await fetch(`/api/threats/${threatId}/upvote`, { method: "POST" });
    const data = await res.json();
    const countEl = document.getElementById(`votes-${threatId}`);
    if (countEl) countEl.textContent = data.upvotes;
  } catch (err) {
    console.error("Upvote failed:", err);
  }
}

async function moderateThreat(threatId, action) {
  try {
    const res = await fetch(`/api/threats/${threatId}/action`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: action, notes: `Action taken by SOC Analyst at ${new Date().toISOString()}` })
    });
    if (res.ok) {
      await refreshThreatFeed();
    }
  } catch (err) {
    alert("Moderation action failed: " + err.message);
  }
}

async function openThreatDetail(threatId) {
  try {
    const res = await fetch(`/api/threats/${threatId}`);
    const t = await res.json();

    document.getElementById("detailModalTitle").textContent = `${t.title} (${t.id})`;
    document.getElementById("detailModalBody").innerHTML = `
      <div style="margin-bottom:14px;">
        <span class="badge ${t.provenance === 'LIVE' ? 'badge-live' : 'badge-simulated'}">${t.provenance}</span>
        <span class="badge ${t.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}">${t.severity}</span>
        <span class="badge badge-low">${t.status}</span>
      </div>
      <p style="font-size:0.84rem; color:var(--text-primary); line-height:1.5; margin-bottom:14px;">${t.summary}</p>
      <div style="background:var(--bg-subtle); border:1px solid var(--border-subtle); padding:12px; border-radius:var(--radius-xs); font-size:0.72rem; color:var(--text-secondary);">
        <div><strong style="color:var(--text-primary);">Incident Reference:</strong> ${t.incident_id || 'Direct Community Submission'}</div>
        <div><strong style="color:var(--text-primary);">Author:</strong> ${t.author}</div>
        <div><strong style="color:var(--text-primary);">Timestamp:</strong> ${t.created_at}</div>
        <div><strong style="color:var(--text-primary);">Resolution Notes:</strong> ${t.resolution_notes || 'Pending moderator analysis.'}</div>
      </div>
      <div style="display:flex; justify-content:space-between; margin-top:16px;">
        <div style="display:flex; gap:8px;">
          <button class="btn btn-secondary btn-sm" onclick="moderateThreat('${t.id}', 'verify'); closeModal('modalThreatDetail');">Verify Incident</button>
          <button class="btn btn-secondary btn-sm" onclick="moderateThreat('${t.id}', 'dismiss'); closeModal('modalThreatDetail');">Dismiss</button>
        </div>
        <button class="btn btn-primary btn-sm" onclick="closeModal('modalThreatDetail')">Close</button>
      </div>
    `;

    openModal("modalThreatDetail");
  } catch (err) {
    alert("Failed to load details: " + err.message);
  }
}

function openThreatReportModalFromBlocked(incidentId, attackType, reason) {
  document.getElementById("reportIncidentId").value = incidentId || "";
  document.getElementById("reportTitle").value = `Blocked ${attackType === 'ai_clone' ? 'AI Voice Clone' : 'Voice Fraud Attempt'} on Corporate Signatory`;
  document.getElementById("reportSummary").value = `Aletheia multi-factor voice firewall intercepted unauthorized voice authorization. Telemetry details: ${reason}. Incident ID: ${incidentId}. No funds dispatched; Phantom Mode triggered.`;
  document.getElementById("reportAttackType").value = attackType || "ai_clone";
  openModal("modalThreatReport");
}

// ============================================================================
// 9. AUDIT HISTORY & CSV EXPORT
// ============================================================================
async function refreshAuditLogs() {
  const decision = document.getElementById("auditFilterDecision")?.value || "all";
  const mode = document.getElementById("auditFilterMode")?.value || "all";

  const params = new URLSearchParams();
  if (decision !== "all") params.append("decision", decision);
  if (mode !== "all") params.append("mode", mode);

  try {
    const res = await fetch(`/api/audit?${params.toString()}`);
    const logs = await res.json();

    const tbody = document.getElementById("auditTableBody");
    if (!tbody) return;

    if (logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" style="text-align:center; padding:30px; color:var(--text-dim);">No audit records found.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => {
      const decBadge = l.final_decision === "APPROVED" ? "badge-approved" : (l.final_decision === "BLOCKED" ? "badge-blocked" : "badge-step-up");
      const modeBadge = l.mode === "LIVE" ? "badge-live" : "badge-simulated";

      return `
        <tr>
          <td class="mono" style="font-weight:600; color:var(--text-primary);">${l.incident_id}</td>
          <td style="font-size:0.75rem; color:var(--text-muted);">${new Date(l.timestamp).toLocaleTimeString()}</td>
          <td><span class="badge ${modeBadge}">${l.mode}</span></td>
          <td>${l.speaker_name || 'N/A'}</td>
          <td>
            <span style="font-weight:700; color:${l.aletheia_verdict === 'real' ? 'var(--success)' : (l.aletheia_verdict === 'fake' ? 'var(--danger)' : 'var(--warning)')}">
              ${l.aletheia_verdict ? l.aletheia_verdict.toUpperCase() : '--'}
            </span>
            <span class="mono" style="font-size:0.72rem; color:var(--text-dim);">(${l.aletheia_score || 0})</span>
          </td>
          <td>
            <span style="font-weight:600;">${l.eidos_verdict ? l.eidos_verdict.toUpperCase() : '--'}</span>
          </td>
          <td>
            <span style="font-size:0.78rem;">${l.challenge_outcome || '--'}</span>
          </td>
          <td><span class="badge ${decBadge}">${l.final_decision}</span></td>
          <td>
            ${l.threat_report_id ? `<span class="badge badge-critical mono" style="cursor:pointer;" onclick="openThreatDetail('${l.threat_report_id}')">${l.threat_report_id}</span>` : '<span style="color:var(--text-dim);">--</span>'}
          </td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick='inspectAuditJson(${JSON.stringify(l).replace(/'/g, "&apos;")})'>Inspect</button>
          </td>
        </tr>
      `;
    }).join("");
  } catch (err) {
    console.error("Failed to load audit logs:", err);
  }
}

function inspectAuditJson(record) {
  document.getElementById("auditJsonContent").textContent = JSON.stringify(record, null, 2);
  openModal("modalAuditJson");
}

// ============================================================================
// 10. MODALS & EVENT HANDLERS
// ============================================================================
function setupModals() {
  // ESC key closes active dialog
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll("dialog[open]").forEach(d => d.close());
    }
  });

  // Light dismiss: clicking on backdrop
  document.querySelectorAll("dialog").forEach(dialog => {
    dialog.addEventListener("click", (e) => {
      const rect = dialog.getBoundingClientRect();
      const isInDialog = (
        rect.top <= e.clientY && e.clientY <= rect.top + rect.height &&
        rect.left <= e.clientX && e.clientX <= rect.left + rect.width
      );
      if (!isInDialog) dialog.close();
    });
  });
}

function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.showModal();
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.close();
}

function setupEventListeners() {
  // Mode toggles
  document.getElementById("btnHeaderToggleMode").addEventListener("click", () => {
    toggleOperatingMode(state.mode === "DEMO" ? "LIVE" : "DEMO");
  });
  document.getElementById("btnSetDemoMode").addEventListener("click", () => toggleOperatingMode("DEMO"));
  document.getElementById("btnSetLiveMode").addEventListener("click", () => toggleOperatingMode("LIVE"));

  // API Ping Test
  document.getElementById("btnTestApiConnection").addEventListener("click", async () => {
    const box = document.getElementById("connectionTestResultBox");
    box.innerHTML = `<span style="color:var(--cyan-primary);">Testing connection to DetectifAI platform...</span>`;
    try {
      const res = await fetch("/api/test-connection", { method: "POST" });
      const data = await res.json();
      box.innerHTML = `
        <div style="font-weight:700; color:${data.connected && data.authenticated ? 'var(--success)' : (data.connected ? 'var(--warning)' : 'var(--danger)')}">
          ${data.message}
        </div>
        <div style="font-size:0.75rem; color:var(--text-dim); margin-top:4px;">
          Reachability: ${data.connected ? 'OK' : 'Unreachable'} | Auth: ${data.authenticated ? 'Valid' : 'Unauthenticated'}
        </div>
      `;
    } catch (err) {
      box.innerHTML = `<span style="color:var(--danger);">Error: ${err.message}</span>`;
    }
  });

  // Refresh Challenge Button
  document.getElementById("btnRefreshChallenge").addEventListener("click", fetchNewChallenge);

  // Speaker Enrollment Form Submit
  document.getElementById("enrollmentForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const name = document.getElementById("enrollName").value;
    const role = document.getElementById("enrollRole").value;
    const notes = document.getElementById("enrollNotes").value;
    const consent = document.getElementById("enrollConsent").checked;
    const file = document.getElementById("enrollFileInput").files[0];

    if (!consent) {
      alert("Biometric consent is mandatory before enrolling a voice profile.");
      return;
    }

    const formData = new FormData();
    formData.append("display_name", name);
    formData.append("role_title", role);
    formData.append("notes", notes);
    formData.append("consent_confirmed", consent);

    if (file) {
      formData.append("file", file);
    } else {
      // Create empty mock audio if in demo mode and no sample provided
      const emptyBlob = new Blob([new Uint8Array(2000)], { type: "audio/wav" });
      formData.append("file", emptyBlob, "sample.wav");
    }

    try {
      const res = await fetch("/api/speakers/enroll", {
        method: "POST",
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Enrollment failed");
      }
      const data = await res.json();
      alert(data.message);
      document.getElementById("enrollmentForm").reset();
      await refreshSpeakers();
    } catch (err) {
      alert("Enrollment error: " + err.message);
    }
  });

  // Wire Transfer Form Submit
  document.getElementById("wireTransferForm").addEventListener("submit", handleWireTransferSubmit);
  document.getElementById("btnResetVault").addEventListener("click", resetVaultLockdown);

  // Submit Threat Report Form
  document.getElementById("btnOpenNewThreatModal").addEventListener("click", () => {
    document.getElementById("formSubmitThreatReport").reset();
    document.getElementById("reportIncidentId").value = "";
    openModal("modalThreatReport");
  });

  document.getElementById("formSubmitThreatReport").addEventListener("submit", async (e) => {
    e.preventDefault();
    const incidentId = document.getElementById("reportIncidentId").value || null;
    const title = document.getElementById("reportTitle").value;
    const summary = document.getElementById("reportSummary").value;
    const attackType = document.getElementById("reportAttackType").value;
    const severity = document.getElementById("reportSeverity").value;

    const payload = {
      incident_id: incidentId,
      title: title,
      summary: summary,
      attack_type: attackType,
      severity: severity,
      provenance: state.mode === "LIVE" ? "LIVE" : "SIMULATED",
      author: "u/SOC_Analyst"
    };

    try {
      const res = await fetch("/api/threats", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        closeModal("modalThreatReport");
        await refreshThreatFeed();
        alert("Report submitted successfully to r/VoiceThreatNet (Status: Pending Review).");
      }
    } catch (err) {
      alert("Failed to submit report: " + err.message);
    }
  });

  // Search & Filter listeners
  document.getElementById("threatSearchInput").addEventListener("input", debounce(refreshThreatFeed, 300));
  document.getElementById("threatFilterType").addEventListener("change", refreshThreatFeed);
  document.getElementById("threatFilterSeverity").addEventListener("change", refreshThreatFeed);
  document.getElementById("threatFilterStatus").addEventListener("change", refreshThreatFeed);
  document.getElementById("btnRefreshThreats").addEventListener("click", refreshThreatFeed);

  document.getElementById("auditFilterDecision").addEventListener("change", refreshAuditLogs);
  document.getElementById("auditFilterMode").addEventListener("change", refreshAuditLogs);
  document.getElementById("btnRefreshAudit").addEventListener("click", refreshAuditLogs);
  document.getElementById("btnRefreshSpeakers").addEventListener("click", refreshSpeakers);
}

// Utility: debounce
function debounce(fn, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
