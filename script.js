// -------------------------------------------------------------
// script.js – Pronunciation Checker (WaveSurfer v7.5)
// Updated 26 Apr 2025 – sample messages now appear under Play Sample
// -------------------------------------------------------------

// ------------  DOM ------------
const wordInput   = document.getElementById('word-input');
const playBtn     = document.getElementById('play-sample');
const recStartBtn = document.getElementById('record-start');
const recStopBtn  = document.getElementById('record-stop');
const playUserBtn  = document.getElementById('play-user');

const sampleWF = document.getElementById('sample-waveform-container');
const userWF   = document.getElementById('user-waveform-container');
const overlapWF= document.getElementById('difference-waveform-container');

const msgBox     = document.getElementById('message-box');      // recording messages
const sampleMsg  = document.getElementById('sample-message');    // sample messages

// ------------  Globals ------------
let ac;
const ensureAC = () => (ac ||= new AudioContext());

let sampleBuf, userBuf;
let sampleWS,  userWS;
let mediaRecorder, chunks = [];

const defaultThreshold  = 0.05;     // 2 % FS for sample
const NOISE_MULTIPLIER = 3.0;    // <-- adjust sensitivity here default value 1.5
let   noiseThreshold    = defaultThreshold;  // user-specific gate

// Auto-stop settings
const SILENCE_HOLD_MS  = 1200;   // how long (ms) mic must stay quiet default 800
const ANALYSE_INTERVAL = 100;   // how often we check the mic (ms)

// -----  Noise correction -----
const noiseBtn   = document.getElementById('measure-noise');
const noiseLabel = document.getElementById('noise-result');

noiseBtn.addEventListener('click', async () => {
  try {
    noiseLabel.textContent = 'Measuring…';
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const ac     = ensureAC();
    const src    = ac.createMediaStreamSource(stream);
    const analyser = ac.createAnalyser();
    analyser.fftSize = 2048;
    src.connect(analyser);

    let rmsSum = 0, frames = 0;
    const end = Date.now() + 1500;          // 1.5 s window
    while (Date.now() < end) {
      const buf = new Float32Array(analyser.fftSize);
      analyser.getFloatTimeDomainData(buf);
      const rms = Math.sqrt(buf.reduce((s, x) => s + x * x, 0) / buf.length);
      rmsSum += rms; frames++;
      await new Promise(r => setTimeout(r, 50)); // ~20 fps
    }
    stream.getTracks().forEach(t => t.stop());

    const ambient = rmsSum / frames;
    noiseThreshold = Math.max(ambient * NOISE_MULTIPLIER, defaultThreshold);
    noiseLabel.textContent = `Threshold set ${(noiseThreshold*100).toFixed(1)} % FS`;
  } catch (err) {
    console.error(err);
    noiseLabel.textContent = 'Noise measure failed';
  }
});


// ------------  Helpers ------------
const say        = txt => (msgBox.textContent    = txt);
const sampleSay  = txt => (sampleMsg.textContent = txt);

async function fetchBuffer(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return ensureAC().decodeAudioData(await res.arrayBuffer());
}

function trimSilence(buf, threshold) {
  const d  = buf.getChannelData(0);
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
  if (ws.setBuffer) ws.setBuffer(buf);           // v7 helper
  else if (ws.loadDecodedBuffer) ws.loadDecodedBuffer(buf); // v6 helper
  else ws.load(bufferToUrl(buf));                // v8 nightly fallback
  return ws;
}

// encode AudioBuffer to WAV for v8 fallback
function bufferToUrl(buffer) {
  const n  = buffer.length;
  const sr = buffer.sampleRate;
  const pcm= buffer.getChannelData(0);
  const ab = new ArrayBuffer(44 + n * 2);
  const v  = new DataView(ab);
  const w  = (o, s) => [...s].forEach((c,i)=>v.setUint8(o+i,c.charCodeAt(0)));
  w(0,'RIFF'); v.setUint32(4,36+n*2,true);
  w(8,'WAVE'); w(12,'fmt '); v.setUint32(16,16,true);
  v.setUint16(20,1,true); v.setUint16(22,1,true);
  v.setUint32(24,sr,true); v.setUint32(28,sr*2,true);
  v.setUint16(32,2,true); v.setUint16(34,16,true);
  w(36,'data'); v.setUint32(40,n*2,true);
  for(let i=0;i<n;i++) v.setInt16(44+i*2, Math.max(-1,Math.min(1,pcm[i]))*0x7FFF, true);
  return URL.createObjectURL(new Blob([ab],{type:'audio/wav'}));
}

function renderOverlap() {
  overlapWF.innerHTML = '';
  const sDiv = document.createElement('div');
  const uDiv = document.createElement('div');
  Object.assign(sDiv.style,{position:'absolute',inset:0});
  Object.assign(uDiv.style,{position:'absolute',inset:0});
  overlapWF.style.position='relative';
  overlapWF.append(sDiv,uDiv);
  const sWS = makeWS(sDiv,'rgba(70,130,180,.6)');
  const uWS = makeWS(uDiv,'rgba(34,139,34,.6)');
  (sWS.setBuffer ?? sWS.loadDecodedBuffer ?? (b=>sWS.load(bufferToUrl(b))))(sampleBuf);
  (uWS.setBuffer ?? uWS.loadDecodedBuffer ?? (b=>uWS.load(bufferToUrl(b))))(userBuf);
}

// ------------  Play sample ------------
playBtn.addEventListener('click', async () => {
  const word = wordInput.value.trim();
  if (!word) {
    sampleSay('Type a word first.');
    return;
  }
  sampleSay('Loading sample…');
  try {
    sampleBuf = await fetchBuffer(`audio/${word}.mp3`);
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

// ------------  Record user ------------
function toggle(rec) {
  recStartBtn.disabled = rec;
  recStopBtn.disabled  = !rec;
}

recStartBtn.addEventListener('click', async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      clearInterval(autoCheck);               // <-- NEW
      userBuf = await ensureAC().decodeAudioData(await new Blob(chunks).arrayBuffer());
      userBuf = trimSilence(userBuf, noiseThreshold);
      userWS  = renderWS(userBuf, userWF, userWS, 'forestgreen');
      if (sampleBuf) renderOverlap();
      playUserBtn.disabled = false;          // recording ready to play
      stream.getTracks().forEach(t=>t.stop());
      toggle(false);
      say('Done.');
    };
    mediaRecorder.start();
    playUserBtn.disabled = true;
    // ---- auto-stop logic ---------------------------------------
    const micSrc   = ensureAC().createMediaStreamSource(stream);
    const analyser = ensureAC().createAnalyser();
    analyser.fftSize = 2048;
    micSrc.connect(analyser);

    let silenceStart = null;
    const autoCheck  = setInterval(() => {
      const buf = new Float32Array(analyser.fftSize);
      analyser.getFloatTimeDomainData(buf);
      const rms = Math.sqrt(buf.reduce((s,x)=>s+x*x,0)/buf.length);

      if (rms < noiseThreshold) {
        silenceStart ??= Date.now();                  // first quiet frame
        if (Date.now() - silenceStart > SILENCE_HOLD_MS &&
            mediaRecorder.state === 'recording') {
          say('Auto-stop: silence detected');
          mediaRecorder.stop();                       // triggers onstop
        }
      } else {
        silenceStart = null;                          // reset on speech
      }
    }, ANALYSE_INTERVAL);
    // -------------------------------------------------------------

    toggle(true);
    say('Recording…');
  } catch (e) {
    console.error(e);
    say('Mic error.');
  }
});

recStopBtn.addEventListener('click', () => {
  if (mediaRecorder?.state==='recording') mediaRecorder.stop();
});

window.addEventListener('load', ensureAC);
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
