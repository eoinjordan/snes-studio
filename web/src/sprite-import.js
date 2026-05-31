// Convert an arbitrary image (e.g. AI-generated pixel art from GameTorch, Pixie,
// Layer.ai, aipixelkit) into a SNES Studio sprite: downscale to a square tile
// grid and quantize to <=15 colors + transparent (slot 0), matching SNES 4bpp.

const toHex = (n) => n.toString(16).padStart(2, '0');
const rgbToHex = ([r, g, b]) => `#${toHex(r)}${toHex(g)}${toHex(b)}`;

// Median-cut color quantization. boxes of [r,g,b] -> up to `max` average colors.
function medianCut(pixels, max) {
  if (!pixels.length) return [];
  let boxes = [pixels];
  const range = (box) => {
    const lo = [255, 255, 255], hi = [0, 0, 0];
    for (const p of box) for (let c = 0; c < 3; c++) { if (p[c] < lo[c]) lo[c] = p[c]; if (p[c] > hi[c]) hi[c] = p[c]; }
    let chan = 0, span = -1;
    for (let c = 0; c < 3; c++) { const s = hi[c] - lo[c]; if (s > span) { span = s; chan = c; } }
    return { chan, span };
  };
  while (boxes.length < max) {
    let bi = -1, best = 0, bchan = 0;
    boxes.forEach((box, i) => { if (box.length < 2) return; const r = range(box); if (r.span > best) { best = r.span; bi = i; bchan = r.chan; } });
    if (bi < 0) break;
    const box = boxes[bi].slice().sort((a, b) => a[bchan] - b[bchan]);
    const mid = box.length >> 1;
    boxes.splice(bi, 1, box.slice(0, mid), box.slice(mid));
  }
  return boxes.map((box) => {
    const sum = [0, 0, 0];
    for (const p of box) for (let c = 0; c < 3; c++) sum[c] += p[c];
    return box.length ? sum.map((s) => Math.round(s / box.length)) : [0, 0, 0];
  });
}

const dist2 = (a, b) => { const dr = a[0] - b[0], dg = a[1] - b[1], db = a[2] - b[2]; return dr * dr + dg * dg + db * db; };

// img: HTMLImageElement (loaded). Returns a sprite object (no id/name applied yet).
export function imageToSprite(img, { size = 16, maxColors = 12, transCorners = true } = {}) {
  const cvs = document.createElement('canvas');
  cvs.width = size; cvs.height = size;
  const ctx = cvs.getContext('2d', { willReadFrequently: true });
  ctx.imageSmoothingEnabled = false;
  ctx.clearRect(0, 0, size, size);
  ctx.drawImage(img, 0, 0, size, size);
  const data = ctx.getImageData(0, 0, size, size).data;
  const n = size * size;

  // Determine a "background" colour from the corners if requested (for images
  // that have no real alpha channel, e.g. JPGs on a flat background).
  const corners = [0, size - 1, (size - 1) * size, n - 1];
  const bg = corners.map((i) => [data[i * 4], data[i * 4 + 1], data[i * 4 + 2]]);
  const isBg = (rgb) => transCorners && bg.some((c) => dist2(c, rgb) < 900);

  const opaque = []; // {i, rgb}
  const transparent = new Uint8Array(n);
  for (let i = 0; i < n; i++) {
    const a = data[i * 4 + 3];
    const rgb = [data[i * 4], data[i * 4 + 1], data[i * 4 + 2]];
    if (a < 128 || isBg(rgb)) { transparent[i] = 1; continue; }
    opaque.push(rgb);
  }

  const colors = medianCut(opaque, Math.max(2, Math.min(15, maxColors)));
  const palette = ['#000000', ...colors.map(rgbToHex)]; // slot 0 = transparent

  const pixels = new Array(n).fill(0);
  let oi = 0;
  for (let i = 0; i < n; i++) {
    if (transparent[i]) { pixels[i] = 0; continue; }
    const rgb = [data[i * 4], data[i * 4 + 1], data[i * 4 + 2]];
    let best = 1, bd = Infinity;
    for (let c = 0; c < colors.length; c++) { const d = dist2(colors[c], rgb); if (d < bd) { bd = d; best = c + 1; } }
    pixels[i] = best;
    oi++;
  }

  return { width: size, height: size, palette, frames: [{ id: 'frame_0', name: 'Frame 0', pixels }] };
}

// ---- Scenes: tile-based backgrounds (32x28 grid of 8x8 cells) ----------------
export const SCENE_COLS = 32, SCENE_ROWS = 28;

const luminance = (hex) => { const n = parseInt(hex.replace('#', ''), 16); return 0.3 * ((n >> 16) & 255) + 0.59 * ((n >> 8) & 255) + 0.11 * (n & 255); };

// Convert an image into a scene background: a 32x28 grid of palette indices + the
// quantized palette (index 0 is a real colour — backgrounds are opaque).
export function imageToScenePaint(img, { maxColors = 12 } = {}) {
  const cvs = document.createElement('canvas');
  cvs.width = SCENE_COLS; cvs.height = SCENE_ROWS;
  const ctx = cvs.getContext('2d', { willReadFrequently: true });
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(img, 0, 0, SCENE_COLS, SCENE_ROWS);
  const data = ctx.getImageData(0, 0, SCENE_COLS, SCENE_ROWS).data;
  const n = SCENE_COLS * SCENE_ROWS;
  const pts = [];
  for (let i = 0; i < n; i++) pts.push([data[i * 4], data[i * 4 + 1], data[i * 4 + 2]]);
  const colors = medianCut(pts, Math.max(2, Math.min(16, maxColors)));
  const palette = colors.map(rgbToHex);
  const paint = new Array(n);
  for (let i = 0; i < n; i++) {
    const rgb = [data[i * 4], data[i * 4 + 1], data[i * 4 + 2]];
    let best = 0, bd = Infinity;
    for (let c = 0; c < colors.length; c++) { const d = dist2(colors[c], rgb); if (d < bd) { bd = d; best = c; } }
    paint[i] = best;
  }
  return { paint, palette };
}

// Greedy 2D rectangle merge of "solid" cells into a few clean collision rects.
export function paintToWallCollisions(paint, solidIndices) {
  const set = new Set(solidIndices);
  const cw = 256 / SCENE_COLS, ch = 224 / SCENE_ROWS;
  const used = new Uint8Array(SCENE_COLS * SCENE_ROWS);
  const free = (c, r) => c >= 0 && c < SCENE_COLS && r >= 0 && r < SCENE_ROWS && set.has(paint[r * SCENE_COLS + c]) && !used[r * SCENE_COLS + c];
  const rects = [];
  for (let r = 0; r < SCENE_ROWS; r++) {
    for (let c = 0; c < SCENE_COLS; c++) {
      if (!free(c, r)) continue;
      let w = 1; while (free(c + w, r)) w++;
      let h = 1; while (r + h < SCENE_ROWS && [...Array(w)].every((_, i) => free(c + i, r + h))) h++;
      for (let rr = r; rr < r + h; rr++) for (let cc = c; cc < c + w; cc++) used[rr * SCENE_COLS + cc] = 1;
      rects.push({ x: Math.round(c * cw), y: Math.round(r * ch), w: Math.round(w * cw), h: Math.round(h * ch) });
    }
  }
  return rects;
}

export const darkestIndex = (palette) => palette.reduce((best, hex, i, a) => luminance(hex) < luminance(a[best]) ? i : best, 0);

// ---- Procedural "building block" backgrounds (no image needed) ----------------
const _rnd = (c, r, seed = 0) => { const x = Math.sin((c + 1) * 12.9898 + (r + 1) * 78.233 + seed) * 43758.5453; return x - Math.floor(x); };
const _grid = (fn) => { const a = new Array(SCENE_COLS * SCENE_ROWS); for (let r = 0; r < SCENE_ROWS; r++) for (let c = 0; c < SCENE_COLS; c++) a[r * SCENE_COLS + c] = fn(c, r); return a; };
const _border = (c, r) => c === 0 || r === 0 || c === SCENE_COLS - 1 || r === SCENE_ROWS - 1;

export const SCENE_PRESETS = [
  { name: 'Grassland', build() {
    const palette = ['#5aa83a', '#48902f', '#caa15a', '#2f7fd1', '#e8d24a'];
    const midL = (SCENE_COLS >> 1) - 1, midR = SCENE_COLS >> 1;
    const paint = _grid((c, r) => {
      if (c >= midL && c <= midR) return 2;                       // path
      if (r >= SCENE_ROWS - 6 && c >= SCENE_COLS - 8) return 3;   // pond
      if (_rnd(c, r) > 0.86) return 4;                            // flowers
      return _rnd(c, r, 9) > 0.7 ? 1 : 0;                          // grass tufts
    });
    return { paint, palette, solid: [3] };
  } },
  { name: 'Cave', build() {
    const palette = ['#3a352f', '#23201c', '#5a5048', '#7a6a55', '#100d0b'];
    const paint = _grid((c, r) => {
      if (_border(c, r) || _rnd(c, r, 3) > 0.9) return 2;          // stone walls
      if (_rnd(c, r, 7) > 0.92) return 4;                          // pits
      return _rnd(c, r, 1) > 0.8 ? 1 : 0;                          // rocky floor
    });
    return { paint, palette, solid: [2, 4] };
  } },
  { name: 'Water Edge', build() {
    const palette = ['#2f7fd1', '#3a93e0', '#e6d9a8', '#caa15a'];
    const paint = _grid((c, r) => {
      const wave = Math.round(13 + 2 * Math.sin(c * 0.6));
      if (r < wave) return _rnd(c, r) > 0.8 ? 1 : 0;               // sea
      return _rnd(c, r, 5) > 0.85 ? 3 : 2;                          // sand
    });
    return { paint, palette, solid: [] };
  } },
  { name: 'Dungeon', build() {
    const palette = ['#4b4f63', '#2e3142', '#8a8fae', '#b34a3a', '#1a1c26'];
    const paint = _grid((c, r) => {
      if (_border(c, r)) return 2;                                 // outer wall
      if ((c % 8 === 0 || r % 7 === 0) && _rnd(c, r, 2) > 0.4) return 1; // inner walls
      if (_rnd(c, r, 6) > 0.95) return 3;                          // torches
      return _rnd(c, r, 4) > 0.85 ? 4 : 0;                          // floor
    });
    return { paint, palette, solid: [1, 2] };
  } },
  { name: 'Town', build() {
    const palette = ['#5aa83a', '#caa15a', '#9b6b43', '#b34a3a', '#8a8a8a'];
    const paint = _grid((c, r) => {
      if (c >= 14 && c <= 17) return 1;                            // vertical road
      if (r >= 13 && r <= 15) return 1;                            // horizontal road
      if (r >= 3 && r <= 7 && c >= 4 && c <= 9) return r <= 4 ? 3 : 2;  // house
      if (r >= 3 && r <= 7 && c >= 22 && c <= 27) return r <= 4 ? 3 : 2; // house
      return _rnd(c, r, 8) > 0.85 ? 4 : 0;                          // grass + stones
    });
    return { paint, palette, solid: [2, 3] };
  } },
];

export const AI_PIXEL_TOOLS = [
  { name: 'GameTorch', url: 'https://gametorch.app/image-to-pixel-art' },
  { name: 'Pixie', url: 'https://pixie.haus/' },
  { name: 'Layer.ai', url: 'https://www.layer.ai/tools/layer--image-to-sprite' },
  { name: 'AI Pixel Kit', url: 'https://www.aipixelkit.com/' },
];
