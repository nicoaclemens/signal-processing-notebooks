function render({ model, el }) {
  const MIN_ANGLE = 0.75 * Math.PI;
  const MAX_ANGLE = 2.25 * Math.PI;
  const SWEEP = MAX_ANGLE - MIN_ANGLE;

  const container = document.createElement('div');
  container.className = 'knob-container';

  const labelEl = document.createElement('div');
  labelEl.className = 'knob-label';

  const canvas = document.createElement('canvas');

  const readoutEl = document.createElement('div');
  readoutEl.className = 'knob-readout';

  container.appendChild(labelEl);
  container.appendChild(canvas);
  container.appendChild(readoutEl);
  el.appendChild(container);

  const ctx = canvas.getContext('2d');
  let dragging = false;
  let lastY = 0;
  let dragAccum = 0;

  function valueToAngle(val) {
    const mode = model.get('mode');
    if (mode === 'discrete') {
      const n = model.get('options').length;
      if (n <= 1) return MIN_ANGLE;
      return MIN_ANGLE + (val / (n - 1)) * SWEEP;
    }
    const min = model.get('min');
    const max = model.get('max');
    if (max === min) return MIN_ANGLE;
    return MIN_ANGLE + ((val - min) / (max - min)) * SWEEP;
  }

  function draw() {
    const size = model.get('size');
    const dpr = window.devicePixelRatio || 1;
    const pad = 14;
    const canvasW = size + pad * 2;
    const canvasH = size + pad * 2;
    canvas.width = canvasW * dpr;
    canvas.height = canvasH * dpr;
    canvas.style.width = canvasW + 'px';
    canvas.style.height = canvasH + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const cx = canvasW / 2;
    const cy = canvasH / 2;
    const radius = size / 2 - 4;
    const arcR = radius + 7;
    const color = model.get('color');
    const value = model.get('value');
    const mode = model.get('mode');

    ctx.clearRect(0, 0, canvasW, canvasH);

    // Background arc (track)
    ctx.beginPath();
    ctx.arc(cx, cy, arcR, MIN_ANGLE, MAX_ANGLE, false);
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Value arc
    const angle = valueToAngle(value);
    if (angle > MIN_ANGLE + 0.01) {
      ctx.beginPath();
      ctx.arc(cx, cy, arcR, MIN_ANGLE, angle, false);
      ctx.strokeStyle = color;
      ctx.lineWidth = 3;
      ctx.lineCap = 'round';
      ctx.stroke();
    }

    // Discrete tick marks
    if (mode === 'discrete') {
      const opts = model.get('options');
      const n = opts.length;
      for (let i = 0; i < n; i++) {
        const a = n === 1 ? MIN_ANGLE : MIN_ANGLE + (i / (n - 1)) * SWEEP;
        const r1 = arcR + 3;
        const r2 = arcR + 7;
        ctx.beginPath();
        ctx.moveTo(cx + r1 * Math.cos(a), cy + r1 * Math.sin(a));
        ctx.lineTo(cx + r2 * Math.cos(a), cy + r2 * Math.sin(a));
        ctx.strokeStyle = i === Math.round(value) ? color : '#555';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.stroke();
      }
    }

    // Knob body (flat)
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
    ctx.fillStyle = '#2d2d4a';
    ctx.fill();
    ctx.strokeStyle = '#1a1a2e';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // Indicator line
    const indOuter = radius * 0.78;
    const indInner = radius * 0.3;
    ctx.beginPath();
    ctx.moveTo(
      cx + indInner * Math.cos(angle),
      cy + indInner * Math.sin(angle)
    );
    ctx.lineTo(
      cx + indOuter * Math.cos(angle),
      cy + indOuter * Math.sin(angle)
    );
    ctx.strokeStyle = '#eee';
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Label
    labelEl.textContent = model.get('label');

    // Readout
    if (mode === 'discrete') {
      const opts = model.get('options');
      const idx = Math.round(value);
      readoutEl.textContent = opts[idx] || '';
    } else {
      const fmt = model.get('readout_format');
      const unit = model.get('unit');
      let text;
      if (fmt === '.0f') text = Math.round(value).toString();
      else if (fmt === '.1f') text = value.toFixed(1);
      else if (fmt === '.2f') text = value.toFixed(2);
      else if (fmt === '.3f') text = value.toFixed(3);
      else text = value.toFixed(1);
      readoutEl.textContent = unit ? text + ' ' + unit : text;
    }
  }

  function clampValue(v) {
    const mode = model.get('mode');
    if (mode === 'discrete') {
      const n = model.get('options').length;
      return Math.max(0, Math.min(n - 1, Math.round(v)));
    }
    const min = model.get('min');
    const max = model.get('max');
    const step = model.get('step');
    v = Math.max(min, Math.min(max, v));
    if (step > 0) {
      v = min + Math.round((v - min) / step) * step;
      v = Math.max(min, Math.min(max, v));
    }
    return v;
  }

  // --- Interaction: vertical drag ---
  canvas.addEventListener('mousedown', (e) => {
    dragging = true;
    lastY = e.clientY;
    dragAccum = model.get('value');
    canvas.style.cursor = 'ns-resize';
    e.preventDefault();
  });

  function onMouseMove(e) {
    if (!dragging) return;
    const dy = lastY - e.clientY; // up = positive
    lastY = e.clientY;
    const mode = model.get('mode');
    let sensitivity;
    if (mode === 'discrete') {
      const n = model.get('options').length;
      sensitivity = (n - 1) / 150;
    } else {
      sensitivity = (model.get('max') - model.get('min')) / 200;
    }
    if (e.shiftKey) sensitivity *= 0.1;
    dragAccum += dy * sensitivity;
    if (mode === 'discrete') {
      // clamp the float accumulator but don't round yet
      const n = model.get('options').length;
      dragAccum = Math.max(0, Math.min(n - 1, dragAccum));
      // snap to nearest for visual + model, but keep float accum
      const snapped = Math.round(dragAccum);
      if (snapped !== model.get('value')) {
        model.set('value', snapped);
        model.save_changes();
      }
    } else {
      const newVal = clampValue(dragAccum);
      dragAccum = newVal;
      if (newVal !== model.get('value')) {
        model.set('value', newVal);
        model.save_changes();
      }
    }
  }

  function onMouseUp() {
    if (!dragging) return;
    dragging = false;
    canvas.style.cursor = 'grab';
    if (model.get('mode') === 'discrete') {
      const snapped = Math.round(model.get('value'));
      model.set('value', snapped);
      model.save_changes();
    }
  }

  window.addEventListener('mousemove', onMouseMove);
  window.addEventListener('mouseup', onMouseUp);

  // scroll
  canvas.addEventListener(
    'wheel',
    (e) => {
      e.preventDefault();
      const mode = model.get('mode');
      let delta;
      if (mode === 'discrete') {
        delta = e.deltaY > 0 ? -1 : 1;
      } else {
        const step = model.get('step');
        delta = e.deltaY > 0 ? -step * 3 : step * 3;
        if (e.shiftKey) delta *= 0.1;
      }
      const newVal = clampValue(model.get('value') + delta);
      if (newVal !== model.get('value')) {
        model.set('value', newVal);
        model.save_changes();
      }
    },
    { passive: false }
  );

  // reset on dblclick
  canvas.addEventListener('dblclick', () => {
    const def = model.get('default_value');
    model.set('value', clampValue(def));
    model.save_changes();
  });

  model.on('change', draw);
  draw();

  return () => {
    window.removeEventListener('mousemove', onMouseMove);
    window.removeEventListener('mouseup', onMouseUp);
  };
}

export default { render };
