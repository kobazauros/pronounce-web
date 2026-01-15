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

function updateSettingsMeter(peak) {
    if (!UI.settingsMeter) return;

    // Log scale for natural movement
    // Peak is 0.0 to 1.0
    // Visual boost: * 5 to make normal speech fill ~50%
    const percent = Math.min(100, Math.max(0, peak * 400)); // amplified for visibility

    UI.settingsMeter.style.width = `${percent}%`;

    // Color coding
    if (percent > 95) UI.settingsMeter.className = 'h-full bg-red-500 transition-all duration-75';
    else if (percent > 60) UI.settingsMeter.className = 'h-full bg-green-500 transition-all duration-75';
    else UI.settingsMeter.className = 'h-full bg-sky-500 transition-all duration-75';

    if (UI.settingsNoiseLabel) {
        if (percent > 95) UI.settingsNoiseLabel.innerText = "CLIPPING!";
        else if (percent > 10) UI.settingsNoiseLabel.innerText = "GOOD";
        else UI.settingsNoiseLabel.innerText = "LOW";
    }
}

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
let microphoneStream = null;
let measuredNoiseFloor = 0.015;
let userProgress = { pre: [], post: [] };
let lockedStage = null; // Fix: Global lock state
let isLoggingEnabled = window.ENABLE_LOGGING || false;
let lastLogTime = 0;

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
    progressPercent: document.getElementById('progress-percent'),
    // loggingToggle removed
    // Settings UI
    openSettingsBtn: document.getElementById('open-settings-btn'),
    closeSettingsBtn: document.getElementById('close-settings-btn'),
    settingsModal: document.getElementById('audio-settings-modal'),

    // Tips UI
    openTipsBtn: document.getElementById('open-tips-btn'),
    closeTipsBtn: document.getElementById('close-tips-btn'),
    tipsModal: document.getElementById('recording-tips-modal'),
    inputSelect: document.getElementById('audio-input-select'),
    modeFidelityBtn: document.getElementById('mode-fidelity'),
    modeReductionBtn: document.getElementById('mode-reduction'),
    modeValue: document.getElementById('audio-mode-value'),
    settingsMeter: document.getElementById('settings-meter-bar'),
    settingsNoiseLabel: document.getElementById('settings-noise-label'),
    mobileStageLabel: document.getElementById('mobile-stage-label'),
    nextWordBtn: document.getElementById('next-word-btn')
};

// ======= Audio Config State =======
const AudioState = {
    selectedDeviceId: 'default',
    mode: 'fidelity', // 'fidelity' | 'reduction'
    knownDevices: [], // Track devices for auto-switching logic
    constraints: {
        fidelity: { echoCancellation: false, noiseSuppression: false, autoGainControl: false, channelCount: 1 },
        reduction: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 }
    }
};

// ======= Helpers =======

const say = txt => { if (UI.msgBox) UI.msgBox.textContent = txt ?? 'Ready'; };

const logEvent = async (event, data = {}) => {
    if (!isLoggingEnabled && event !== 'system_init') return; // system_init might force log? No.
    try {
        await fetch('/api/log_event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event, timestamp: Date.now() / 1000, ...data })
        });
    } catch (e) {
        // Silent fail
    }
};

const getAC = async () => {
    if (!audioContext) {
        // Use native sample rate for better compatibility/latency
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
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

function trimSilence(buffer) {
    const pcm = buffer.getChannelData(0);
    const sr = buffer.sampleRate;
    const frameSize = Math.floor(sr * 0.02); // 20ms frames
    const nFrames = Math.floor(pcm.length / frameSize);

    // Calculate Noise Floor from the buffer content (Robustness fix)
    let rmsValues = [];
    for (let i = 0; i < nFrames; i++) {
        let sumSq = 0;
        for (let j = 0; j < frameSize; j++) {
            const val = pcm[i * frameSize + j];
            sumSq += val * val;
        }
        rmsValues.push(Math.sqrt(sumSq / frameSize));
    }
    // Calculate Local Floor (Backup)
    rmsValues.sort((a, b) => a - b);
    const floorIndex = Math.floor(rmsValues.length * 0.1);
    const localFloor = rmsValues[floorIndex] || 0.01;

    // Determine Effective Floor: Prefer Live Monitor, Fallback to Local
    // If Monitor is Dead (<0.0001), use Local.
    let effectiveFloor = localFloor;
    if (typeof measuredNoiseFloor !== 'undefined' && measuredNoiseFloor > 0.0001) {
        // Trust live monitor but sanity check against local (e.g. don't go below local/2)
        effectiveFloor = measuredNoiseFloor;
    }

    // Thresholds (Hybrid)
    // Optimization found 3.0 (Live) vs 4.0 (Local). Using conservative (higher) to be safe.
    const volThresh = Math.max(0.015, effectiveFloor * Config.TRIM_THRESHOLD_FACTOR);
    const sensitiveThresh = Math.max(0.005, effectiveFloor * 2.5);
    const zcrThresh = 0.1;

    let startFrame = 0;
    let endFrame = nFrames - 1;

    // Helper: Is frame speech?
    const isSpeech = (idx) => {
        let sumSq = 0;
        let crosses = 0;
        const offset = idx * frameSize;

        for (let i = 0; i < frameSize; i++) {
            const val = pcm[offset + i];
            sumSq += val * val;
            if (i > 0 && (val > 0) !== (pcm[offset + i - 1] > 0)) crosses++;
        }

        const rms = Math.sqrt(sumSq / frameSize);
        const zcr = crosses / frameSize;

        // Keep if LOUD or (QUIET but HISSY)
        return (rms > volThresh) || (rms > sensitiveThresh && zcr > zcrThresh);
    };

    // Scan Forward
    while (startFrame < nFrames && !isSpeech(startFrame)) startFrame++;

    // Scan Backward
    while (endFrame > startFrame && !isSpeech(endFrame)) endFrame--;

    // Start/End in samples
    // Add 10ms padding (tighter cut)
    const padding = Math.floor(sr * 0.01);
    let startSample = Math.max(0, startFrame * frameSize - padding);
    let endSample = Math.min(pcm.length, (endFrame + 1) * frameSize + padding);

    // Ensure valid duration
    if (endSample <= startSample) {
        startSample = 0;
        endSample = pcm.length;
    }

    const trimmed = audioContext.createBuffer(1, Math.max(1, endSample - startSample), sr);
    trimmed.copyToChannel(pcm.subarray(startSample, endSample), 0);
    return trimmed;
}

function clearStage() {
    if (sampleWS) { try { sampleWS.destroy(); } catch (e) { } sampleWS = null; }
    if (userWS) { try { userWS.destroy(); } catch (e) { } userWS = null; }
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
        cursorColor: colour, // Match cursor to wave color
        cursorWidth: 2,      // Enable cursor
        interact: false,
        barWidth: 2,
        barGap: 2,
        barRadius: 4,
        normalize: true,
        fillParent: true
    });
}

// ... (keep intervening code if any, but replacing chunks) ...

if (UI.playBtn) UI.playBtn.onclick = async () => {
    if (!selectedWord) return;
    if (isAppBusy) return; // Prevent double clicks
    isAppBusy = true;

    // Stop any existing playback
    if (sampleWS) sampleWS.stop();
    if (userWS) userWS.stop();

    try {
        // If we already have the sample buffer and visualization, just play it
        if (sampleBuf && sampleWS) {
            sampleWS.play();
            sampleWS.once('finish', () => { isAppBusy = false; });
            return;
        }

        const res = await fetch(`/static/audio/${selectedWord}.${Config.AUDIO_EXT}`);
        const ctx = await getAC();
        const raw = await ctx.decodeAudioData(await res.arrayBuffer());
        sampleBuf = trimSilence(raw, 0.005);

        // Re-render stage if needed
        if (userBuf) {
            renderComparison();
        } else {
            clearStage();
            sampleWS = makeWS(UI.mainStage, Config.COLORS.MODEL);
            sampleWS.load(URL.createObjectURL(bufferToWav(sampleBuf)));
        }

        // Wait for ready then play
        if (sampleWS) {
            sampleWS.once('ready', () => {
                sampleWS.play();
                sampleWS.once('finish', () => { isAppBusy = false; });
            });
            // If already ready (sync load case), play immediately
            if (sampleWS.isReady) { // Note: V7 property might differ, relying on event is safer or check duration
                sampleWS.play();
                sampleWS.once('finish', () => { isAppBusy = false; });
            }
        }

    } catch (e) {
        console.error("Play Sample Error", e);
        isAppBusy = false;
    }
};

// ...

if (UI.playUserBtn) UI.playUserBtn.onclick = async () => {
    if (!userBuf) return;
    if (isAppBusy) return;

    // Stop any existing playback
    if (sampleWS) sampleWS.stop();
    if (userWS) userWS.stop();

    if (!userWS) renderComparison();

    if (userWS) {
        userWS.play();
    }
};

// Logging toggle listener removed (controlled by server config)

// ======= Data Management =======

async function loadWordList() {
    try {
        const response = await fetch('/api/word_list', { cache: 'no-store' });
        const data = await response.json();
        WORDS = Array.isArray(data) ? data : (data.words || []);
        buildWordList();
        await fetchUserProgress();
        if (UI.statusText) {
            UI.statusText.textContent = 'ONLINE';
            UI.statusDot.style.backgroundColor = '#22c55e';
        }
        startNoiseMonitor();

        // 3. Universal: Auto-Select First INCOMPLETE Word if none selected
        if (!selectedWord && WORDS.length > 0) {
            // Find first word alphabetically (as built in list)
            const sorted = [...WORDS].sort((a, b) => {
                const wordA = (typeof a === 'object') ? a.word : a;
                const wordB = (typeof b === 'object') ? b.word : b;
                return wordA.localeCompare(wordB);
            });

            // Determine active stage
            const stage = UI.testTypeInput?.value || 'pre';
            const completed = userProgress[stage] || [];

            // Find first incomplete word
            const target = sorted.find(item => {
                const w = (typeof item === 'object') ? item.word : item;
                return !completed.includes(w);
            }) || sorted[0]; // Fallback to first if all done

            const w = (typeof target === 'object') ? target.word : target;

            // Trigger UI click to set state
            const link = document.querySelector(`.word-link[data-word="${w}"]`);
            if (link) {
                // Small delay to ensure UI is ready
                setTimeout(() => {
                    link.click();
                    say(`Auto-selected "${w}"`);
                }, 500);
            }
        }
    } catch (e) {
        if (UI.statusText) { UI.statusText.textContent = 'ERROR'; UI.statusDot.style.backgroundColor = '#ef4444'; }
    }
}

async function fetchUserProgress() {
    try {
        const res = await fetch('/get_progress');
        if (res.ok) {
            const data = await res.json();
            // Backend now returns { progress: ..., stage: ... }
            if (data.progress) {
                userProgress = data.progress;

                // Enforce Stage Locking (Strict Flow)
                if (data.stage && UI.testTypeInput) {
                    lockedStage = data.stage; // Fix: Store lock state
                    UI.testTypeInput.value = data.stage;
                    UI.testTypeInput.disabled = true;

                    // Visual feedback for locked stage
                    UI.testTypeInput.title = "Stage locked by curriculum progress";
                    if (data.stage === 'post') {
                        UI.testTypeInput.classList.add('bg-slate-100', 'text-slate-500');
                    }
                } else {
                    lockedStage = null; // Unlock if no stage forced
                }
            } else {
                // Fallback for types (should not happen if backend is updated)
                userProgress = data;
            }
            refreshProgressUI();
            updateMobileLabel(); // Update label on load/sync
        }
    } catch (e) { console.warn("Sync failed", e); }
}

const isMobile = () => window.innerWidth < 1024; // Matches Tailwind lg breakpoint

function updateMobileLabel() {
    if (!UI.mobileStageLabel || !UI.testTypeInput) return;
    const stage = UI.testTypeInput.value;
    UI.mobileStageLabel.textContent = stage === 'pre' ? 'PRE-TEST' : 'POST-TEST';
    // Style update based on stage
    if (stage === 'post') {
        UI.mobileStageLabel.classList.remove('text-slate-400');
        UI.mobileStageLabel.classList.add('text-indigo-500');
    } else {
        UI.mobileStageLabel.classList.add('text-slate-400');
        UI.mobileStageLabel.classList.remove('text-indigo-500');
    }
}

function autoProceed() {
    if (!selectedWord) return;

    // 1. Find current index
    const sortedWords = [...WORDS].sort((a, b) => {
        const wordA = (typeof a === 'object') ? a.word : a;
        const wordB = (typeof b === 'object') ? b.word : b;
        return wordA.localeCompare(wordB);
    });

    const currentIndex = sortedWords.findIndex(item => {
        const w = (typeof item === 'object') ? item.word : item;
        return w === selectedWord;
    });

    // 2. Find next word
    if (currentIndex >= 0 && currentIndex < sortedWords.length - 1) {
        const nextItem = sortedWords[currentIndex + 1];
        const nextWord = (typeof nextItem === 'object') ? nextItem.word : nextItem;

        // 3. Trigger selection
        const link = document.querySelector(`.word-link[data-word="${nextWord}"]`);
        if (link) {
            say(`Auto-advancing to "${nextWord}"...`);
            setTimeout(() => {
                link.click();
                // REMOVED SCROLL: User requested to keep viewport steady
                // link.scrollIntoView({ behavior: 'smooth', block: 'center' }); 
            }, 1500); // 1.5s delay for user to see result
        }
    } else {
        say("All words completed!");
    }
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

            // Enforce "Listen Before Record"
            UI.recStartBtn.disabled = true;
            UI.recStartBtn.style.opacity = '0.5';
            UI.recStartBtn.style.cursor = 'not-allowed';

            if (ipa) {
                // Ensure no double slashes if data already has them
                const cleanIpa = ipa.replace(/\//g, '');
                UI.phonetic.textContent = `/${cleanIpa}/`;
                UI.phonetic.style.opacity = '1';
            } else {
                UI.phonetic.style.opacity = '0';
            }
            if (UI.submitBtn) UI.submitBtn.disabled = true;

            // Check if already completed to enable Next
            if (UI.nextWordBtn) {
                const stage = UI.testTypeInput?.value || 'pre';
                const done = userProgress[stage] || [];
                const isDone = done.includes(w);
                UI.nextWordBtn.disabled = !isDone;
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
    UI.recStopBtn.style.pointerEvents = 'none';

    // Fix: Respect locked stage
    if (UI.testTypeInput) {
        if (lockedStage) {
            UI.testTypeInput.value = lockedStage;
            UI.testTypeInput.disabled = true;
        } else {
            UI.testTypeInput.disabled = false;
        }
    }
    if (UI.submitMsg) UI.submitMsg.textContent = '';
    say('');
}

async function startNoiseMonitor() {
    if (isMonitoring) return;

    if (!UI.noiseIcon) UI.noiseIcon = document.getElementById('noise-indicator-icon');
    if (!UI.noiseLevel) UI.noiseLevel = document.getElementById('noise-level-display');

    try {
        if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const ctx = audioContext;

        if (!microphoneStream) {
            const constraints = {
                audio: {
                    deviceId: AudioState.selectedDeviceId !== 'default' ? { exact: AudioState.selectedDeviceId } : undefined,
                    ...AudioState.constraints[AudioState.mode]
                }
            };
            console.log("Using Constraints:", constraints);
            microphoneStream = await navigator.mediaDevices.getUserMedia(constraints);

            // VERIFICATION: Check what the browser actually gave us
            const track = microphoneStream.getAudioTracks()[0];
            if (track) {
                const settings = track.getSettings();
                console.log("Actual Applied Settings:", {
                    echoCancellation: settings.echoCancellation,
                    noiseSuppression: settings.noiseSuppression,
                    autoGainControl: settings.autoGainControl,
                    deviceId: settings.deviceId
                });
            }
        }

        // Try to resume if suspended
        if (ctx.state === 'suspended') {
            ctx.resume().catch(() => { });
        }

        const source = ctx.createMediaStreamSource(microphoneStream);
        const analyzer = ctx.createAnalyser();
        analyzer.fftSize = 2048;
        source.connect(analyzer);

        const buffer = new Float32Array(analyzer.fftSize);
        isMonitoring = true;
        monitorStarted = true;

        const loop = () => {
            if (!isMonitoring) return;
            requestAnimationFrame(loop);

            // If strictly suspended, notify user
            if (ctx.state === 'suspended') {
                if (UI.noiseLevel && UI.noiseLevel.textContent !== "CLICK PAGE") {
                    UI.noiseLevel.textContent = "CLICK PAGE";
                    UI.noiseLevel.className = "text-[9px] font-bold text-amber-500 uppercase tracking-widest";
                }
                return;
            }

            // Check Active States (Recording / Playback)
            const isRec = (mediaRecorder && mediaRecorder.state === 'recording') || !!recorderNode;
            const isPlaying = (sampleWS && sampleWS.isPlaying()) || (userWS && userWS.isPlaying());

            if (isRec || isPlaying) {
                if (UI.noiseLevel) {
                    const status = isRec ? "RECORDING" : "PLAYBACK";
                    if (UI.noiseLevel.textContent !== status) {
                        UI.noiseLevel.textContent = status;
                        UI.noiseLevel.className = "text-[9px] font-bold text-sky-500 uppercase tracking-widest transition-colors";
                    }
                }
                // Settings Meter should still update if modal is open!
                if (!UI.settingsModal.classList.contains('hidden')) {
                    // Get data even if playing/recording to show input activity
                    analyzer.getFloatTimeDomainData(buffer);
                    let peak = 0;
                    for (let i = 0; i < buffer.length; i++) peak = Math.max(peak, Math.abs(buffer[i]));
                    updateSettingsMeter(peak);
                }

                if (UI.noiseIcon) {
                    UI.noiseIcon.style.backgroundColor = isRec ? "#f43f5e" : "#0ea5e9";
                    UI.noiseIcon.style.transform = "scale(1)";
                }
                return; // Skip main dashboard noise icon update
            }

            analyzer.getFloatTimeDomainData(buffer);
            let peak = 0;
            for (let i = 0; i < buffer.length; i++) peak = Math.max(peak, Math.abs(buffer[i]));

            // Update Settings Meter if open
            if (UI.settingsModal && !UI.settingsModal.classList.contains('hidden')) {
                updateSettingsMeter(peak);
            }

            // Asymmetric Attack/Decay for Noise Floor
            // Goal: Track the BACKGROUND noise, not the speech.
            if (peak < measuredNoiseFloor) {
                // Decay quickly (it got quieter, so the floor is lower)
                measuredNoiseFloor = (measuredNoiseFloor * 0.90) + (peak * 0.10);
            } else {
                // Attack slowly (it got louder, might be speech, don't inflate the floor too much)
                // But still track rising ambient noise (fan spinning up)
                measuredNoiseFloor = (measuredNoiseFloor * 0.9995) + (peak * 0.0005);
            }

            const isQuiet = peak < 0.02;
            if (UI.noiseIcon) {
                UI.noiseIcon.style.backgroundColor = isQuiet ? "#22c55e" : "#f59e0b";
                UI.noiseIcon.style.transform = isQuiet ? "scale(1)" : `scale(${1 + peak * 5})`;
            }
            if (UI.noiseLevel) {
                // Debug: Show the floor value in the UI tooltip or title
                UI.noiseLevel.title = `Floor: ${measuredNoiseFloor.toFixed(4)}`;
                UI.noiseLevel.textContent = isQuiet ? "QUIET" : "NOISY";
                UI.noiseLevel.className = isQuiet
                    ? "text-[9px] font-bold text-slate-400 uppercase tracking-widest transition-colors"
                    : "text-[9px] font-bold text-amber-500 uppercase tracking-widest transition-colors";
            }
            if (isLoggingEnabled && Date.now() - lastLogTime > 1000) {
                const db = 20 * Math.log10(peak || 0.0001);
                logEvent('noise_sample', { peak, db, noiseFloor: measuredNoiseFloor });
                lastLogTime = Date.now();
            }
        };
        loop();

    } catch (err) {
        console.warn("Monitor Error", err);
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
            if (UI.statusText) {
                UI.statusText.textContent = 'MIC BLOCKED';
                UI.statusDot.style.backgroundColor = '#ef4444';
            }
            if (UI.noiseLevel) UI.noiseLevel.textContent = "BLOCKED";
            alert("Microphone access is blocked. Please allow access to use this app.");
        }
    }
}

// ======= Interactions =======

// ======= Audio Device Auto-Switching =======
async function handleDeviceChange() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const inputs = devices.filter(d => d.kind === 'audioinput');
        const currentIds = inputs.map(d => d.deviceId);

        // 1. Detect New Devices (Plugged In)
        // Find devices present now but not in knownDevices
        const newDevice = inputs.find(d => !AudioState.knownDevices.includes(d.deviceId));

        if (newDevice) {
            console.log("[AutoSwitch] New Device Detected:", newDevice.label);
            AudioState.selectedDeviceId = newDevice.deviceId;

            // Optional: Visual Feedback via the header
            const header = document.getElementById('sample-word-placeholder');
            const originalText = header ? header.innerText : "";
            if (header) {
                header.innerText = `Detected: ${newDevice.label.slice(0, 20)}...`;
                setTimeout(() => header.innerText = originalText, 3000);
            }
        }

        // 2. Detect Removed Device (Unplugged)
        // Check if currently selected device is gone
        if (!currentIds.includes(AudioState.selectedDeviceId)) {
            console.log("[AutoSwitch] Selected Device Unplugged. Falling back.");
            if (inputs.length > 0) {
                AudioState.selectedDeviceId = inputs[0].deviceId;
            }
        }

        // 3. Sync State & Restart
        AudioState.knownDevices = currentIds;
        initAudioSettings(); // Re-populate UI
        restartAudioStream(); // Re-connect audio

    } catch (e) {
        console.error("Device Auto-Switch Failed:", e);
    }
}

navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange);

// ======= Audio Settings Logic =======
async function initAudioSettings() {
    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const inputs = devices.filter(d => d.kind === 'audioinput');

        // INITIALIZE TRACKING (First Run)
        if (AudioState.knownDevices.length === 0) {
            AudioState.knownDevices = inputs.map(d => d.deviceId);
        }

        // Populate Select
        if (UI.inputSelect) {
            UI.inputSelect.innerHTML = '';
            inputs.forEach(device => {
                const opt = document.createElement('option');
                opt.value = device.deviceId;
                opt.text = device.label || `Microphone ${UI.inputSelect.length + 1}`;
                if (device.deviceId === AudioState.selectedDeviceId) opt.selected = true;
                UI.inputSelect.appendChild(opt);
            });
            // Enforce selection if empty (e.g. initial load)
            if (AudioState.selectedDeviceId === 'default' && inputs.length > 0) {
                // Try to find default or pick first
                AudioState.selectedDeviceId = inputs[0].deviceId;
                UI.inputSelect.value = inputs[0].deviceId;
            }
        }
    } catch (e) { console.warn("Device Enumeration Failed", e); }
}

async function restartAudioStream() {
    // 1. Stop existing tracks
    if (microphoneStream) {
        microphoneStream.getTracks().forEach(track => track.stop());
        microphoneStream = null;
    }
    // 2. Disconnect nodes
    if (recordingSource) { recordingSource.disconnect(); recordingSource = null; }

    // 3. Restart Monitoring (will fetch new stream)
    isMonitoring = false; // Force restart
    await startNoiseMonitor();
}

// Event Listeners for Settings
if (UI.openSettingsBtn) {
    UI.openSettingsBtn.onclick = async () => {
        UI.settingsModal.classList.remove('hidden');
        await getAC(); // Request permissions first
        await initAudioSettings();
        await startNoiseMonitor(); // Ensure meter is running
    };
}

if (UI.closeSettingsBtn) {
    UI.closeSettingsBtn.onclick = () => {
        UI.settingsModal.classList.add('hidden');
    };
}

// Event Listeners for Tips Modal
if (UI.openTipsBtn) {
    UI.openTipsBtn.onclick = () => {
        if (UI.tipsModal) UI.tipsModal.classList.remove('hidden');
    };
}
if (UI.closeTipsBtn) {
    UI.closeTipsBtn.onclick = () => {
        if (UI.tipsModal) UI.tipsModal.classList.add('hidden');
    };
}

if (UI.inputSelect) {
    UI.inputSelect.onchange = async (e) => {
        AudioState.selectedDeviceId = e.target.value;
        await restartAudioStream();
    };
}

// Mode Selection Logic
const setMode = async (mode) => {
    AudioState.mode = mode;
    UI.modeValue.value = mode;

    if (mode === 'fidelity') {
        UI.modeFidelityBtn.classList.add('active', 'bg-sky-50', 'text-sky-700', 'border-sky-200');
        UI.modeFidelityBtn.classList.remove('bg-white', 'text-slate-500', 'border-slate-200');

        UI.modeReductionBtn.classList.remove('active', 'bg-sky-50', 'text-sky-700', 'border-sky-200');
        UI.modeReductionBtn.classList.add('bg-white', 'text-slate-500', 'border-slate-200');
    } else {
        UI.modeReductionBtn.classList.add('active', 'bg-sky-50', 'text-sky-700', 'border-sky-200');
        UI.modeReductionBtn.classList.remove('bg-white', 'text-slate-500', 'border-slate-200');

        UI.modeFidelityBtn.classList.remove('active', 'bg-sky-50', 'text-sky-700', 'border-sky-200');
        UI.modeFidelityBtn.classList.add('bg-white', 'text-slate-500', 'border-slate-200');
    }
    await restartAudioStream();
};

if (UI.modeFidelityBtn) UI.modeFidelityBtn.onclick = () => setMode('fidelity');
if (UI.modeReductionBtn) UI.modeReductionBtn.onclick = () => setMode('reduction');

if (UI.nextWordBtn) UI.nextWordBtn.onclick = () => {
    autoProceed();
    // Disable self until next logical state? No, user might want to skip.
    // Actually, "autoProceed" selects the *next* word.
    // The selection logic triggers enable/disable based on that *next* word's status.
};


// ======= Visual Feedback Helpers =======

function showProcessing() {
    if (!UI.mainStage) return;
    // Check if exists
    if (document.querySelector('.processing-overlay')) return;

    const overlay = document.createElement('div');
    overlay.className = 'processing-overlay';
    overlay.innerHTML = `
        <div class="processing-spinner"></div>
        <span class="text-xs font-bold text-slate-500 uppercase tracking-widest">Analysing...</span>
    `;
    UI.mainStage.appendChild(overlay);
}

function hideProcessing() {
    const overlay = document.querySelector('.processing-overlay');
    if (overlay) {
        overlay.style.opacity = '0';
        setTimeout(() => overlay.remove(), 300);
    }
}

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
        sampleWS = makeWS(sDiv, Config.COLORS.MODEL);
        sampleWS.load(URL.createObjectURL(bufferToWav(sampleBuf)));
    }
    userWS = makeWS(uDiv, Config.COLORS.USER);
    userWS.load(URL.createObjectURL(bufferToWav(userBuf)));
}

if (UI.playBtn) UI.playBtn.onclick = async () => {
    if (!selectedWord) return;
    logEvent('play_example', { word: selectedWord });
    if (isAppBusy) return;

    // Stop any existing playback
    if (sampleWS) sampleWS.stop();
    if (userWS) userWS.stop();

    try {
        // If we already have the sample buffer and visualization, just play it
        if (sampleBuf && sampleWS) {
            sampleWS.play();
            // Unlock Recording when playback starts/happens
            UI.recStartBtn.disabled = false;
            UI.recStartBtn.style.opacity = '1';
            UI.recStartBtn.style.cursor = 'pointer';

            // Do NOT set isAppBusy for playback duration
            return;
        }

        isAppBusy = true; // Block strictly during fetch/decode
        const res = await fetch(`/static/audio/${selectedWord}.${Config.AUDIO_EXT}`);
        const ctx = await getAC();
        const raw = await ctx.decodeAudioData(await res.arrayBuffer());
        sampleBuf = raw;

        // Re-render stage if needed
        if (userBuf) {
            renderComparison();
        } else {
            clearStage();
            sampleWS = makeWS(UI.mainStage, Config.COLORS.MODEL);
            sampleWS.load(URL.createObjectURL(bufferToWav(sampleBuf)));
        }

        // Wait for ready then play
        if (sampleWS) {
            if (sampleWS.isReady) {
                isAppBusy = false;
                sampleWS.play();
                // Unlock Recording
                UI.recStartBtn.disabled = false;
                UI.recStartBtn.style.opacity = '1';
                UI.recStartBtn.style.cursor = 'pointer';
            } else {
                sampleWS.once('ready', () => {
                    isAppBusy = false;
                    sampleWS.play();
                    // Unlock Recording
                    UI.recStartBtn.disabled = false;
                    UI.recStartBtn.style.opacity = '1';
                    UI.recStartBtn.style.cursor = 'pointer';
                });
            }
        } else {
            isAppBusy = false;
        }

    } catch (e) {
        console.error("Play Sample Error", e);
        isAppBusy = false;
    }
};

// Global State Updates
let rawChunks = [];
let recorderNode = null;
let recordingSource = null;
let workletLoaded = false;

// Helper: Securely load worklet
async function loadRecorderWorklet(ctx) {
    if (workletLoaded) return;
    try {
        await ctx.audioWorklet.addModule('/static/js/recorder-worklet.js');
        workletLoaded = true;
    } catch (e) { console.error("Worklet Load Failed", e); }
}

async function stopRecording() {
    if (!recorderNode) return;

    // Stop & Disconnect Source (Crucial fix for distortion/slow-down)
    if (recordingSource) {
        recordingSource.disconnect();
        recordingSource = null;
    }

    // Stop & Disconnect Recorder
    recorderNode.disconnect();
    recorderNode = null;

    // Stop auto-check
    if (autoCheckInterval) clearInterval(autoCheckInterval);

    // UI Updates
    isAppBusy = true; // Busy processing
    say('PROCESSING...');
    UI.recStartBtn.disabled = true;
    UI.recStopBtn.style.opacity = '0';
    UI.recStopBtn.style.pointerEvents = 'none';
    if (UI.testTypeInput) UI.testTypeInput.disabled = false;

    // UX: Show "Processing..." Overlay
    showProcessing();

    // UX: Show "Processing..." Overlay
    showProcessing();

    // Compile Audio
    const ctx = audioContext;
    if (rawChunks.length === 0) { say('EMPTY'); isAppBusy = false; UI.recStartBtn.disabled = false; return; }

    // Flatten chunks
    const totalLen = rawChunks.reduce((acc, c) => acc + c.length, 0);
    const result = new Float32Array(totalLen);
    let offset = 0;
    for (const chunk of rawChunks) {
        result.set(chunk, offset);
        offset += chunk.length;
    }

    // Create Wav Blob
    const buffer = ctx.createBuffer(1, totalLen, ctx.sampleRate);
    buffer.copyToChannel(result, 0);
    const wavBlob = bufferToWav(buffer);
    lastRecordingBlob = wavBlob;

    logEvent('record_stop', { size: wavBlob.size });

    // Upload to Server for Robust Trimming
    try {
        const formData = new FormData();
        formData.append('file', wavBlob, 'recording.wav');
        formData.append('word', selectedWord);
        // Pass the continuous noise floor for better trimming
        formData.append('noiseFloor', measuredNoiseFloor);

        const res = await fetch('/api/process_audio', {
            method: 'POST',
            body: formData
        });

        if (!res.ok) throw new Error('Processing Failed');

        const processedBlob = await res.blob();

        // Decode for visualization
        const ab = await processedBlob.arrayBuffer();
        userBuf = await ctx.decodeAudioData(ab);

        // Update UI
        say('READY');
        UI.submitBtn.disabled = false;
        UI.playUserBtn.disabled = false;
        UI.recStartBtn.disabled = false;

        renderComparison();

    } catch (e) {
        console.error(e);
        say('ERROR');
        UI.recStartBtn.disabled = false;
    } finally {
        isAppBusy = false;
        hideProcessing();
    }
}

if (UI.recStartBtn) UI.recStartBtn.onclick = async () => {
    if (!selectedWord) return;
    logEvent('record_start', { word: selectedWord });
    const ctx = await getAC();
    await loadRecorderWorklet(ctx);

    isAppBusy = true;
    UI.recStartBtn.disabled = true;
    UI.recStopBtn.style.opacity = '1';
    UI.recStopBtn.style.pointerEvents = 'auto';
    if (UI.testTypeInput) UI.testTypeInput.disabled = true;

    // Clear previous
    if (userWS) { try { userWS.destroy(); } catch (e) { } userWS = null; }

    say('RECORDING...');

    try {
        let stream = microphoneStream;
        if (!stream) {
            const constraints = {
                audio: {
                    deviceId: AudioState.selectedDeviceId !== 'default' ? { exact: AudioState.selectedDeviceId } : undefined,
                    ...AudioState.constraints[AudioState.mode]
                }
            };
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            microphoneStream = stream;
        }

        // Setup Worklet Node
        const source = ctx.createMediaStreamSource(stream);
        recordingSource = source; // Track globally for cleanup
        recorderNode = new AudioWorkletNode(ctx, 'recorder-processor');

        rawChunks = [];
        recorderNode.port.onmessage = (e) => {
            if (e.data) rawChunks.push(e.data);
        };

        // Connect Source -> Recorder
        source.connect(recorderNode);

        const startTime = Date.now();
        let silenceStart = null;

        // Auto-Stop Monitor (Reuse Analyzer)
        const analyzer = ctx.createAnalyser();
        source.connect(analyzer);

        const dataArr = new Float32Array(analyzer.fftSize);
        autoCheckInterval = setInterval(() => {
            const elapsed = Date.now() - startTime;
            if (elapsed > Config.MAX_RECORDING_MS) { stopRecording(); return; }

            analyzer.getFloatTimeDomainData(dataArr);
            let peak = 0;
            for (let i = 0; i < dataArr.length; i++) peak = Math.max(peak, Math.abs(dataArr[i]));

            if (peak < Math.max(0.012, measuredNoiseFloor * 2.5) && elapsed > 1000) {
                if (!silenceStart) silenceStart = Date.now();
                if (Date.now() - silenceStart > Config.AUTO_STOP_SILENCE_MS) stopRecording();
            } else silenceStart = null;
        }, 100);

    } catch (e) {
        console.error(e);
        isAppBusy = false;
        UI.recStartBtn.disabled = false;
    }
};

if (UI.recStopBtn) UI.recStopBtn.onclick = () => { if (recorderNode) stopRecording(); };
if (UI.playUserBtn) UI.playUserBtn.onclick = async () => {
    if (!userBuf) return;
    logEvent('play_user', { word: selectedWord });
    if (isAppBusy) return; // Respect recording/uploading busy state

    // Stop any existing playback
    if (sampleWS) sampleWS.stop();
    if (userWS) userWS.stop();

    if (!userWS) renderComparison();

    if (userWS) {
        userWS.play();
        // strictly no isAppBusy manipulation here
    }
};

if (UI.submitBtn) UI.submitBtn.onclick = async (e) => {
    e.preventDefault();
    if (!lastRecordingBlob) return;
    if (UI.submitMsg) UI.submitMsg.textContent = 'SAVING...';
    UI.submitBtn.disabled = true;
    if (UI.testTypeInput) UI.testTypeInput.disabled = true;
    const fd = new FormData();
    fd.append('file', lastRecordingBlob, 'attempt.wav');
    fd.append('word', selectedWord);
    fd.append('noiseFloor', measuredNoiseFloor);
    fd.append('testType', UI.testTypeInput?.value || 'pre');
    try {
        const res = await fetch('/upload', { method: 'POST', body: fd });
        const data = await res.json();

        if (res.ok) {
            let msg = '✅ SAVED';
            if (data.analysis && data.analysis.distance_bark !== null) {
                const d = data.analysis.distance_bark;
                let colorClass = 'text-slate-600'; // Default
                let verdict = 'OK';

                // Traffic Light Logic
                if (d < 1.5) {
                    colorClass = 'score-success';
                    verdict = 'Excellent!';
                } else if (d < 3.0) {
                    colorClass = 'score-warning';
                    verdict = 'Good';
                } else {
                    colorClass = 'score-danger';
                    verdict = 'Try Again';
                }

                // Render HTML inside message box (safely)
                let recHtml = '';
                if (data.analysis.recommendation) {
                    recHtml = `<div class="text-sm font-medium text-slate-500 normal-case tracking-normal mt-0.5">💡 ${data.analysis.recommendation}</div>`;
                }
                UI.submitMsg.innerHTML = `<div>✅ <span class="${colorClass}">Score: ${d} Bark (${verdict})</span></div>${recHtml}`;
            } else {
                if (UI.submitMsg) UI.submitMsg.textContent = msg;
            }

            await fetchUserProgress();
            if (UI.testTypeInput) UI.testTypeInput.disabled = false;

            await fetchUserProgress();
            if (UI.testTypeInput) UI.testTypeInput.disabled = false;

            // Enable Next Word Button
            if (UI.nextWordBtn) {
                UI.nextWordBtn.disabled = false;
                UI.nextWordBtn.classList.add('animate-pulse-subtle'); // Optional visual cue
            }

            // Universal Auto-Advance REMOVED per user request
            // autoProceed(); logic is now on button click
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

// Global unlock for AudioContext
const unlockAudio = () => {
    if (audioContext && audioContext.state === 'suspended') {
        audioContext.resume();
    }
};
const handleFocus = () => {
    if (audioContext && audioContext.state === 'suspended') audioContext.resume();
    if (!monitorStarted) startNoiseMonitor();
};
const handleBlur = () => {
    // Optional: suspend to save battery, but user requested 'stopped if I leave this page'
    // 'leave this page' usually means simple blur or unload. 
    // Suspending context stops processing.
    if (audioContext && audioContext.state === 'running') audioContext.suspend();
};

document.addEventListener('click', unlockAudio);
document.addEventListener('keydown', unlockAudio);
document.addEventListener('touchstart', unlockAudio);

window.addEventListener('focus', handleFocus);
window.addEventListener('blur', handleBlur);

// Init Logging & Manifest
window.onload = () => {
    loadWordList();

    // Logging Setup
    isLoggingEnabled = localStorage.getItem('loggingEnabled') === 'true';
    if (UI.loggingToggle) {
        UI.loggingToggle.checked = isLoggingEnabled;
        UI.loggingToggle.onchange = (e) => {
            isLoggingEnabled = e.target.checked;
            localStorage.setItem('loggingEnabled', isLoggingEnabled);
        };

        // Auto-enable for test_noise
        if (window.CURRENT_USER === 'test_noise') {
            if (!isLoggingEnabled) {
                isLoggingEnabled = true;
                UI.loggingToggle.checked = true;
                localStorage.setItem('loggingEnabled', true);
            }
            logEvent('system_init', { user: 'test_noise', msg: 'Auto-enabled logging' });
        }
    }
};