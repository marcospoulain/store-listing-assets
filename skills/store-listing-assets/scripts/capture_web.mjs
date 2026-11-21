#!/usr/bin/env node
// Capture a web page at a store device viewport, at exact pixels.
//
// Usage:
//   node capture_web.mjs <url> <out.png> --device <preset> [--dark] [--locale es-CL]
//        [--wait ms] [--wait-for "css"] [--click "css"]... [--hide "css"]...
//        [--storage state.json] [--landscape] [--full-page]
//
// Presets: iphone-6.9, ipad-13, mac, android-phone, android-tablet,
//          android-tablet-portrait, tv
//
// Requires Playwright: npm i -D playwright && npx playwright install chromium

import fs from 'node:fs';
import path from 'node:path';
import { loadChromium } from './lib/playwright-loader.mjs';

const IOS_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1';
const IPAD_UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15';
const ANDROID_UA = 'Mozilla/5.0 (Linux; Android 15; Pixel 9) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36';
const ANDROID_TABLET_UA = 'Mozilla/5.0 (Linux; Android 15; Pixel Tablet) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36';

const PRESETS = {
  'iphone-6.9': { width: 440, height: 956, scale: 3, mobile: true, ua: IOS_UA },
  'ipad-13': { width: 1032, height: 1376, scale: 2, mobile: true, ua: IPAD_UA },
  'mac': { width: 1440, height: 900, scale: 2, mobile: false },
  'android-phone': { width: 412, height: 915, scale: 3.5, mobile: true, ua: ANDROID_UA },
  'android-tablet': { width: 1280, height: 720, scale: 2, mobile: true, ua: ANDROID_TABLET_UA },
  'android-tablet-portrait': { width: 720, height: 1280, scale: 2, mobile: true, ua: ANDROID_TABLET_UA },
  'tv': { width: 1920, height: 1080, scale: 1, mobile: false },
};

const argv = process.argv.slice(2);
const positional = [];
const opt = { click: [], hide: [], wait: 800 };
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === '--dark') opt.dark = true;
  else if (a === '--landscape') opt.landscape = true;
  else if (a === '--full-page') opt.fullPage = true;
  else if (a === '--device') opt.device = argv[++i];
  else if (a === '--locale') opt.locale = argv[++i];
  else if (a === '--wait') opt.wait = parseInt(argv[++i], 10);
  else if (a === '--wait-for') opt.waitFor = argv[++i];
  else if (a === '--storage') opt.storage = argv[++i];
  else if (a === '--click') opt.click.push(argv[++i]);
  else if (a === '--hide') opt.hide.push(argv[++i]);
  else positional.push(a);
}
const [url, out] = positional;
const preset = PRESETS[opt.device];
if (!url || !out || !preset) {
  console.error('Usage: node capture_web.mjs <url> <out.png> --device <preset> [options]');
  console.error('Presets: ' + Object.keys(PRESETS).join(', '));
  process.exit(2);
}

let { width, height } = preset;
if (opt.landscape) [width, height] = [height, width];

const chromium = await loadChromium();
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width, height },
  deviceScaleFactor: preset.scale,
  isMobile: preset.mobile,
  hasTouch: preset.mobile,
  userAgent: preset.ua,
  colorScheme: opt.dark ? 'dark' : 'light',
  locale: opt.locale,
  storageState: opt.storage,
  reducedMotion: 'reduce',
});
const page = await context.newPage();
try {
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
} catch (e) {
  // Pages with long-polling never reach network idle; carry on once the DOM is there.
  if (!/Timeout/i.test(String(e))) throw e;
}
if (opt.waitFor) await page.waitForSelector(opt.waitFor, { state: 'visible', timeout: 30000 });
for (const sel of opt.click) {
  await page.click(sel, { timeout: 15000 });
  await page.waitForTimeout(400);
}
if (opt.hide.length) {
  await page.addStyleTag({ content: opt.hide.map((s) => `${s}{display:none !important}`).join('\n') });
}
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(opt.wait);

fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
await page.screenshot({ path: out, type: 'png', fullPage: !!opt.fullPage });
await browser.close();
console.log(`${out} ${Math.round(width * preset.scale)}x${Math.round(height * preset.scale)}${opt.fullPage ? ' (full page: height varies)' : ''}`);
