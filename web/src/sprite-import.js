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

export const AI_PIXEL_TOOLS = [
  { name: 'GameTorch', url: 'https://gametorch.app/image-to-pixel-art' },
  { name: 'Pixie', url: 'https://pixie.haus/' },
  { name: 'Layer.ai', url: 'https://www.layer.ai/tools/layer--image-to-sprite' },
  { name: 'AI Pixel Kit', url: 'https://www.aipixelkit.com/' },
];
