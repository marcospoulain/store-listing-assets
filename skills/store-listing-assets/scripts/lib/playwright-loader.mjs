// Finds Playwright wherever it is installed: the user's project (cwd), next to
// this skill, or globally. Exits with install instructions when it is missing.
import path from 'node:path';
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';

export async function loadChromium() {
  const tries = [
    () => import('playwright'),
    () => createRequire(path.join(process.cwd(), 'noop.js'))('playwright'),
    () => createRequire(path.join(process.cwd(), 'noop.js'))('@playwright/test'),
    () => {
      const root = execSync('npm root -g', { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim();
      return createRequire(import.meta.url)(path.join(root, 'playwright'));
    },
  ];
  for (const t of tries) {
    try {
      const mod = await t();
      const chromium = mod.chromium ?? mod.default?.chromium;
      if (chromium) return chromium;
    } catch { /* try the next location */ }
  }
  console.error('Playwright is not installed. In the project run:\n  npm i -D playwright && npx playwright install chromium');
  process.exit(3);
}
