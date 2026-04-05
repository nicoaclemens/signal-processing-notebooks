const N_SAMPLES = 256;
const CANVAS_WIDTH = 600;
const CANVAS_HEIGHT = 200;

const PRESETS = {
  sine: (i, N) => Math.sin((2 * Math.PI * i) / N),
  sawtooth: (i, N) => 2 * (i / N) - 1,
  square: (i, N) => (i < N / 2 ? 1 : -1),
  triangle: (i, N) => {
    const t = i / N;
    return t < 0.5 ? 4 * t - 1 : 3 - 4 * t;
  },
};

// helpers

function yToCanvas(y) {
  return ((1 - y) / 2) * CANVAS_HEIGHT;
}
function canvasToY(cy) {
  return 1 - (2 * cy) / CANVAS_HEIGHT;
}
function xToIdx(cx) {
  return Math.round((cx / CANVAS_WIDTH) * (N_SAMPLES - 1));
}
function idxToX(i) {
  return (i / (N_SAMPLES - 1)) * CANVAS_WIDTH;
}

function clampY(y) {
  return Math.max(-1, Math.min(1, y));
}
function clampIdx(i) {
  return Math.max(0, Math.min(N_SAMPLES - 1, i));
}

function fillSamples(samples, fromIdx, fromY, toIdx, toY) {
  const lo = Math.max(0, Math.min(fromIdx, toIdx));
  const hi = Math.min(N_SAMPLES - 1, Math.max(fromIdx, toIdx));
  if (lo === hi) {
    samples[lo] = clampY(toY);
    return;
  }
  for (let i = lo; i <= hi; i++) {
    const t = (i - fromIdx) / (toIdx - fromIdx);
    samples[i] = clampY(fromY + t * (toY - fromY));
  }
}

function canvasPos(e, canvas) {
  const r = canvas.getBoundingClientRect();
  return {
    x: ((e.clientX - r.left) * CANVAS_WIDTH) / r.width,
    y: ((e.clientY - r.top) * CANVAS_HEIGHT) / r.height,
  };
}

// rendering

function drawGrid(ctx) {
  ctx.fillStyle = '#1a1a2e';
  ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

  ctx.strokeStyle = '#2d2d4a';
  ctx.lineWidth = 1;
  for (const y of [-1, -0.5, 0.5, 1]) {
    const cy = yToCanvas(y);
    ctx.beginPath();
    ctx.moveTo(0, cy);
    ctx.lineTo(CANVAS_WIDTH, cy);
    ctx.stroke();
  }
  ctx.strokeStyle = '#4a4a6a';
  ctx.beginPath();
  ctx.moveTo(0, yToCanvas(0));
  ctx.lineTo(CANVAS_WIDTH, yToCanvas(0));
  ctx.stroke();

  ctx.strokeStyle = '#2d2d4a';
  for (let q = 1; q < 4; q++) {
    const x = (CANVAS_WIDTH * q) / 4;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, CANVAS_HEIGHT);
    ctx.stroke();
  }

  ctx.fillStyle = '#555';
  ctx.font = '10px monospace';
  ctx.textAlign = 'left';
  ctx.fillText('+1', 4, yToCanvas(1) + 12);
  ctx.fillText(' 0', 4, yToCanvas(0) - 4);
  ctx.fillText('\u22121', 4, yToCanvas(-1) - 4);
}

function drawWaveform(ctx, samples) {
  drawGrid(ctx);
  ctx.strokeStyle = '#7c6ff7';
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i < N_SAMPLES; i++) {
    const x = idxToX(i),
      y = yToCanvas(samples[i]);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
}

function render({ model, el }) {
  const container = document.createElement('div');
  container.classList.add('draw-widget');

  // toolbar
  const toolbar = document.createElement('div');
  toolbar.classList.add('dw-toolbar');

  const clearBtn = document.createElement('button');
  clearBtn.classList.add('dw-btn');
  clearBtn.textContent = 'Clear';

  const smoothBtn = document.createElement('button');
  smoothBtn.classList.add('dw-btn', 'dw-btn-secondary');
  smoothBtn.textContent = 'Smooth';

  const sep = document.createElement('span');
  sep.classList.add('dw-sep');

  toolbar.appendChild(clearBtn);
  toolbar.appendChild(smoothBtn);
  toolbar.appendChild(sep);

  for (const name of Object.keys(PRESETS)) {
    const btn = document.createElement('button');
    btn.classList.add('dw-btn', 'dw-btn-preset');
    btn.textContent = name;
    btn.addEventListener('click', () => {
      const gen = PRESETS[name];
      for (let i = 0; i < N_SAMPLES; i++) samples[i] = gen(i, N_SAMPLES);
      drawWaveform(cctx, samples);
      sync();
    });
    toolbar.appendChild(btn);
  }

  const label = document.createElement('span');
  label.classList.add('dw-label');
  label.textContent = 'Draw one period of your waveshape';
  toolbar.appendChild(label);

  // canvas
  const canvas = document.createElement('canvas');
  canvas.classList.add('dw-canvas');
  canvas.width = CANVAS_WIDTH;
  canvas.height = CANVAS_HEIGHT;

  container.appendChild(toolbar);
  container.appendChild(canvas);
  el.appendChild(container);

  const cctx = canvas.getContext('2d');
  const samples = new Float64Array(N_SAMPLES);

  const ms = model.get('samples') || [];
  for (let i = 0; i < Math.min(ms.length, N_SAMPLES); i++) samples[i] = ms[i];

  let drawing = false,
    lastIdx = null,
    lastY = null;

  function sync() {
    model.set('samples', Array.from(samples));
    model.save_changes();
  }

  // events
  canvas.addEventListener('mousedown', (e) => {
    drawing = true;
    const p = canvasPos(e, canvas);
    const idx = clampIdx(xToIdx(p.x));
    const y = clampY(canvasToY(p.y));
    samples[idx] = y;
    lastIdx = idx;
    lastY = y;
    drawWaveform(cctx, samples);
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!drawing) return;
    const p = canvasPos(e, canvas);
    const idx = clampIdx(xToIdx(p.x));
    const y = clampY(canvasToY(p.y));
    fillSamples(samples, lastIdx, lastY, idx, y);
    lastIdx = idx;
    lastY = y;
    drawWaveform(cctx, samples);
  });

  canvas.addEventListener('mouseup', () => {
    if (!drawing) return;
    drawing = false;
    lastIdx = null;
    lastY = null;
    sync();
  });

  canvas.addEventListener('mouseleave', () => {
    if (!drawing) return;
    drawing = false;
    lastIdx = null;
    lastY = null;
    sync();
  });

  clearBtn.addEventListener('click', () => {
    samples.fill(0);
    drawWaveform(cctx, samples);
    sync();
  });

  smoothBtn.addEventListener('click', () => {
    const tmp = new Float64Array(N_SAMPLES);
    const k = 5,
      half = Math.floor(k / 2);
    for (let i = 0; i < N_SAMPLES; i++) {
      let sum = 0;
      for (let j = -half; j <= half; j++)
        sum += samples[(i + j + N_SAMPLES) % N_SAMPLES];
      tmp[i] = sum / k;
    }
    for (let i = 0; i < N_SAMPLES; i++) samples[i] = tmp[i];
    drawWaveform(cctx, samples);
    sync();
  });

  model.on('change:samples', () => {
    const ns = model.get('samples') || [];
    if (ns.length === N_SAMPLES) {
      for (let i = 0; i < N_SAMPLES; i++) samples[i] = ns[i];
      drawWaveform(cctx, samples);
    }
  });

  drawWaveform(cctx, samples);
}

export default { render };
