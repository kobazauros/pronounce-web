// -------------------------------------------------------------
// script.js – Pronunciation Checker (Thesis Edition)
// -------------------------------------------------------------

// ======= Configuration =======
let WORDS = [];
const AUDIO_EXT = 'mp3';
const TARGET_RATE = 16000; // Force standard rate
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
const noiseBtn = document.getElementById('measure-noise');
const noiseLabel = document.getElementById('noise-result');

// ------- Audio globals -------
let ac;
let sampleBuf, userBuf;
let sampleWS, userWS;
let mediaRecorder, chunks = [];
let lastRecordingBlob = null;
let selectedWord = null;

// thresholds
const defaultThreshold = 0.01; // Was 0.055. Lowered to 1% to catch soft consonants.
const NOISE_MULTIPLIER = 2.0;  // Was 3.0. Reduced to be less sensitive to AC/fans.
let noiseThreshold = defaultThreshold;
const SILENCE_HOLD_MS = 1500;  // Increased from 1200ms to give you a bit more pause time.
const START_GRACE_MS = 2000;   // NEW: Ignore silence for the first 2 seconds.

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

// --- HELPER: Normalize Audio to -1.0 dB ---
function normalizeBuffer(buffer) {
  const data = buffer.getChannelData(0);
  let maxPeak = 0;
  for (let i = 0; i < data.length; i++) {
    const abs = Math.abs(data[i]);
    if (abs > maxPeak) maxPeak = abs;
  }
  if (maxPeak === 0) return buffer;
  const target = 0.89125; // -1.0 dB
  const gain = target / maxPeak;
  const newBuf = ac.createBuffer(1, buffer.length, buffer.sampleRate);
  const newData = newBuf.getChannelData(0);
  for (let i = 0; i < data.length; i++) {
    newData[i] = data[i] * gain;
  }
  return newBuf;
}

// ------- Noise measurement -------
noiseBtn.addEventListener('click', async () => {
  try {
    noiseLabel.textContent = 'Measuring…';
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, sampleRate: TARGET_RATE }
    });
    const ac = ensureAC();
    const src = ac.createMediaStreamSource(stream);
    const analyser = ac.createAnalyser();
    analyser.fftSize = 2048;
    src.connect(analyser);

    let rmsSum = 0, frames = 0;
    const end = Date.now() + 1500;
    while (Date.now() < end) {
      const buf = new Float32Array(analyser.fftSize);
      analyser.getFloatTimeDomainData(buf);
      const rms = Math.sqrt(buf.reduce((s, x) => s + x * x, 0) / buf.length);
      rmsSum += rms; frames++;
      await new Promise(r => setTimeout(r, 50));
    }
    stream.getTracks().forEach(t => t.stop());

    const ambient = rmsSum / frames;
    noiseThreshold = Math.max(ambient * NOISE_MULTIPLIER, defaultThreshold);
    noiseLabel.textContent = `Threshold set ${(noiseThreshold * 100).toFixed(1)} % FS`;
  } catch (err) {
    console.error(err);
    noiseLabel.textContent = 'Noise measure failed';
  }
});

// ------- Audio utils -------
async function fetchBuffer(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return ensureAC().decodeAudioData(await res.arrayBuffer());
}

function trimSilence(buf, threshold) {
  const d = buf.getChannelData(0);
  const sr = buf.sampleRate;
  let s = 0, e = d.length - 1;
  while (s < e && Math.abs(d[s]) < threshold) s++;
  while (e > s && Math.abs(d[e]) < threshold) e--;
  if (e - s < sr * 0.05) return buf;
  const out = ac.createBuffer(1, e - s + 1, sr);
  out.copyToChannel(d.subarray(s, e + 1), 0);
  return out;
}

function makeWS(container, colour) {
  return WaveSurfer.create({
    container,
    height: 200,
    waveColor: colour,
    cursorColor: '#666',
    responsive: true
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
function bufferToUrl(buffer) {
  return URL.createObjectURL(bufferToWavBlob(buffer));
}

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

// ======= Sample playback =======
playBtn.addEventListener('click', async () => {
  if (!guardStudentInfo()) return;
  const word = selectedWord;
  if (!word) {
    sampleSay('Select a word first.');
    return;
  }
  sampleSay('Loading sample…');
  try {
    sampleBuf = await fetchBuffer(`audio/${word}.${AUDIO_EXT}`);
    sampleBuf = trimSilence(sampleBuf, defaultThreshold);
    const src = ensureAC().createBufferSource();
    src.buffer = sampleBuf;
    src.connect(ensureAC().destination);
    src.start();
    sampleWS = renderWS(sampleBuf, sampleWF, sampleWS, 'steelblue');
    sampleSay('Sample ready.');
  } catch (e) {
    console.error(e);
    sampleSay('Sample not found.');
  }
});

// ======= Recording =======
function toggle(rec) {
  recStartBtn.disabled = rec;
  recStopBtn.disabled = !rec;
}

let autoCheck = null;

recStartBtn.addEventListener('click', async () => {
  if (!guardStudentInfo()) return;
  if (!selectedWord) {
    say('Select a word first.');
    return;
  }
  try {
    // --- FIX IS HERE ---
    // We removed 'sampleRate: TARGET_RATE' from constraints.
    // We let the browser pick the hardware native rate (usually 44.1k or 48k)
    // to prevent "OverconstrainedError".
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1, // Mono is usually fine, but if this fails, remove it too.
        echoCancellation: true,
        noiseSuppression: true
        // sampleRate: TARGET_RATE <--- REMOVED THIS
      }
    });

    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    lastRecordingBlob = null;
    mediaRecorder.ondataavailable = e => chunks.push(e.data);

    mediaRecorder.onstop = async () => {
      clearInterval(autoCheck);
      lastRecordingBlob = new Blob(chunks, { type: chunks[0]?.type || 'audio/webm' });

      userBuf = await ensureAC().decodeAudioData(await lastRecordingBlob.arrayBuffer());

      // Trim Silence
      const trimLevel = Math.min(noiseThreshold * 0.5, 0.01);
      userBuf = trimSilence(userBuf, trimLevel);

      userWS = renderWS(userBuf, userWF, userWS, 'forestgreen');

      if (sampleBuf) renderOverlap();
      playUserBtn.disabled = false;
      submitBtn.disabled = false;
      stream.getTracks().forEach(t => t.stop());
      toggle(false);
      say('Done.');
    };
    mediaRecorder.start();
    playUserBtn.disabled = true;
    submitBtn.disabled = true;

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
    console.error(e); // Check your browser console (F12) to see the specific error name
    say('Mic error: ' + (e.name || e));
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
  if (!userBuf) {
    say('Record something first.');
    return;
  }
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

    // 1. NORMALIZE (Boost volume to -1.0dB)
    const normBuf = normalizeBuffer(userBuf);

    // 2. Prepare for MP3 Encoding
    const sr = normBuf.sampleRate;
    const pcm = normBuf.getChannelData(0);
    const pcm16 = new Int16Array(pcm.length);

    for (let i = 0; i < pcm.length; i++) {
      const s = Math.max(-1, Math.min(1, pcm[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
    }

    // 3. Encode MP3
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

    // 4. Create Blob
    const mp3Blob = new Blob(out, { type: 'audio/mpeg' });

    // 5. Prepare Upload Data (WITH NAME)
    const sid = idInput.value.trim();
    const sname = nameInput.value.trim(); // <--- Capture Name

    const formData = new FormData();
    // Filename format: "STUDENTID-WORD.mp3" (standard convention)
    formData.append('file', mp3Blob, `${sid}-${selectedWord}.mp3`);
    formData.append('studentId', sid);
    formData.append('studentName', sname); // <--- Send Name
    formData.append('word', selectedWord);

    submitSay('Uploading...');
    submitBtn.disabled = true;

    // 6. Send to PythonAnywhere
    const response = await fetch('/upload', {
      method: 'POST',
      body: formData
    });

    if (response.ok) {
      submitSay(`✅ Saved: ${selectedWord}`);

      // Update Local Progress
      const prog = loadProgress(sid);
      prog[selectedWord] = true;
      saveProgress(sid, prog);
      refreshSubmittedColors();

    } else {
      submitSay('⚠️ Server Error. Try again.');
      console.error('Server responded with error');
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