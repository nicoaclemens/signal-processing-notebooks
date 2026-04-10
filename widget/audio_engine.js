const RAMP_TIME = 0.02; // 20 ms click-free ramp
const FFT_SIZE = 2048;
const CANVAS_HEIGHT = 100;

const MULTIPLY_PROCESSOR_CODE = `
class MultiplyProcessor extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const in0 = inputs[0], in1 = inputs[1], out = outputs[0];
    for (let ch = 0; ch < out.length; ch++) {
      const o = out[ch], a = in0[ch], b = in1[ch];
      if (a && b) { for (let i = 0; i < o.length; i++) o[i] = a[i] * b[i]; }
      else { o.fill(0); }
    }
    return true;
  }
}
registerProcessor("multiply-processor", MultiplyProcessor);
`;

// helpers

function rampTo(param, value, ctx) {
  param.cancelScheduledValues(ctx.currentTime);
  param.setValueAtTime(param.value, ctx.currentTime);
  param.linearRampToValueAtTime(value, ctx.currentTime + RAMP_TIME);
}

function setFreq(osc, freq, ctx) {
  rampTo(osc.frequency, Math.max(freq, 0.01), ctx);
}

// graph builder

/**
 * Build an audio graph from an array of component descriptors.
 
 * Returns { ctx, master, analyser, componentMap: Map<id, {oscs, compGain}> }
 */
function buildGraph(ctx, components, volume) {
  const master = ctx.createGain();
  master.gain.value = volume;

  const analyser = ctx.createAnalyser();
  analyser.fftSize = FFT_SIZE;
  analyser.smoothingTimeConstant = 0.85;

  master.connect(analyser);
  analyser.connect(ctx.destination);

  const componentMap = new Map();

  for (const comp of components) {
    const compGain = ctx.createGain();
    compGain.gain.value = comp.enabled ? 1.0 : 0.0;
    compGain.connect(master);

    const oscs = (comp.oscs || []).map((spec) => {
      const osc = ctx.createOscillator();
      osc.type = spec.type || 'sine';
      osc.frequency.value = Math.max(spec.freq || 0.01, 0.01);
      const g = ctx.createGain();
      g.gain.value = spec.gain ?? 1.0;
      osc.connect(g);
      osc.start();
      return { osc, gain: g };
    });

    if (comp.mode === 'multiply' && oscs.length >= 2) {
      const worklet = new AudioWorkletNode(ctx, 'multiply-processor', {
        numberOfInputs: 2,
        numberOfOutputs: 1,
        outputChannelCount: [1],
      });
      oscs[0].gain.connect(worklet, 0, 0);
      oscs[1].gain.connect(worklet, 0, 1);
      worklet.connect(compGain);
      componentMap.set(comp.id, { oscs, compGain, worklet });
    } else {
      for (const o of oscs) o.gain.connect(compGain);
      componentMap.set(comp.id, { oscs, compGain });
    }
  }

  return { ctx, master, analyser, componentMap };
}

function destroyGraph(graph) {
  if (!graph) return;
  for (const comp of graph.componentMap.values()) {
    for (const o of comp.oscs) {
      try {
        o.osc.stop();
      } catch (_) {
        /* already stopped */
      }
    }
  }
  graph.ctx.close();
}

// rt updates

function applyFrequencies(graph, freqDict) {
  for (const [id, freqs] of Object.entries(freqDict)) {
    const comp = graph.componentMap.get(id);
    if (!comp) continue;
    for (let i = 0; i < freqs.length && i < comp.oscs.length; i++) {
      setFreq(comp.oscs[i].osc, freqs[i], graph.ctx);
    }
  }
}

function applyEnables(graph, enablesDict) {
  for (const [id, enabled] of Object.entries(enablesDict)) {
    const comp = graph.componentMap.get(id);
    if (!comp) continue;
    rampTo(comp.compGain.gain, enabled ? 1.0 : 0.0, graph.ctx);
  }
}

function applyWaveforms(graph, waveformsDict, model) {
  const periodicImag = model.get('periodic_coeffs') || [];
  const periodicReal = model.get('periodic_real_coeffs') || [];
  const nCoeffs = Math.max(periodicImag.length, periodicReal.length);
  let periodicWave = null;
  if (nCoeffs > 0) {
    const real = new Float32Array(nCoeffs + 1);
    const imag = new Float32Array(nCoeffs + 1);
    for (let j = 0; j < periodicReal.length; j++) real[j + 1] = periodicReal[j];
    for (let j = 0; j < periodicImag.length; j++) imag[j + 1] = periodicImag[j];
    periodicWave = graph.ctx.createPeriodicWave(real, imag);
  }
  for (const [id, wf] of Object.entries(waveformsDict)) {
    const comp = graph.componentMap.get(id);
    if (!comp) continue;
    const types = Array.isArray(wf) ? wf : comp.oscs.map(() => wf);
    for (let i = 0; i < types.length && i < comp.oscs.length; i++) {
      if (types[i] === 'custom' && periodicWave) {
        comp.oscs[i].osc.setPeriodicWave(periodicWave);
      } else {
        comp.oscs[i].osc.type = types[i] === 'custom' ? 'sine' : types[i];
      }
    }
  }
}

function countActive(model) {
  const components = model.get('components') || [];
  const enables = model.get('enables') || {};
  let n = 0;
  for (const comp of components) {
    const override = enables[comp.id];
    if (override !== undefined ? override : comp.enabled) n++;
  }
  return n;
}

function applyMasterGain(graph, model) {
  const active = countActive(model);
  const vol = model.get('volume');
  const scaled = active > 0 ? vol / Math.sqrt(active) : vol;
  rampTo(graph.master.gain, scaled, graph.ctx);
}

// visualiser
function drawWaveform(analyser, canvas, animRef, playing) {
  const cctx = canvas.getContext('2d');
  const bufLen = analyser ? analyser.frequencyBinCount : 0;
  const data = bufLen > 0 ? new Float32Array(bufLen) : null;

  function draw() {
    if (!playing.value) {
      cctx.fillStyle = '#1a1a2e';
      cctx.fillRect(0, 0, canvas.width, canvas.height);
      cctx.strokeStyle = '#4a4a6a';
      cctx.lineWidth = 1;
      cctx.beginPath();
      cctx.moveTo(0, canvas.height / 2);
      cctx.lineTo(canvas.width, canvas.height / 2);
      cctx.stroke();
      return;
    }

    animRef.value = requestAnimationFrame(draw);
    if (analyser && data) analyser.getFloatTimeDomainData(data);

    cctx.fillStyle = '#1a1a2e';
    cctx.fillRect(0, 0, canvas.width, canvas.height);
    cctx.lineWidth = 2;
    cctx.strokeStyle = '#7c6ff7';
    cctx.beginPath();

    if (data) {
      const slice = canvas.width / bufLen;
      let x = 0;
      for (let i = 0; i < bufLen; i++) {
        const y = ((data[i] + 1) / 2) * canvas.height;
        if (i === 0) cctx.moveTo(x, y);
        else cctx.lineTo(x, y);
        x += slice;
      }
    }
    cctx.lineTo(canvas.width, canvas.height / 2);
    cctx.stroke();
  }

  draw();
}

// lifecycle
function render({ model, el }) {
  const container = document.createElement('div');
  container.classList.add('audio-widget');

  const controls = document.createElement('div');
  controls.classList.add('aw-controls');

  const playBtn = document.createElement('button');
  playBtn.classList.add('aw-play-btn');
  playBtn.textContent = '\u25B6 Play';

  const statusEl = document.createElement('span');
  statusEl.classList.add('aw-status');
  statusEl.textContent = 'Stopped';

  controls.appendChild(playBtn);
  controls.appendChild(statusEl);

  const canvas = document.createElement('canvas');
  canvas.classList.add('aw-canvas');
  canvas.width = 600;
  canvas.height = CANVAS_HEIGHT;

  container.appendChild(controls);
  container.appendChild(canvas);
  el.appendChild(container);

  const initCtx = canvas.getContext('2d');
  initCtx.fillStyle = '#1a1a2e';
  initCtx.fillRect(0, 0, canvas.width, canvas.height);
  initCtx.strokeStyle = '#4a4a6a';
  initCtx.lineWidth = 1;
  initCtx.beginPath();
  initCtx.moveTo(0, canvas.height / 2);
  initCtx.lineTo(canvas.width, canvas.height / 2);
  initCtx.stroke();

  let graph = null;
  const animRef = { value: null };
  const playingRef = { value: false };

  async function ensureGraph() {
    if (!graph) {
      const ctx = new AudioContext();
      const blob = new Blob([MULTIPLY_PROCESSOR_CODE], {
        type: 'application/javascript',
      });
      const blobUrl = URL.createObjectURL(blob);
      await ctx.audioWorklet.addModule(blobUrl);
      URL.revokeObjectURL(blobUrl);
      graph = buildGraph(
        ctx,
        model.get('components') || [],
        model.get('volume')
      );
      const freqs = model.get('frequencies');
      if (freqs && Object.keys(freqs).length) applyFrequencies(graph, freqs);
      const enables = model.get('enables');
      if (enables && Object.keys(enables).length) applyEnables(graph, enables);
      const wf = model.get('waveforms');
      if (wf && Object.keys(wf).length) applyWaveforms(graph, wf, model);
      applyMasterGain(graph, model);
    }
    return graph;
  }

  async function startAudio() {
    const g = await ensureGraph();
    await g.ctx.resume();
    playingRef.value = true;
    model.set('playing', true);
    model.save_changes();
    playBtn.textContent = '\u23F9 Stop';
    playBtn.classList.add('aw-playing');
    statusEl.textContent = 'Playing';
    drawWaveform(g.analyser, canvas, animRef, playingRef);
  }

  function stopAudio() {
    if (graph) graph.ctx.suspend();
    playingRef.value = false;
    model.set('playing', false);
    model.save_changes();
    playBtn.textContent = '\u25B6 Play';
    playBtn.classList.remove('aw-playing');
    statusEl.textContent = 'Stopped';
    if (animRef.value) {
      cancelAnimationFrame(animRef.value);
      animRef.value = null;
    }
    drawWaveform(graph ? graph.analyser : null, canvas, animRef, playingRef);
  }

  playBtn.addEventListener('click', () => {
    if (playingRef.value) stopAudio();
    else startAudio();
  });

  // listeners

  function onComponents() {
    if (graph) {
      const wasPlaying = playingRef.value;
      if (wasPlaying) stopAudio();
      destroyGraph(graph);
      graph = null;
      if (wasPlaying) startAudio();
    }
  }

  function onFrequencies() {
    if (graph) applyFrequencies(graph, model.get('frequencies') || {});
  }

  function onEnables() {
    if (graph) {
      applyEnables(graph, model.get('enables') || {});
      applyMasterGain(graph, model);
    }
  }

  function onWaveforms() {
    if (graph) applyWaveforms(graph, model.get('waveforms') || {}, model);
  }

  function onPeriodicCoeffs() {
    if (graph) applyWaveforms(graph, model.get('waveforms') || {}, model);
  }

  function onPeriodicRealCoeffs() {
    if (graph) applyWaveforms(graph, model.get('waveforms') || {}, model);
  }

  function onVolume() {
    if (graph) applyMasterGain(graph, model);
  }

  function onMonoFrequency() {
    if (!graph) return;
    const freq = model.get('mono_frequency');
    if (freq <= 0) return;
    for (const comp of graph.componentMap.values()) {
      for (const o of comp.oscs) {
        setFreq(o.osc, freq, graph.ctx);
      }
    }
  }

  model.on('change:components', onComponents);
  model.on('change:frequencies', onFrequencies);
  model.on('change:enables', onEnables);
  model.on('change:waveforms', onWaveforms);
  model.on('change:periodic_coeffs', onPeriodicCoeffs);
  model.on('change:periodic_real_coeffs', onPeriodicRealCoeffs);
  model.on('change:volume', onVolume);
  model.on('change:mono_frequency', onMonoFrequency);

  return () => {
    if (animRef.value) cancelAnimationFrame(animRef.value);
    destroyGraph(graph);
    graph = null;
    model.off('change:components', onComponents);
    model.off('change:frequencies', onFrequencies);
    model.off('change:enables', onEnables);
    model.off('change:waveforms', onWaveforms);
    model.off('change:periodic_coeffs', onPeriodicCoeffs);
    model.off('change:periodic_real_coeffs', onPeriodicRealCoeffs);
    model.off('change:volume', onVolume);
    model.off('change:mono_frequency', onMonoFrequency);
  };
}

export default { render };
