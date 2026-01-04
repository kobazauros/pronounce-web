// -------------------------------------------------------------
// script.js – Pronunciation Checker (Thesis Edition)
// -------------------------------------------------------------

// ======= Configuration =======
let WORDS = [];
const AUDIO_EXT = 'mp3';
const TARGET_RATE = 16000;
const ensureAC = () => (ac ||= new AudioContext({ sampleRate: TARGET_RATE }));

// Manifest loader
async function loadManifest() {
  try {
    const res = await fetch('audio/index.json', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const arr = Array.isArray(data) ? data : Array.isArray(data.words) ? data.words : [];
    if (!Array.isArray(arr) || arr.length === 0) throw new Error('Empty manifest');
    WORDS = arr.map(item => {
      const w = (item && typeof item === 'object' && item.word) ? item.word : item;
      return String(w).replace(/\.[^/.]+$/, '');
    }).slice(0, 20);
  } catch (e) {
    console.warn('Manifest load failed.', e);
    if (studentMsg) studentMsg.textContent = '⚠️ Error: Could not load audio/index.json.';
    WORDS = [];
  }
}

// ------- DOM -------
const nameInput = document.getElementById('student-name');
const idInput = document.getElementById('student-id');
const studentMsg = document.getElementById('student-msg');
const wordList = document.getElementById('word-list');
const sampleTitle = document.getElementById('sample-word-placeholder');
const playBtn = document.getElementById('play-sample');
const recStartBtn = document.getElementById('record-start');
const recStopBtn = document.getElementById('record-stop');
const playUserBtn = document.getElementById('play-user');
const submitBtn = document.getElementById('submit-recording');
const sampleWF = document.getElementById('sample-waveform-container');
const userWF = document.getElementById('user-waveform-container');
const overlapWF = document.getElementById('difference-waveform-container');
const msgBox = document.getElementById('message-box');
const sampleMsg = document.getElementById('sample-message');
const submitMsg = document.getElementById('submit-msg');

// Noise UI
const noiseStatusContainer = document.getElementById('noise-status-container');
const noiseText = document.getElementById('noise-indicator-text');
const noiseLevelDisplay = document.getElementById('noise-level-display');

// ------- Audio globals -------
let ac;
let sampleBuf, userBuf;
let sampleWS, userWS;
let mediaRecorder, chunks = [];
let lastRecordingBlob = null;
let selectedWord = null;

// Thresholds & Variables
const defaultThreshold = 0.01;
let noiseThreshold = defaultThreshold;
const SILENCE_HOLD_MS = 1500;
const START_GRACE_MS = 2000;
const ANALYSE_INTERVAL = 100;

// === STATE MACHINE VARIABLES ===
let isAppBusy = false;     // TRUE if Recording or Playing
let sessionActive = false; // TRUE if User has started typing name
let isMonitoring = false;  // TRUE if currently listening to room noise

// ======= Helpers =======
const say = txt => (msgBox.textContent = txt ?? '');
const sampleSay = txt => (sampleMsg.textContent = txt ?? '');
const submitSay = txt => (submitMsg.textContent = txt ?? '');

function guardStudentInfo() {
  const name = nameInput.value.trim();
  const sid = idInput.value.trim();
  if (!name || !sid) {
    studentMsg.textContent = 'Enter Student Name and ID to continue.';
    return false;
  }
  studentMsg.textContent = '';
  return true;
}

function getProgressKey(sid) { return `thesis_progress_${sid}`; }
function loadProgress(sid) {
  try { return JSON.parse(localStorage.getItem(getProgressKey(sid)) || '{}'); } catch { return {}; }
}
function saveProgress(sid, data) {
  localStorage.setItem(getProgressKey(sid), JSON.stringify(data));
}

function buildWordList() {
  wordList.innerHTML = '';
  const words = [...WORDS].sort((a, b) => a.localeCompare(b));
  for (const w of words) {
    const a = document.createElement('a');
    a.href = '#';
    a.textContent = w;
    a.className = 'word-link word-pending';
    a.dataset.word = w;
    a.addEventListener('click', (e) => {
      e.preventDefault();
      if (!guardStudentInfo()) return;
      selectedWord = w;
      sampleTitle.textContent = w;
      sampleSay('Click "Play Sample" to hear the model.');
    });
    wordList.appendChild(a);
  }
}

function refreshSubmittedColors() {
  const sid = idInput.value.trim();
  const prog = sid ? loadProgress(sid) : {};
  for (const el of wordList.querySelectorAll('.word-link')) {
    const w = el.dataset.word;
    el.classList.toggle('word-submitted', !!prog[w]);
    el.classList.toggle('word-pending', !prog[w]);
  }
}

function normalizeBuffer(buffer) {
  const data = buffer.getChannelData(0);
  let maxPeak = 0;
  for (let i = 0; i < data.length; i++) {
    const abs = Math.abs(data[i]);
    if (abs > maxPeak) maxPeak = abs;
  }
  if (maxPeak === 0) return buffer;
  const target = 0.89125;
  const gain = target / maxPeak;
  const newBuf = ac.createBuffer(1, buffer.length, buffer.sampleRate);
  const newData = newBuf.getChannelData(0);
  for (let i = 0; i < data.length; i++) {
    newData[i] = data[i] * gain;
  }
  return newBuf;
}

// ============================================
//  CORE STATE MACHINE LOGIC
// ============================================
let monitorStream = null;
let monitorCtx = null;
let currentNoisePeak = 0;

// 1. RESUME: Try to start monitoring (Subject to Rules)
async function resumeMonitoring() {
  // RULE 1: If App is Busy (Recording/Playing), stay OFF.
  if (isAppBusy) return;
  // RULE 2: If Privacy Mode (Tab hidden), stay OFF.
  if (document.hidden) return;
  // RULE 3: If Session hasn't started (No name), stay OFF.
  if (!sessionActive) return;
  // RULE 4: If already running, do nothing.
  if (isMonitoring) return;

  try {
    if (noiseStatusContainer) noiseStatusContainer.style.display = 'block';
    if (noiseText) {
      noiseText.textContent = "Monitoring noise...";
      noiseText.style.color = "#666";
    }

    monitorStream = await navigator.mediaDevices.getUserMedia({ audio: true });

    monitorCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = monitorCtx.createMediaStreamSource(monitorStream);
    const analyser = monitorCtx.createAnalyser();

    analyser.fftSize = 2048;
    source.connect(analyser);

    const buffer = new Float32Array(analyser.fftSize);
    isMonitoring = true;

    // Start Analysis Loop
    function loop() {
      if (!isMonitoring) return;
      requestAnimationFrame(loop);

      analyser.getFloatTimeDomainData(buffer);
      let framePeak = 0;
      for (let i = 0; i < buffer.length; i++) {
        const abs = Math.abs(buffer[i]);
        if (abs > framePeak) framePeak = abs;
      }
      currentNoisePeak = (currentNoisePeak * 0.9) + (framePeak * 0.1);

      if (noiseLevelDisplay) {
        const percent = (currentNoisePeak * 1000).toFixed(0);
        noiseLevelDisplay.textContent = `Level: ${percent}`;

        if (currentNoisePeak < 0.02) noiseLevelDisplay.style.color = "green";
        else if (currentNoisePeak < 0.05) noiseLevelDisplay.style.color = "orange";
        else noiseLevelDisplay.style.color = "red";
      }
    }
    loop();

  } catch (err) {
    console.error("Monitor Error:", err);
    if (noiseText) noiseText.textContent = "Mic Busy or Blocked";
  }
}

// 2. PAUSE: Kill the monitor (For Privacy or to Free Hardware)
function pauseMonitoring() {
  if (!isMonitoring) return;

  isMonitoring = false;

  // Kill Hardware
  if (monitorStream) {
    monitorStream.getTracks().forEach(t => t.stop());
    monitorStream = null;
  }
  if (monitorCtx) {
    monitorCtx.close();
    monitorCtx = null;
  }

  // --- SAVE & CLAMP THRESHOLD ---
  // If a plane flew over (0.8), cap it at 0.15 (15%)
  let measured = currentNoisePeak * 1.5;
  if (measured > 0.15) measured = 0.15;
  noiseThreshold = Math.max(defaultThreshold, measured);

  // Update UI based on context
  if (isAppBusy) {
    if (noiseText) noiseText.textContent = "Paused (Action in progress)";
    if (noiseStatusContainer) noiseStatusContainer.style.color = "orange";
  } else {
    if (noiseText) noiseText.textContent = "Paused (Privacy Mode)";
    if (noiseStatusContainer) noiseStatusContainer.style.color = "gray";
  }
}

// === TRIGGERS ===

// A. Start Session (User touches Name field)
nameInput.addEventListener('focus', () => {
  sessionActive = true;
  resumeMonitoring();
});

// B. Privacy Protection (Tab Hidden / Blurred / Closed)
document.addEventListener('visibilitychange', () => {
  if (document.hidden) pauseMonitoring();
  else resumeMonitoring();
});
window.addEventListener('blur', pauseMonitoring);
window.addEventListener('focus', resumeMonitoring);
window.addEventListener('beforeunload', pauseMonitoring);


// ------- Audio utils -------
async function fetchBuffer(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return ensureAC().decodeAudioData(await res.arrayBuffer());
}

function trimSilence(buf) {
  const d = buf.getChannelData(0);
  const sr = buf.sampleRate;

  // 1. Find the Peak Volume of the recording
  let peak = 0;
  for (let i = 0; i < d.length; i++) {
    const abs = Math.abs(d[i]);
    if (abs > peak) peak = abs;
  }

  // 2. Define Dynamic Threshold (The "Gate")
  // We set the cutoff at 5% (0.05) of your max volume.
  // - Lip smacks/Breaths are usually < 5% of peak voice.
  // - Vowels are 100% of peak.
  // We also ensure we don't go below the ambient noise floor (noiseThreshold).
  const effectiveThreshold = Math.max(peak * 0.05, noiseThreshold);

  console.log(`Smart Trim: Peak=${peak.toFixed(4)} Threshold=${effectiveThreshold.toFixed(4)}`);

  let s = 0, e = d.length - 1;

  // 3. Scan Forward (Start)
  while (s < e) {
    if (Math.abs(d[s]) >= effectiveThreshold) {
      // Anti-Click Check: Look ahead 100ms to ensure it's sustained sound
      let isRealSound = false;
      const scanWindow = sr * 0.1; // 100ms window
      for (let i = 1; i < scanWindow && (s + i) < e; i++) {
        if (Math.abs(d[s + i]) > effectiveThreshold) {
          isRealSound = true;
          break;
        }
      }
      if (isRealSound) break;
      // If not real sound (just a click), we skip it and keep scanning
      s += scanWindow;
      continue;
    }
    s++;
  }

  // 4. Scan Backward (End)
  // We use a slightly higher threshold for the end to cut breath trails aggressively
  const endThreshold = effectiveThreshold * 0.8;
  while (e > s && Math.abs(d[e]) < endThreshold) e--;

  // Safety: If we trimmed everything away, return original
  if (e - s < sr * 0.1) return buf;

  // 5. Add a tiny bit of "Room Tone" padding (fade in/out feel)
  // This prevents the word from sounding too "chopped"
  const padding = Math.floor(sr * 0.02); // 20ms padding
  const startPad = Math.max(0, s - padding);
  const endPad = Math.min(d.length, e + padding);

  const out = ac.createBuffer(1, endPad - startPad, sr);
  out.copyToChannel(d.subarray(startPad, endPad), 0);
  return out;
}

function makeWS(container, colour) {
  return WaveSurfer.create({
    container, height: 200, waveColor: colour, cursorColor: '#666', responsive: true
  });
}

function renderWS(buf, container, prev, colour) {
  prev?.destroy();
  const ws = makeWS(container, colour);
  if (ws.setBuffer) ws.setBuffer(buf);
  else if (ws.loadDecodedBuffer) ws.loadDecodedBuffer(buf);
  else ws.load(bufferToUrl(buf));
  return ws;
}

function bufferToWavBlob(buffer) {
  const n = buffer.length;
  const sr = buffer.sampleRate;
  const pcm = buffer.getChannelData(0);
  const ab = new ArrayBuffer(44 + n * 2);
  const v = new DataView(ab);
  const w = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
  w(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true);
  w(8, 'WAVE'); w(12, 'fmt '); v.setUint32(16, 16, true);
  v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, sr, true); v.setUint32(28, sr * 2, true);
  v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  w(36, 'data'); v.setUint32(40, n * 2, true);
  for (let i = 0; i < n; i++) v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, pcm[i])) * 0x7FFF, true);
  return new Blob([ab], { type: 'audio/wav' });
}
function bufferToUrl(buffer) { return URL.createObjectURL(bufferToWavBlob(buffer)); }

function renderOverlap() {
  overlapWF.innerHTML = '';
  const sDiv = document.createElement('div');
  const uDiv = document.createElement('div');
  Object.assign(sDiv.style, { position: 'absolute', inset: 0 });
  Object.assign(uDiv.style, { position: 'absolute', inset: 0 });
  overlapWF.style.position = 'relative';
  overlapWF.append(sDiv, uDiv);
  const sWS = makeWS(sDiv, 'rgba(70,130,180,.6)');
  const uWS = makeWS(uDiv, 'rgba(34,139,34,.6)');
  (sWS.setBuffer ?? sWS.loadDecodedBuffer ?? (b => sWS.load(bufferToUrl(b))))(sampleBuf);
  (uWS.setBuffer ?? uWS.loadDecodedBuffer ?? (b => uWS.load(bufferToUrl(b))))(userBuf);
}

// ======= Sample playback (Pauses Monitor) =======
playBtn.addEventListener('click', async () => {
  if (!guardStudentInfo()) return;
  const word = selectedWord;
  if (!word) { sampleSay('Select a word first.'); return; }

  // 1. SET BUSY & STOP MONITOR
  isAppBusy = true;
  pauseMonitoring();

  sampleSay('Loading sample…');
  try {
    sampleBuf = await fetchBuffer(`audio/${word}.${AUDIO_EXT}`);
    sampleBuf = trimSilence(sampleBuf, defaultThreshold);
    const src = ensureAC().createBufferSource();
    src.buffer = sampleBuf;
    src.connect(ensureAC().destination);

    // 2. RESUME MONITOR ON END
    src.onended = () => {
      isAppBusy = false;
      resumeMonitoring(); // <--- Auto Resume
    };

    src.start();
    sampleWS = renderWS(sampleBuf, sampleWF, sampleWS, 'steelblue');
    sampleSay('Sample ready.');
  } catch (e) {
    console.error(e);
    sampleSay('Sample not found.');
    // Safety reset
    isAppBusy = false;
    resumeMonitoring();
  }
});

// ======= Recording (Pauses Monitor) =======
function toggle(rec) {
  recStartBtn.disabled = rec;
  recStopBtn.disabled = !rec;
}

let autoCheck = null;

recStartBtn.addEventListener('click', async () => {
  if (!guardStudentInfo()) return;
  if (!selectedWord) { say('Select a word first.'); return; }

  // 1. SET BUSY & STOP MONITOR
  isAppBusy = true;
  pauseMonitoring();

  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true }
    });

    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    lastRecordingBlob = null;
    mediaRecorder.ondataavailable = e => chunks.push(e.data);

    mediaRecorder.onstop = async () => {
      clearInterval(autoCheck);
      lastRecordingBlob = new Blob(chunks, { type: chunks[0]?.type || 'audio/webm' });
      userBuf = await ensureAC().decodeAudioData(await lastRecordingBlob.arrayBuffer());
      const trimLevel = Math.min(noiseThreshold * 0.5, 0.01);
      userBuf = trimSilence(userBuf, trimLevel);
      userWS = renderWS(userBuf, userWF, userWS, 'forestgreen');
      if (sampleBuf) renderOverlap();
      playUserBtn.disabled = false;
      submitBtn.disabled = false;
      stream.getTracks().forEach(t => t.stop());
      toggle(false);
      say('Done.');

      // 2. RESUME MONITOR (Post-Recording)
      isAppBusy = false;
      resumeMonitoring(); // <--- Auto Resume
    };

    mediaRecorder.start();
    playUserBtn.disabled = true;
    submitBtn.disabled = true;

    // --- Hard Time Limit (5 Seconds) ---
    const MAX_RECORDING_TIME = 5000;
    const safetyTimer = setTimeout(() => {
      if (mediaRecorder.state === 'recording') {
        say('Time limit reached.');
        mediaRecorder.stop();
      }
    }, MAX_RECORDING_TIME);

    // Setup Silence Detection
    const micSrc = ensureAC().createMediaStreamSource(stream);
    const analyser = ensureAC().createAnalyser();
    analyser.fftSize = 2048;
    micSrc.connect(analyser);

    let silenceStart = null;
    const recordingStartTime = Date.now();

    autoCheck = setInterval(() => {
      const buf = new Float32Array(analyser.fftSize);
      analyser.getFloatTimeDomainData(buf);
      const rms = Math.sqrt(buf.reduce((s, x) => s + x * x, 0) / buf.length);
      const isGracePeriod = (Date.now() - recordingStartTime) < START_GRACE_MS;

      if (rms < noiseThreshold) {
        if (!isGracePeriod) {
          silenceStart ??= Date.now();
          if (Date.now() - silenceStart > SILENCE_HOLD_MS && mediaRecorder.state === 'recording') {
            say('Auto-stop: silence detected');
            clearTimeout(safetyTimer); // Cancel safety timer
            mediaRecorder.stop();
          }
        }
      } else {
        silenceStart = null;
      }
    }, ANALYSE_INTERVAL);

    toggle(true);
    say('Recording…');

  } catch (e) {
    console.error(e);
    say('Mic error: ' + (e.name || e.message || e));
    if (stream) stream.getTracks().forEach(t => t.stop());
  }
});

recStopBtn.addEventListener('click', () => {
  if (mediaRecorder?.state === 'recording') mediaRecorder.stop();
});

window.addEventListener('load', async () => {
  ensureAC();
  await loadManifest();
  buildWordList();
  refreshSubmittedColors();
});

playUserBtn.addEventListener('click', () => {
  if (!userBuf) { say('Record something first.'); return; }
  const src = ensureAC().createBufferSource();
  src.buffer = userBuf;
  src.connect(ensureAC().destination);
  src.start();
});

// ======= Submit last recording =======
submitBtn.addEventListener('click', async () => {
  if (!guardStudentInfo()) return;
  if (!selectedWord) { submitSay('Select a word first.'); return; }
  if (!userBuf) { submitSay('Record your pronunciation first.'); return; }

  try {
    submitSay('Normalizing & Encoding...');
    const normBuf = normalizeBuffer(userBuf);
    const sr = normBuf.sampleRate;
    const pcm = normBuf.getChannelData(0);
    const pcm16 = new Int16Array(pcm.length);

    for (let i = 0; i < pcm.length; i++) {
      const s = Math.max(-1, Math.min(1, pcm[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }

    const mp3enc = new lamejs.Mp3Encoder(1, sr, 128);
    const CHUNK = 1152;
    const out = [];
    for (let i = 0; i < pcm16.length; i += CHUNK) {
      const slice = pcm16.subarray(i, i + CHUNK);
      const buff = mp3enc.encodeBuffer(slice);
      if (buff.length) out.push(new Uint8Array(buff));
    }
    const end = mp3enc.flush();
    if (end.length) out.push(new Uint8Array(end));

    const mp3Blob = new Blob(out, { type: 'audio/mpeg' });
    const sid = idInput.value.trim();
    const sname = nameInput.value.trim();

    const formData = new FormData();
    formData.append('file', mp3Blob, `${sid}-${selectedWord}.mp3`);
    formData.append('studentId', sid);
    formData.append('studentName', sname);
    formData.append('word', selectedWord);

    submitSay('Uploading...');
    submitBtn.disabled = true;

    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    if (response.ok) {
      submitSay(`✅ Saved: ${selectedWord}`);
      const prog = loadProgress(sid);
      prog[selectedWord] = true;
      saveProgress(sid, prog);
      refreshSubmittedColors();
    } else {
      submitSay('⚠️ Server Error. Try again.');
    }

  } catch (err) {
    console.error(err);
    submitSay('⚠️ Processing Error.');
  } finally {
    submitBtn.disabled = false;
  }
});

idInput.addEventListener('input', refreshSubmittedColors);
nameInput.addEventListener('input', () => { });