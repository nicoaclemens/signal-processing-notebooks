const CANVAS_W = 600;
const CANVAS_H = 500;

function render({ model, el }) {
  const container = document.createElement('div');
  container.classList.add('epicycles-widget');

  // controls
  const controls = document.createElement('div');
  controls.classList.add('ep-controls');

  const playBtn = document.createElement('button');
  playBtn.classList.add('ep-btn');
  playBtn.textContent = '\u25B6 Play';

  const resetBtn = document.createElement('button');
  resetBtn.classList.add('ep-btn', 'ep-btn-secondary');
  resetBtn.textContent = '\u21BB Reset';

  const statusEl = document.createElement('span');
  statusEl.classList.add('ep-status');
  statusEl.textContent = 'Stopped';

  controls.appendChild(playBtn);
  controls.appendChild(resetBtn);
  controls.appendChild(statusEl);

  // canvas
  const canvas = document.createElement('canvas');
  canvas.classList.add('ep-canvas');
  canvas.width = CANVAS_W;
  canvas.height = CANVAS_H;

  container.appendChild(controls);
  container.appendChild(canvas);
  el.appendChild(container);

  const ctx = canvas.getContext('2d');
  const CX = CANVAS_W / 2,
    CY = CANVAS_H / 2;
  const SCALE = Math.min(CANVAS_W, CANVAS_H) * 0.38;

  let t = 0;
  const traced = [];
  const MAX_TRACE = 8000;
  let animId = null;
  let playing = false;

  function getCoeffs() {
    const freqs = model.get('coeff_freqs') || [];
    const reals = model.get('coeff_reals') || [];
    const imags = model.get('coeff_imags') || [];
    const n = Math.min(model.get('n_components') || 1, freqs.length);
    const out = [];
    for (let i = 0; i < n; i++) {
      out.push({ freq: freqs[i], re: reals[i] || 0, im: imags[i] || 0 });
    }
    return out;
  }

  function drawFrame() {
    const coeffs = getCoeffs();

    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

    if (coeffs.length === 0) {
      ctx.fillStyle = '#666';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Draw a shape to see epicycles', CX, CY);
      return;
    }

    // draw epicycle chain
    let x = CX,
      y = CY;

    for (let i = 0; i < coeffs.length; i++) {
      const { freq, re, im } = coeffs[i];
      const radius = Math.sqrt(re * re + im * im) * SCALE;
      const phase = Math.atan2(im, re);
      const angle = phase + 2 * Math.PI * freq * t;

      if (radius > 0.5) {
        ctx.strokeStyle = 'rgba(124, 111, 247, 0.2)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(x, y, radius, 0, 2 * Math.PI);
        ctx.stroke();
      }

      const nx = x + radius * Math.cos(angle);
      const ny = y - radius * Math.sin(angle);

      ctx.strokeStyle = 'rgba(124, 111, 247, 0.45)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(nx, ny);
      ctx.stroke();

      x = nx;
      y = ny;
    }

    // trace
    traced.push({ x, y });
    if (traced.length > MAX_TRACE) traced.shift();

    if (traced.length > 1) {
      ctx.strokeStyle = '#7c6ff7';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(traced[0].x, traced[0].y);
      for (let i = 1; i < traced.length; i++)
        ctx.lineTo(traced[i].x, traced[i].y);
      ctx.stroke();
    }

    // tip dot
    ctx.fillStyle = '#ff6b6b';
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, 2 * Math.PI);
    ctx.fill();

    statusEl.textContent = `${coeffs.length} circles \u00b7 ${(t * 100).toFixed(0)}%`;

    const speed = model.get('speed') || 1.0;
    t += speed / 600;
    if (t >= 1) {
      t -= 1;
      traced.length = 0;
    }
  }

  function tick() {
    if (!playing) return;
    drawFrame();
    animId = requestAnimationFrame(tick);
  }

  function start() {
    playing = true;
    model.set('playing', true);
    model.save_changes();
    playBtn.textContent = '\u23F9 Stop';
    playBtn.classList.add('ep-playing');
    tick();
  }

  function stop() {
    playing = false;
    model.set('playing', false);
    model.save_changes();
    if (animId) {
      cancelAnimationFrame(animId);
      animId = null;
    }
    playBtn.textContent = '\u25B6 Play';
    playBtn.classList.remove('ep-playing');
    statusEl.textContent = 'Paused';
  }

  function reset() {
    t = 0;
    traced.length = 0;
    if (!playing) drawFrame();
  }

  playBtn.addEventListener('click', () => (playing ? stop() : start()));
  resetBtn.addEventListener('click', reset);

  function onCoeffsChange() {
    reset();
  }

  model.on('change:coeff_freqs', onCoeffsChange);
  model.on('change:coeff_reals', onCoeffsChange);
  model.on('change:coeff_imags', onCoeffsChange);
  model.on('change:n_components', () => {
    t = 0;
    traced.length = 0;
    if (!playing) drawFrame();
  });

  // initial frame
  drawFrame();

  return () => {
    if (animId) cancelAnimationFrame(animId);
    model.off('change:coeff_freqs', onCoeffsChange);
    model.off('change:coeff_reals', onCoeffsChange);
    model.off('change:coeff_imags', onCoeffsChange);
    model.off('change:n_components');
  };
}

export default { render };
