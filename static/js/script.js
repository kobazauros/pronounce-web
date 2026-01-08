// -------------------------------------------------------------
// script.js – Corrected for static/audio location & Robust Status
// -------------------------------------------------------------

// ======= Configuration =======
let WORDS = [];
const AUDIO_EXT = 'mp3';
const TARGET_RATE = 16000;
let audioContext = null; 
let autoCheckInterval = null; 

// UI References
const idInput = document.getElementById('student-id');
const nameInput = document.getElementById('student-name');
const testTypeInput = document.getElementById('test-type'); 
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

// Status UI
const statusDot = document.getElementById('status-dot');
const statusText = document.getElementById('connection-status');

// Noise UI
const noiseLevelDisplay = document.getElementById('noise-level-display');
const noiseIndicatorIcon = document.getElementById('noise-indicator-icon');

// ======= State Management =======
let sampleBuf = null;
let userBuf = null;
let sampleWS = null;
let userWS = null;
let mediaRecorder = null;
let chunks = [];
let lastRecordingBlob = null;
let selectedWord = null;
let isAppBusy = false;
let isMonitoring = false;
let monitorStarted = false;

let measuredNoiseFloor = 0.015; 

// ======= Helpers =======
const getAC = async () => {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: TARGET_RATE });
  }
  if (audioContext.state === 'suspended') await audioContext.resume();
  return audioContext;
};

const say = txt => { if (msgBox) msgBox.textContent = txt ?? ''; };
const sampleSay = txt => { if (sampleMsg) sampleMsg.textContent = txt ?? ''; };
const submitSay = txt => { if (submitMsg) submitMsg.textContent = txt ?? ''; };

/**
 * Updates the Navbar Status Indicator
 */
function updateSystemStatus(status) {
    if (!statusText || !statusDot) return;
    
    if (status === 'online') {
        statusText.textContent = 'Online';
        statusDot.style.backgroundColor = '#22c55e'; // Green
    } else if (status === 'offline') {
        statusText.textContent = 'Offline';
        statusDot.style.backgroundColor = '#ef4444'; // Red
    } else {
        statusText.textContent = 'Connecting...';
        statusDot.style.backgroundColor = '#94a3b8'; // Slate
    }
}

function trimSilence(buffer, threshold = 0.01) {
    const pcm = buffer.getChannelData(0);
    let start = 0;
    let end = pcm.length - 1;
    while (start < pcm.length && Math.abs(pcm[start]) < threshold) start++;
    while (end > start && Math.abs(pcm[end]) < threshold) end--;
    const padding = Math.floor(buffer.sampleRate * 0.05);
    start = Math.max(0, start - padding);
    end = Math.min(pcm.length - 1, end + padding);
    const newLength = end - start;
    if (newLength <= 0) return buffer;
    const trimmed = audioContext.createBuffer(1, newLength, buffer.sampleRate);
    trimmed.copyToChannel(pcm.subarray(start, end), 0);
    return trimmed;
}

function bufferToWav(buffer) {
    const length = buffer.length * 2;
    const arrayBuffer = new ArrayBuffer(44 + length);
    const view = new DataView(arrayBuffer);
    const sampleRate = buffer.sampleRate;
    const writeString = (offset, string) => {
        for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
    };
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length, true);
    const data = buffer.getChannelData(0);
    let offset = 44;
    for (let i = 0; i < data.length; i++, offset += 2) {
        const s = Math.max(-1, Math.min(1, data[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([arrayBuffer], { type: 'audio/wav' });
}

function clearOldData() {
    lastRecordingBlob = null;
    userBuf = null;
    if (userWS) { userWS.destroy(); userWS = null; }
    if (sampleWS) { sampleWS.destroy(); sampleWS = null; }
    if (overlapWF) overlapWF.innerHTML = '';
    if (submitBtn) submitBtn.disabled = true;
    if (playUserBtn) playUserBtn.disabled = true;
    if (recStartBtn) recStartBtn.disabled = false;
    if (recStopBtn) recStopBtn.disabled = true;
    submitSay('');
    say('Ready to record.');
}

// ======= Initialization =======
async function loadManifest() {
  updateSystemStatus('connecting');
  try {
    const res = await fetch('/static/audio/index.json', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    
    // Robust parsing logic
    let arr = [];
    if (Array.isArray(data)) arr = data;
    else if (data && Array.isArray(data.words)) arr = data.words;
    
    if (arr.length === 0) throw new Error("Empty manifest data");

    WORDS = arr.map(item => {
      const w = item.word || item;
      return String(w).replace(/\.[^/.]+$/, '');
    }).slice(0, 20);
    
    buildWordList();
    updateSystemStatus('online');
  } catch (e) {
    console.error('Manifest load failed.', e);
    updateSystemStatus('offline');
    say("System Error: Check static/audio/index.json");
  }
}

function buildWordList() {
  if (!wordList) return;
  wordList.innerHTML = '';
  [...WORDS].sort((a, b) => a.localeCompare(b)).forEach(w => {
    const a = document.createElement('a');
    a.href = '#';
    a.textContent = w;
    a.className = 'word-link word-pending p-3 border-2 border-slate-100 rounded-xl text-center text-xs font-black uppercase transition-all duration-200 hover:border-indigo-300 hover:bg-indigo-50 shadow-sm';
    a.dataset.word = w;
    a.addEventListener('click', async (e) => {
      e.preventDefault();
      await getAC();
      if (!monitorStarted) startNoiseMonitor();
      document.querySelectorAll('.word-link').forEach(el => el.classList.remove('active-selection'));
      a.classList.add('active-selection');
      selectedWord = w;
      clearOldData();
      if (sampleTitle) sampleTitle.textContent = w;
      if (playBtn) playBtn.disabled = false;
      sampleSay('Click "Play" to hear the model.');
    });
    wordList.appendChild(a);
  });
  refreshSubmittedColors();
}

async function startNoiseMonitor() {
  if (isMonitoring || isAppBusy) return;
  try {
    const ctx = await getAC();
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const source = ctx.createMediaStreamSource(stream);
    const monitorAnalyser = ctx.createAnalyser();
    monitorAnalyser.fftSize = 2048;
    source.connect(monitorAnalyser);
    const buffer = new Float32Array(monitorAnalyser.fftSize);
    isMonitoring = true; monitorStarted = true;
    function loop() {
      if (!isMonitoring) return;
      requestAnimationFrame(loop);
      monitorAnalyser.getFloatTimeDomainData(buffer);
      let peak = 0;
      for (let i = 0; i < buffer.length; i++) peak = Math.max(peak, Math.abs(buffer[i]));
      measuredNoiseFloor = (measuredNoiseFloor * 0.95) + (peak * 0.05);
      const level = (peak * 1000).toFixed(0);
      if (noiseLevelDisplay) noiseLevelDisplay.textContent = `Level: ${level}`;
      if (noiseIndicatorIcon) {
          noiseIndicatorIcon.style.backgroundColor = peak < 0.02 ? "#22c55e" : (peak < 0.05 ? "#f97316" : "#ef4444");
      }
    }
    loop();
  } catch (err) { console.warn("Monitor Error:", err); }
}

function pauseMonitoring() {
  isMonitoring = false;
}

function makeWS(container, colour) {
  return WaveSurfer.create({
    container, height: 100, waveColor: colour, cursorColor: 'transparent', 
    interact: false, barWidth: 2, barRadius: 3, normalize: true 
  });
}

playBtn.addEventListener('click', async () => {
    if (!selectedWord) return;
    isAppBusy = true; pauseMonitoring(); 
    sampleSay('Loading...');
    try {
        const url = `/static/audio/${selectedWord}.${AUDIO_EXT}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error("Audio file not found");
        const arrayBuf = await res.arrayBuffer();
        const ctx = await getAC();
        const rawBuf = await ctx.decodeAudioData(arrayBuf);
        sampleBuf = trimSilence(rawBuf, 0.005); 
        const src = ctx.createBufferSource();
        src.buffer = sampleBuf; 
        src.connect(ctx.destination);
        src.onended = () => { isAppBusy = false; startNoiseMonitor(); };
        src.start();
        const trimmedUrl = URL.createObjectURL(bufferToWav(sampleBuf));
        if (sampleWS) sampleWS.destroy();
        sampleWS = makeWS('#sample-waveform-container', '#475569');
        sampleWS.load(trimmedUrl);
        sampleSay('Playing...');
    } catch (e) { 
        sampleSay('Audio error.'); isAppBusy = false; startNoiseMonitor(); 
    }
});

recStartBtn.addEventListener('click', async () => {
    if (!selectedWord) return say('Select a word first.');
    const ctx = await getAC();
    isAppBusy = true; pauseMonitoring(); 
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: { echoCancellation: true, autoGainControl: true, noiseSuppression: true } 
        });
        mediaRecorder = new MediaRecorder(stream);
        chunks = [];
        mediaRecorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
        mediaRecorder.onstop = async () => {
            if (autoCheckInterval) clearInterval(autoCheckInterval);
            const rawBlob = new Blob(chunks, { type: 'audio/webm' });
            stream.getTracks().forEach(t => t.stop());
            isAppBusy = false; startNoiseMonitor(); 
            recStartBtn.disabled = false;
            recStopBtn.disabled = true;
            const decodedBuf = await ctx.decodeAudioData(await rawBlob.arrayBuffer());
            userBuf = trimSilence(decodedBuf, Math.max(0.01, measuredNoiseFloor * 1.5)); 
            lastRecordingBlob = bufferToWav(userBuf); 
            if (lastRecordingBlob.size < 1000) { say('Too short.'); return; }
            submitBtn.disabled = false;
            playUserBtn.disabled = false;
            say('Recorded.');
            const blobUrl = URL.createObjectURL(lastRecordingBlob);
            if (userWS) userWS.destroy();
            userWS = makeWS('#user-waveform-container', '#6366f1');
            userWS.load(blobUrl);
            renderComparison(blobUrl);
        };
        mediaRecorder.start();
        recStartBtn.disabled = true;
        recStopBtn.disabled = false;
        say('Recording...');
        const startTime = Date.now();
        let silenceStart = null;
        const micSrc = ctx.createMediaStreamSource(stream);
        const recAnalyser = ctx.createAnalyser();
        micSrc.connect(recAnalyser);
        const dataArr = new Float32Array(recAnalyser.fftSize);
        autoCheckInterval = setInterval(() => {
            recAnalyser.getFloatTimeDomainData(dataArr);
            let peak = 0;
            for (let i = 0; i < dataArr.length; i++) peak = Math.max(peak, Math.abs(dataArr[i]));
            const grace = (Date.now() - startTime) < 1500;
            const dynamicThreshold = Math.max(0.012, measuredNoiseFloor * 2);
            if (peak < dynamicThreshold && !grace) {
                if (!silenceStart) silenceStart = Date.now();
                if (Date.now() - silenceStart > 1500) if (mediaRecorder.state === 'recording') mediaRecorder.stop();
            } else silenceStart = null;
        }, 100);
    } catch (e) { say('Mic denied.'); isAppBusy = false; startNoiseMonitor(); }
});

recStopBtn.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop();
});

playUserBtn.addEventListener('click', async () => {
    if (!userBuf) return;
    const ctx = await getAC();
    const src = ctx.createBufferSource();
    src.buffer = userBuf;
    src.connect(ctx.destination);
    src.start();
    say('Playing recording...');
});

function renderComparison(blobUrl) {
    if (!overlapWF) return;
    overlapWF.innerHTML = '';
    const sDiv = document.createElement('div');
    const uDiv = document.createElement('div');
    Object.assign(sDiv.style, { position: 'absolute', inset: 0, opacity: '0.4' });
    Object.assign(uDiv.style, { position: 'absolute', inset: 0, opacity: '0.8', mixBlendMode: 'screen' });
    overlapWF.style.position = 'relative';
    overlapWF.append(sDiv, uDiv);
    const ws1 = makeWS(sDiv, '#ffffff');
    const ws2 = makeWS(uDiv, '#6366f1');
    ws1.load(URL.createObjectURL(bufferToWav(sampleBuf)));
    ws2.load(blobUrl);
}

submitBtn.addEventListener('click', async (e) => {
    e.preventDefault(); // Safety to prevent implicit form reload
    if (!lastRecordingBlob) return;
    submitSay('Saving...');
    submitBtn.disabled = true;
    const formData = new FormData();
    const sid = idInput?.value || 'unknown';
    formData.append('file', lastRecordingBlob, `${sid}-${selectedWord}.wav`);
    formData.append('word', selectedWord);
    formData.append('testType', testTypeInput?.value || 'pre');
    try {
        const res = await fetch('/upload', { method: 'POST', body: formData });
        if (res.ok) {
            submitSay('✅ Saved');
            const prog = JSON.parse(localStorage.getItem('thesis_prog') || '{}');
            prog[selectedWord] = true;
            localStorage.setItem('thesis_prog', JSON.stringify(prog));
            refreshSubmittedColors();
        } else { submitSay('⚠️ Error'); submitBtn.disabled = false; }
    } catch (e) { submitSay('⚠️ Network Error'); submitBtn.disabled = false; }
});

function refreshSubmittedColors() {
    const prog = JSON.parse(localStorage.getItem('thesis_prog') || '{}');
    document.querySelectorAll('.word-link').forEach(el => {
        if (prog[el.dataset.word]) {
            el.classList.add('word-submitted');
            el.classList.remove('word-pending');
        }
    });
}

window.addEventListener('load', loadManifest);