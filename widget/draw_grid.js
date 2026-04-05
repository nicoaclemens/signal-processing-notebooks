const CANVAS_SIZE = 512;

const PRESETS = {
  circle: (t) => {
    const a = t * 2 * Math.PI;
    return [0.5 + 0.38 * Math.cos(a), 0.5 + 0.38 * Math.sin(a)];
  },
  square: (t) => {
    const m = 0.15,
      M = 0.85,
      s = M - m;
    const d = (t % 1) * 4 * s;
    if (d < s) return [m + d, m];
    if (d < 2 * s) return [M, m + (d - s)];
    if (d < 3 * s) return [M - (d - 2 * s), M];
    return [m, M - (d - 3 * s)];
  },
  star: (t) => {
    const pts = 5,
      outer = 0.4,
      inner = 0.16,
      total = pts * 2;
    const idx = t * total,
      i = Math.floor(idx) % total,
      f = idx - Math.floor(idx);
    const vtx = (k) => {
      const r = k % 2 === 0 ? outer : inner;
      const a = (k / total) * 2 * Math.PI - Math.PI / 2;
      return [0.5 + r * Math.cos(a), 0.5 + r * Math.sin(a)];
    };
    const [x1, y1] = vtx(i),
      [x2, y2] = vtx((i + 1) % total);
    return [x1 + f * (x2 - x1), y1 + f * (y2 - y1)];
  },
  heart: (t) => {
    const a = t * 2 * Math.PI;
    const x = 16 * Math.sin(a) ** 3;
    const y =
      13 * Math.cos(a) -
      5 * Math.cos(2 * a) -
      2 * Math.cos(3 * a) -
      Math.cos(4 * a);
    return [0.5 + x / 42, 0.5 - y / 42];
  },
};

function rasterize(pixels, N, pathFn) {
  pixels.fill(0);
  const samples = N * 8;
  let px = -1,
    py = -1;
  for (let i = 0; i <= samples; i++) {
    const [fx, fy] = pathFn(i / samples);
    const x = Math.round(fx * (N - 1));
    const y = Math.round(fy * (N - 1));
    if (x >= 0 && x < N && y >= 0 && y < N) {
      pixels[y * N + x] = 1;
      if (px >= 0 && px < N && py >= 0 && py < N) {
        const steps = Math.max(Math.abs(x - px), Math.abs(y - py));
        for (let s = 1; s < steps; s++) {
          const ix = Math.round(px + ((x - px) * s) / steps);
          const iy = Math.round(py + ((y - py) * s) / steps);
          if (ix >= 0 && ix < N && iy >= 0 && iy < N) pixels[iy * N + ix] = 1;
        }
      }
    }
    px = x;
    py = y;
  }
}

function render({ model, el }) {
  const gridSize = model.get('grid_size') || 64;
  const cellSize = CANVAS_SIZE / gridSize;

  const container = document.createElement('div');
  container.classList.add('draw-grid-widget');

  // toolbar
  const toolbar = document.createElement('div');
  toolbar.classList.add('dg-toolbar');

  const clearBtn = document.createElement('button');
  clearBtn.classList.add('dg-btn');
  clearBtn.textContent = 'Clear';
  toolbar.appendChild(clearBtn);

  const sep = document.createElement('span');
  sep.classList.add('dg-sep');
  toolbar.appendChild(sep);

  for (const name of Object.keys(PRESETS)) {
    const btn = document.createElement('button');
    btn.classList.add('dg-btn', 'dg-btn-preset');
    btn.textContent = name;
    btn.addEventListener('click', () => {
      rasterize(pixels, gridSize, PRESETS[name]);
      draw();
      sync();
    });
    toolbar.appendChild(btn);
  }

  const label = document.createElement('span');
  label.classList.add('dg-label');
  label.textContent = `${gridSize}\u00d7${gridSize} \u00b7 draw a closed shape`;
  toolbar.appendChild(label);

  // canvas
  const canvas = document.createElement('canvas');
  canvas.classList.add('dg-canvas');
  canvas.width = CANVAS_SIZE;
  canvas.height = CANVAS_SIZE;

  container.appendChild(toolbar);
  container.appendChild(canvas);
  el.appendChild(container);

  const ctx = canvas.getContext('2d');
  const pixels = new Uint8Array(gridSize * gridSize);

  const mp = model.get('pixels') || [];
  for (let i = 0; i < Math.min(mp.length, pixels.length); i++)
    pixels[i] = mp[i];

  function draw() {
    ctx.fillStyle = '#12121f';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    for (let r = 0; r < gridSize; r++) {
      for (let c = 0; c < gridSize; c++) {
        if (pixels[r * gridSize + c]) {
          ctx.fillStyle = '#e0e0e0';
          ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
        }
      }
    }

    if (cellSize >= 4) {
      ctx.strokeStyle = 'rgba(255,255,255,0.06)';
      ctx.lineWidth = 0.5;
      for (let i = 0; i <= gridSize; i++) {
        const p = i * cellSize;
        ctx.beginPath();
        ctx.moveTo(p, 0);
        ctx.lineTo(p, CANVAS_SIZE);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(0, p);
        ctx.lineTo(CANVAS_SIZE, p);
        ctx.stroke();
      }
    }
  }

  function getCell(e) {
    const r = canvas.getBoundingClientRect();
    const x = ((e.clientX - r.left) * CANVAS_SIZE) / r.width;
    const y = ((e.clientY - r.top) * CANVAS_SIZE) / r.height;
    const col = Math.floor(x / cellSize),
      row = Math.floor(y / cellSize);
    return row >= 0 && row < gridSize && col >= 0 && col < gridSize
      ? { row, col }
      : null;
  }

  let drawing = false,
    paintVal = 1;

  canvas.addEventListener('mousedown', (e) => {
    const c = getCell(e);
    if (!c) return;
    drawing = true;
    paintVal = pixels[c.row * gridSize + c.col] ? 0 : 1;
    pixels[c.row * gridSize + c.col] = paintVal;
    draw();
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!drawing) return;
    const c = getCell(e);
    if (!c) return;
    pixels[c.row * gridSize + c.col] = paintVal;
    draw();
  });

  const endDraw = () => {
    if (drawing) {
      drawing = false;
      sync();
    }
  };

  canvas.addEventListener('mouseup', endDraw);
  canvas.addEventListener('mouseleave', endDraw);

  function sync() {
    model.set('pixels', Array.from(pixels));
    model.save_changes();
  }

  clearBtn.addEventListener('click', () => {
    pixels.fill(0);
    draw();
    sync();
  });

  model.on('change:pixels', () => {
    const np = model.get('pixels') || [];
    if (np.length === pixels.length) {
      for (let i = 0; i < pixels.length; i++) pixels[i] = np[i];
      draw();
    }
  });

  draw();
}

export default { render };
