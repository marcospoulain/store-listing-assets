#!/usr/bin/env node
// Render an HTML template to an image of exact pixel size for a store listing.
//
// Usage:
//   node compose.mjs <template.html> <out.png|.jpg> <width> <height>
//        [--var KEY=VALUE]... [--vars vars.json] [--rgba]
//
// - {{KEY}} in the template is replaced by the value; {{KEY|default}} uses the
//   default when the variable is not given. Values are HTML-escaped; "\n" in a
//   value becomes a line break.
// - File paths in values are resolved from the current directory (run it from
//   the repo root), or can be absolute.
// - Elements with data-if="KEY" are removed when KEY is empty.
// - Output has NO alpha channel by default (24-bit PNG or JPEG), as both stores
//   require for screenshots and banners. --rgba writes a 32-bit, fully opaque
//   PNG, which is what the Google Play icon needs.
//
// Requires Playwright: npm i -D playwright && npx playwright install chromium

import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';
import zlib from 'node:zlib';
import { pathToFileURL } from 'node:url';
import { loadChromium } from './lib/playwright-loader.mjs';

const argv = process.argv.slice(2);
const positional = [];
const vars = {};
let keepAlpha = false;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--rgba') keepAlpha = true;
  else if (a === '--var') {
    const kv = argv[++i] ?? '';
    const eq = kv.indexOf('=');
    if (eq < 1) fail(`--var expects KEY=VALUE, got "${kv}"`);
    vars[kv.slice(0, eq)] = kv.slice(eq + 1);
  } else if (a === '--vars') Object.assign(vars, JSON.parse(fs.readFileSync(argv[++i], 'utf8')));
  else positional.push(a);
}
const [template, out, w, h] = positional;
if (!template || !out || !w || !h) {
  fail('Usage: node compose.mjs <template.html> <out.png|.jpg> <width> <height> [--var KEY=VALUE]... [--vars vars.json] [--rgba]');
}
const width = parseInt(w, 10);
const height = parseInt(h, 10);
const isJpg = /\.jpe?g$/i.test(out);

// ---- fill the template ----
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/\\n/g, '<br>');
const value = (key, dflt) => (vars[key] !== undefined && vars[key] !== '' ? String(vars[key]) : dflt ?? '');
let html = fs.readFileSync(template, 'utf8');
const placeholders = new Set([...html.matchAll(/\{\{([A-Z0-9_]+)|data-if="([A-Z0-9_]+)"/g)].map((m) => m[1] || m[2]));
// url('{{KEY}}') with no value -> none (so the next background layer shows through)
html = html.replace(/url\(\s*['"]?\{\{([A-Z0-9_]+)\}\}['"]?\s*\)/g, (_, k) => {
  const v = value(k);
  if (!v) return 'none';
  if (!/^(data:|https?:|file:)/.test(v) && !fs.existsSync(v)) fail(`${k}: file not found: ${v}`);
  return `url('${encodeURI(v).replace(/'/g, '%27')}')`;
});
html = html.replace(/\{\{([A-Z0-9_]+)(?:\|([^}]*))?\}\}/g, (_, k, d) => esc(value(k, d)));
for (const k of Object.keys(vars)) {
  if (!placeholders.has(k)) console.error(`warning: the template has no {{${k}}} placeholder`);
}
// Relative paths resolve from the current directory, not from the template.
const base = `<base href="${pathToFileURL(process.cwd() + path.sep).href}">`;
html = /<head[^>]*>/i.test(html) ? html.replace(/<head[^>]*>/i, (m) => m + base) : base + html;
const tmp = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'store-assets-')), 'page.html');
fs.writeFileSync(tmp, html);

// ---- render ----
const chromium = await loadChromium();
fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
const missing = [];
page.on('requestfailed', (r) => missing.push(r.url()));
await page.goto(pathToFileURL(tmp).href, { waitUntil: 'load' });
await page.evaluate((v) => {
  document.querySelectorAll('[data-if]').forEach((el) => { if (!v[el.dataset.if]) el.remove(); });
}, vars);
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => Promise.all([...document.images].map((i) => (i.complete ? null : new Promise((r) => { i.onload = i.onerror = r; })))));
const broken = await page.evaluate(() => [...document.images].filter((i) => !i.naturalWidth).map((i) => i.getAttribute('src')));

if (isJpg) {
  await page.screenshot({ path: out, type: 'jpeg', quality: 95 });
} else {
  const buf = await page.screenshot({ type: 'png' });
  fs.writeFileSync(out, pngConvert(buf, keepAlpha ? 4 : 3));
}
await browser.close();
fs.rmSync(path.dirname(tmp), { recursive: true, force: true });
for (const b of new Set([...broken, ...missing.filter((m) => !broken.some((x) => x && decodeURI(m).endsWith(x)))])) console.error(`warning: could not load ${b}`);
console.log(`OK ${out} ${width}x${height}${isJpg ? ' JPEG' : keepAlpha ? ' PNG-32 (RGBA, opaque)' : ' PNG-24 (RGB)'}`);
if (broken.length) process.exit(4);

function fail(msg) {
  console.error(msg);
  process.exit(2);
}

// --- 8-bit PNG RGB <-> RGBA conversion without dependencies ---
// toChannels = 3: flatten on white (24-bit PNG). toChannels = 4: 32-bit PNG.
function pngConvert(buf, toChannels) {
  const sig = buf.subarray(0, 8);
  let off = 8, ihdr, idat = [];
  while (off < buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.toString('ascii', off + 4, off + 8);
    const data = buf.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') ihdr = data;
    else if (type === 'IDAT') idat.push(data);
    off += 12 + len;
  }
  const W = ihdr.readUInt32BE(0), H = ihdr.readUInt32BE(4);
  const bitDepth = ihdr[8], colorType = ihdr[9], interlace = ihdr[12];
  if (bitDepth !== 8 || interlace !== 0) throw new Error('Unsupported PNG for conversion');
  const bpp = colorType === 6 ? 4 : colorType === 2 ? 3 : 0;
  if (!bpp) throw new Error('Unsupported PNG color type: ' + colorType);
  if (bpp === toChannels) return buf;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const stride = W * bpp;
  const prev = Buffer.alloc(stride), cur = Buffer.alloc(stride);
  const outRaw = Buffer.alloc(H * (W * toChannels + 1));
  let p = 0, o = 0;
  for (let y = 0; y < H; y++) {
    const ft = raw[p++];
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? cur[x - bpp] : 0, b = prev[x], c = x >= bpp ? prev[x - bpp] : 0;
      let v = raw[p++];
      switch (ft) {
        case 1: v += a; break;
        case 2: v += b; break;
        case 3: v += (a + b) >> 1; break;
        case 4: { const pa = Math.abs(b - c), pb = Math.abs(a - c), pc = Math.abs(a + b - 2 * c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; break; }
      }
      cur[x] = v & 0xff;
    }
    outRaw[o++] = 0; // filter: None
    for (let x = 0; x < W; x++) {
      const r = cur[x * bpp], g = cur[x * bpp + 1], bl = cur[x * bpp + 2];
      if (toChannels === 3) {
        const al = cur[x * 4 + 3] / 255;
        outRaw[o++] = Math.round(r * al + 255 * (1 - al));
        outRaw[o++] = Math.round(g * al + 255 * (1 - al));
        outRaw[o++] = Math.round(bl * al + 255 * (1 - al));
      } else {
        outRaw[o++] = r; outRaw[o++] = g; outRaw[o++] = bl; outRaw[o++] = 255;
      }
    }
    cur.copy(prev);
  }
  const newIhdr = Buffer.from(ihdr); newIhdr[9] = toChannels === 3 ? 2 : 6;
  return Buffer.concat([sig, chunk('IHDR', newIhdr), chunk('IDAT', zlib.deflateSync(outRaw, { level: 6 })), chunk('IEND', Buffer.alloc(0))]);
}

function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4); crc.writeUInt32BE(zlib.crc32 ? zlib.crc32(td) >>> 0 : crc32(td) >>> 0);
  return Buffer.concat([len, td, crc]);
}

function crc32(b) {
  let c, crc = 0xffffffff;
  for (let n = 0; n < b.length; n++) {
    c = (crc ^ b[n]) & 0xff;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    crc = (crc >>> 8) ^ c;
  }
  return crc ^ 0xffffffff;
}
