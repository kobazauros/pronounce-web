/**
 * static/js/script.js
 * Optimized for One-Page Layout & Visual Word Status.
 */

const Config = {
    AUTO_STOP_SILENCE_MS: 1500,
    MAX_RECORDING_MS: 5000,
    AUDIO_EXT: 'mp3',
    TARGET_RATE: 16000,
    TRIM_THRESHOLD_FACTOR: 3.5, 
    WORDS_LIMIT: 20,
    COLORS: {
        MODEL: '#0ea5e9', // Sky Blue
        USER: '#f43f5e',  // Rose Red
        GHOST: 'rgba(255, 255, 255, 0.1)',
        STAGE_BG: '#020617' // Dark Slate
    }
};

let WORDS = [];
let audioContext = null; 
let autoCheckInterval = null; 
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
let userProgress = { pre: [], post: [] };

const UI = {
    wordList: document.getElementById('word-list'),
    sampleTitle: document.getElementById('sample-word-placeholder'),
    phonetic: document.getElementById('phonetic-display'),
    playBtn: document.getElementById('play-sample'),
    recStartBtn: document.getElementById('record-start'),
    recStopBtn: document.getElementById('record-stop'),
    playUserBtn: document.getElementById('play-user'),
    submitBtn: document.getElementById('submit-recording'),
    mainStage: document.getElementById('difference-waveform-container'),
    legend: document.getElementById('comparison-legend'),
    msgBox: document.getElementById('message-box'),
    sampleMsg: document.getElementById('sample-message'),
    submitMsg: document.getElementById('submit-msg'),
    testTypeInput: document.getElementById('test-type'),
    statusDot: document.getElementById('status-dot'),
    statusText: document.getElementById('connection-status'),
    noiseLevel: document.getElementById('noise-level-display'),
    noiseIcon: document.getElementById('noise-indicator-icon'),
    progressFill: document.getElementById('progress-bar-fill'),
    progressPercent: document.getElementById('progress-percent')
};

// ======= Helpers =======

const say = txt => { if (UI.msgBox) UI.msgBox.textContent = txt ?? 'Ready'; };

const getAC = async () => {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: Config.TARGET_RATE });
    }
    if (audioContext.state === 'suspended') await audioContext.resume();
    return audioContext;
};

function bufferToWav(buffer) {
    const length = buffer.length * 2;
    const arrayBuffer = new ArrayBuffer(44 + length);
    const view = new DataView(arrayBuffer);
    const writeString = (off, s) => { for (let i = 0; i < s.length; i++) view.setUint8(off + i, s.charCodeAt(i)); };
    writeString(0, 'RIFF'); view.setUint32(4, 36 + length, true);
    writeString(8, 'WAVE'); writeString(12, 'fmt ');
    view.setUint32(16, 16, true); view.setUint16(20, 1, true);
    view.setUint16(22, 1, true); view.setUint32(24, buffer.sampleRate, true);
    view.setUint32(28, buffer.sampleRate * 2, true);
    view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    writeString(36, 'data'); view.setUint32(40, length, true);
    const data = buffer.getChannelData(0);
    for (let i = 0, off = 44; i < data.length; i++, off += 2) {
        const s = Math.max(-1, Math.min(1, data[i]));
        view.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([arrayBuffer], { type: 'audio/wav' });
}

function trimSilence(buffer, threshold = 0.015) {
    const pcm = buffer.getChannelData(0);
    let start = 0, end = pcm.length - 1;
    while (start < pcm.length && Math.abs(pcm[start]) < threshold) start++;
    while (end > start && Math.abs(pcm[end]) < threshold) end--;
    const padding = Math.floor(buffer.sampleRate * 0.03);
    start = Math.max(0, start - padding);
    end = Math.min(pcm.length - 1, end + padding);
    const trimmed = audioContext.createBuffer(1, Math.max(1, end - start), buffer.sampleRate);
    trimmed.copyToChannel(pcm.subarray(start, end), 0);
    return trimmed;
}

function clearStage() {
    if (sampleWS) { try { sampleWS.destroy(); } catch(e){} sampleWS = null; }
    if (userWS) { try { userWS.destroy(); } catch(e){} userWS = null; }
    if (UI.mainStage) {
        UI.mainStage.innerHTML = '';
        UI.mainStage.style.backgroundColor = Config.COLORS.STAGE_BG;
    }
    if (UI.legend) UI.legend.style.opacity = '0';
}

function makeWS(container, colour) {
    // Reduced height dynamically for the one-page fit
    const containerHeight = container.offsetHeight || 180;
    return WaveSurfer.create({
        container: container,
        height: containerHeight, 
        waveColor: colour,
        progressColor: colour,
        cursorWidth: 0,
        interact: false,
        barWidth: 2,
        barGap: 2,
        barRadius: 4,
        normalize: true,
        fillParent: true
    });
}

// ======= Data Management =======

async function loadManifest() {
    try {
        const res = await fetch('/api/words', { cache: 'no-store' });
        const data = await res.json();
        WORDS = Array.isArray(data) ? data : (data.words || []);
        buildWordList();
        await fetchUserProgress();
        if (UI.statusText) {
            UI.statusText.textContent = 'ONLINE';
            UI.statusDot.style.backgroundColor = '#22c55e';
        }
        startNoiseMonitor();
    } catch (e) {
        if (UI.statusText) { UI.statusText.textContent = 'ERROR'; UI.statusDot.style.backgroundColor = '#ef4444'; }
    }
}

async function fetchUserProgress() {
    try {
        const res = await fetch('/get_progress');
        if (res.ok) {
            userProgress = await res.json();
            refreshProgressUI();
        }
    } catch (e) { console.warn("Sync failed", e); }
}

function buildWordList() {
    if (!UI.wordList) return;
    UI.wordList.innerHTML = '';
    const sorted = [...WORDS].sort((a, b) => {
        const wordA = (typeof a === 'object') ? a.word : a;
        const wordB = (typeof b === 'object') ? b.word : b;
        return wordA.localeCompare(wordB);
    });

    sorted.forEach((item) => {
        const w = (typeof item === 'object') ? item.word : item;
        const ipa = (typeof item === 'object') ? item.ipa : null;
        
        const a = document.createElement('a');
        a.href = '#';
        // Added Tailwind classes for better touch targets (py-2.5) and visual feedback
        a.className = 'word-link group flex items-center justify-between w-full px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all border border-transparent hover:border-slate-200';
        a.dataset.word = w;
        if (ipa) a.dataset.ipa = ipa;
        
        a.innerHTML = `<span>${w}</span><i class="status-icon far fa-circle"></i>`;
        
        a.onclick = async (e) => {
            e.preventDefault();
            await getAC();
            if (!monitorStarted) startNoiseMonitor();
            document.querySelectorAll('.word-link').forEach(el => el.classList.remove('active-selection'));
            a.classList.add('active-selection', 'bg-slate-100', 'border-slate-200', 'text-slate-900');
            selectedWord = w;
            resetStageData();
            
            UI.sampleTitle.textContent = w;
            UI.playBtn.disabled = false;
            
            // Show transcription if available, otherwise clear
            if (ipa || a.dataset.ipa) {
                UI.phonetic.textContent = ipa || a.dataset.ipa;
                UI.phonetic.style.opacity = '1';
            } else {
                UI.phonetic.textContent = '/ ... /';
                UI.phonetic.style.opacity = '0.3';
            }
        };
        UI.wordList.appendChild(a);
    });
}

function refreshProgressUI() {
    const type = UI.testTypeInput?.value || 'pre';
    const done = userProgress[type] || [];
    const total = WORDS.length;
    
    document.querySelectorAll('.word-link').forEach(el => {
        const isDone = done.includes(el.dataset.word);
        // Toggle visual state for completed items
        el.classList.toggle('opacity-50', isDone && !el.classList.contains('active-selection'));
        el.classList.toggle('word-submitted', isDone);
        
        const icon = el.querySelector('.status-icon');
        if (icon) {
            if (isDone) {
                icon.className = 'status-icon fas fa-check-circle text-green-500';
            } else {
                icon.className = 'status-icon far fa-circle opacity-20';
            }
        }
    });
    
    const percent = total > 0 ? Math.round((done.length / total) * 100) : 0;
    if (UI.progressFill) UI.progressFill.style.width = `${percent}%`;
    if (UI.progressPercent) UI.progressPercent.textContent = `${percent}%`;
}

function resetStageData() {
    lastRecordingBlob = null;
    userBuf = null;
    clearStage();
    UI.submitBtn.disabled = true;
    UI.playUserBtn.disabled = true;
    UI.recStartBtn.disabled = false;
    UI.recStopBtn.style.opacity = '0';
    UI.recStopBtn.style.pointerEvents = 'none';
    if (UI.testTypeInput) UI.testTypeInput.disabled = false;
    if (UI.submitMsg) UI.submitMsg.textContent = '';
    say('');
}

async function startNoiseMonitor() {
    if (isMonitoring || isAppBusy) return;
    try {
        const ctx = await getAC();
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const source = ctx.createMediaStreamSource(stream);
        const analyzer = ctx.createAnalyser();
        analyzer.fftSize = 2048;
        source.connect(analyzer);
        const buffer = new Float32Array(analyzer.fftSize);
        isMonitoring = true; 
        monitorStarted = true;
        const loop = () => {
            if (!isMonitoring) return;
            requestAnimationFrame(loop);
            analyzer.getFloatTimeDomainData(buffer);
            let peak = 0;
            for (let i = 0; i < buffer.length; i++) peak = Math.max(peak, Math.abs(buffer[i]));
            measuredNoiseFloor = (measuredNoiseFloor * 0.95) + (peak * 0.05);
            if (UI.noiseIcon) UI.noiseIcon.style.backgroundColor = peak < 0.02 ? "#22c55e" : "#f59e0b";
            
            const isQuiet = peak < 0.02;
            if (UI.noiseIcon) UI.noiseIcon.style.backgroundColor = isQuiet ? "#22c55e" : "#f59e0b";
            if (UI.noiseLevel) {
                UI.noiseLevel.textContent = isQuiet ? "QUIET" : "NOISY";
                // Toggle visibility/urgency colors
                UI.noiseLevel.classList.remove('text-slate-300');
                UI.noiseLevel.classList.toggle('text-slate-400', isQuiet);
                UI.noiseLevel.classList.toggle('text-amber-500', !isQuiet);
            }
        };
        loop();
    } catch (err) { 
        console.warn("Monitor Error", err);
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
            if (UI.statusText) { UI.statusText.textContent = 'MIC BLOCKED'; UI.statusDot.style.backgroundColor = '#ef4444'; }
            alert("Microphone access is blocked. Please allow access in your browser settings to use this app.");
        }
    }
}

// ======= Interactions =======

function renderComparison() {
    if (!userBuf) return;
    clearStage();
    UI.legend.style.opacity = '1';
    UI.mainStage.style.position = 'relative';

    const sDiv = document.createElement('div'), uDiv = document.createElement('div');
    
    Object.assign(sDiv.style, { 
        position: 'absolute', top: '0', left: '0', zIndex: '1',
        opacity: '0.6', width: '100%', height: '100%' 
    });
    Object.assign(uDiv.style, { 
        position: 'absolute', top: '0', left: '0', zIndex: '2',
        opacity: '0.9', mixBlendMode: 'screen', width: '100%', height: '100%' 
    });

    UI.mainStage.append(sDiv, uDiv);
    
    if (sampleBuf) {
        const modelCompare = makeWS(sDiv, Config.COLORS.MODEL);
        modelCompare.load(URL.createObjectURL(bufferToWav(sampleBuf)));
    }
    userWS = makeWS(uDiv, Config.COLORS.USER);
    userWS.load(URL.createObjectURL(bufferToWav(userBuf)));
}

UI.playBtn.onclick = async () => {
    if (!selectedWord) return;
    isAppBusy = true; 
    try {
        const res = await fetch(`/static/audio/${selectedWord}.${Config.AUDIO_EXT}`);
        const ctx = await getAC();
        const raw = await ctx.decodeAudioData(await res.arrayBuffer());
        sampleBuf = trimSilence(raw, 0.005); 
        const src = ctx.createBufferSource();
        src.buffer = sampleBuf; 
        src.connect(ctx.destination);
        src.onended = () => { isAppBusy = false; };
        src.start();

        if (userBuf) {
            renderComparison();
        } else {
            clearStage();
            sampleWS = makeWS(UI.mainStage, Config.COLORS.MODEL);
            sampleWS.load(URL.createObjectURL(bufferToWav(sampleBuf)));
        }
    } catch (e) { isAppBusy = false; }
};

UI.recStartBtn.onclick = async () => {
    if (!selectedWord) return;
    const ctx = await getAC();
    isAppBusy = true; 
    UI.recStartBtn.disabled = true;
    UI.recStopBtn.style.opacity = '1';
    UI.recStopBtn.style.pointerEvents = 'auto';
    if (UI.testTypeInput) UI.testTypeInput.disabled = true;
    
    if (sampleWS) sampleWS.setOptions({ waveColor: Config.COLORS.GHOST });
    say('RECORDING...');

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        chunks = [];
        mediaRecorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data); };
        mediaRecorder.onstop = async () => {
            if (autoCheckInterval) clearInterval(autoCheckInterval);
            const rawBlob = new Blob(chunks, { type: 'audio/webm' });
            stream.getTracks().forEach(t => t.stop());
            isAppBusy = false; 
            UI.recStartBtn.disabled = false;
            UI.recStopBtn.style.opacity = '0';
            UI.recStopBtn.style.pointerEvents = 'none';
            if (UI.testTypeInput) UI.testTypeInput.disabled = false;

            const decoded = await ctx.decodeAudioData(await rawBlob.arrayBuffer());
            const thresh = Math.max(0.018, measuredNoiseFloor * Config.TRIM_THRESHOLD_FACTOR);
            userBuf = trimSilence(decoded, thresh); 
            lastRecordingBlob = bufferToWav(userBuf); 
            
            if (lastRecordingBlob.size < 1000) { say('TOO LOW'); return; }
            
            UI.submitBtn.disabled = false;
            UI.playUserBtn.disabled = false;
            say('READY');
            
            renderComparison();
        };
        mediaRecorder.start();
        const startTime = Date.now();
        let silenceStart = null;
        const analyzer = ctx.createAnalyser();
        ctx.createMediaStreamSource(stream).connect(analyzer);
        const dataArr = new Float32Array(analyzer.fftSize);
        autoCheckInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            if (elapsed > Config.MAX_RECORDING_MS) { mediaRecorder.stop(); return; }
            analyzer.getFloatTimeDomainData(dataArr);
            let peak = 0;
            for (let i = 0; i < dataArr.length; i++) peak = Math.max(peak, Math.abs(dataArr[i]));
            if (peak < Math.max(0.012, measuredNoiseFloor * 2.5) && elapsed > 1000) {
                if (!silenceStart) silenceStart = Date.now();
                if (Date.now() - silenceStart > Config.AUTO_STOP_SILENCE_MS) mediaRecorder.stop();
            } else silenceStart = null;
        }, 100);
    } catch (e) { isAppBusy = false; }
};

UI.recStopBtn.onclick = () => { if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop(); };
UI.playUserBtn.onclick = async () => {
    if (!userBuf) return;
    if (!userWS) renderComparison();
    const ctx = await getAC();
    const src = ctx.createBufferSource();
    src.buffer = userBuf;
    src.connect(ctx.destination);
    src.start();
};

UI.submitBtn.onclick = async (e) => {
    e.preventDefault();
    if (!lastRecordingBlob) return;
    if (UI.submitMsg) UI.submitMsg.textContent = 'SAVING...';
    UI.submitBtn.disabled = true;
    if (UI.testTypeInput) UI.testTypeInput.disabled = true;
    const fd = new FormData();
    fd.append('file', lastRecordingBlob, 'attempt.wav');
    fd.append('word', selectedWord);
    fd.append('testType', UI.testTypeInput?.value || 'pre');
    try {
        const res = await fetch('/upload', { method: 'POST', body: fd });
        if (res.ok) { 
            if (UI.submitMsg) UI.submitMsg.textContent = '✅ SAVED'; 
            await fetchUserProgress(); 
            if (UI.testTypeInput) UI.testTypeInput.disabled = false;
        } else { 
            if (UI.submitMsg) UI.submitMsg.textContent = '⚠️ ERROR'; 
            UI.submitBtn.disabled = false; 
            if (UI.testTypeInput) UI.testTypeInput.disabled = false;
        }
    } catch (e) { 
        if (UI.submitMsg) UI.submitMsg.textContent = '⚠️ TIMEOUT'; 
        UI.submitBtn.disabled = false; 
        if (UI.testTypeInput) UI.testTypeInput.disabled = false;
    }
};

if (UI.testTypeInput) UI.testTypeInput.onchange = refreshProgressUI;
window.onload = loadManifest;