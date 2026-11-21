#!/usr/bin/env node
// Renderiza una plantilla HTML a una imagen de píxeles exactos para tiendas de apps.
//
// Uso:
//   node compose.mjs <plantilla.html> <salida.png|.jpg> <ancho> <alto> [--rgba]
//
// - Por defecto la salida NO tiene canal alfa (PNG de 24 bits o JPEG), como exige
//   Google Play para el gráfico de funciones, los screenshots y el banner de TV.
// - --rgba guarda un PNG de 32 bits (RGBA) 100 % opaco, como pide el ícono de Play.
//   La plantilla debe tener un fondo opaco a sangre.
//
// Requiere Playwright: npm i -D playwright && npx playwright install chromium

import path from 'node:path';
import fs from 'node:fs';
import zlib from 'node:zlib';
import { createRequire } from 'node:module';

const args = process.argv.slice(2);
const keepAlpha = args.includes('--rgba');
const [html, out, w, h] = args.filter((a) => !a.startsWith('--'));
if (!html || !out || !w || !h) {
  console.error('Uso: node compose.mjs <plantilla.html> <salida.png|.jpg> <ancho> <alto> [--rgba]');
  process.exit(1);
}

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  // Intento con una instalación global de Playwright
  const require = createRequire(import.meta.url);
  const globalRoot = (await import('node:child_process')).execSync('npm root -g').toString().trim();
  ({ chromium } = require(path.join(globalRoot, 'playwright')));
}

const width = parseInt(w, 10);
const height = parseInt(h, 10);
const isJpg = /\.jpe?g$/i.test(out);
fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
await page.goto('file://' + path.resolve(html), { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.evaluate(() => Promise.all([...document.images].map((i) => i.complete ? null : new Promise((r) => { i.onload = i.onerror = r; }))));

if (isJpg) {
  await page.screenshot({ path: out, type: 'jpeg', quality: 95 });
} else {
  const buf = await page.screenshot({ type: 'png' });
  fs.writeFileSync(out, pngConvert(buf, keepAlpha ? 4 : 3));
}
await browser.close();
console.log(`OK ${out} ${width}x${height}${isJpg ? ' JPEG' : keepAlpha ? ' PNG-32 (RGBA)' : ' PNG-24 (RGB)'}`);

// --- Conversión PNG 8 bits RGB <-> RGBA sin dependencias ---
// toChannels = 3: aplana sobre blanco (PNG de 24 bits). toChannels = 4: PNG de 32 bits.
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
  if (bitDepth !== 8 || interlace !== 0) throw new Error('PNG no soportado para convertir');
  const bpp = colorType === 6 ? 4 : colorType === 2 ? 3 : 0;
  if (!bpp) throw new Error('Tipo de color PNG no soportado: ' + colorType);
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
    outRaw[o++] = 0; // filtro None
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
  return Buffer.concat([sig, chunk('IHDR', newIhdr), chunk('IDAT', zlib.deflateSync(outRaw, { level: 9 })), chunk('IEND', Buffer.alloc(0))]);
}

function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4); crc.writeUInt32BE(crc32(td) >>> 0);
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
