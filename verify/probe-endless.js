// Probe: endless-mode autoplay stall diagnosis for Second Glance.
// Starts ENDLESS with autoplay on, samples state every 3s for 100s.
const { chromium } = require('/home/hatch/workspace/tools/pw-shot/node_modules/playwright-core');
const path = require('path');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const W = 1136, H = 640;
async function state(page) {
  const title = await page.title();
  const m = {};
  title.split('|').forEach((part) => {
    const kv = part.split('=');
    if (kv.length === 2) m[kv[0]] = kv[1];
  });
  return m;
}
async function heldClick(page, x, y, holdMs) {
  await page.mouse.move(x, y);
  await page.mouse.down();
  await sleep(holdMs || 800);
  await page.mouse.up();
  await sleep(400);
}
async function guiClick(page, x, y) { await heldClick(page, x, H - y); }
async function heldKey(page, key) {
  await page.keyboard.down(key);
  await sleep(150);
  await page.keyboard.up(key);
  await sleep(300);
}
(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/meta-chromium/chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage',
      '--allow-file-access-from-files',
      '--use-gl=angle', '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--hatch-webgl-allowed-domains-file=/home/hatch/workspace/defold/projects/second-glance/verify/webgl-policy-all.txt',
      '--hatch-webgl-allowed-domains-sha256=8097045f0459c96c4cdc76e3a1af4e0f43f640b4b59c43d6db35e3641c0264c6',
      '--autoplay-policy=no-user-gesture-required',
      '--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests,local-network-access-check',
      '--no-proxy-server',
      '--ignore-certificate-errors'],
  });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => console.log('PAGEERROR:', e.message.slice(0, 200)));
  page.on('console', (m) => {
    const t = m.text();
    if (m.type() === 'error' && !/Failed to load resource|gamedistribution|GD_|browsingTopics/i.test(t)) {
      console.log('CONSOLE-ERR:', t.slice(0, 300));
    }
    if (/Lua|error|Error/.test(t) && !/Failed to load resource|browsingTopics/i.test(t)) {
      console.log('CONSOLE:', m.type(), t.slice(0, 300));
    }
  });
  await page.goto('file:///home/hatch/workspace/defold/projects/second-glance/verify/redirect.html', { waitUntil: 'load' });
  await sleep(2000);
  await page.evaluate(() => {
    if (location.protocol !== 'file:') return;
    const w = document.getElementById('running-from-file-warning');
    if (w) w.style.display = 'none';
    EngineLoader.load('canvas', 'SecondGlance');
  });
  await sleep(9000);
  let s = await state(page);
  console.log('t=0 title screen:', s.screen);
  await guiClick(page, 736, 210); // ENDLESS
  for (let i = 0; i < 20; i++) {
    s = await state(page);
    if (s.screen === 'play') break;
    await sleep(1000);
  }
  console.log('endless started:', JSON.stringify(s));
  await heldKey(page, 'a'); // autoplay ON
  await sleep(500);
  s = await state(page);
  console.log('autoplay on:', s.auto, 'phase:', s.phase);
  for (let i = 0; i < 33; i++) {
    await sleep(3000);
    s = await state(page);
    console.log(`t=${(i + 1) * 3}s screen=${s.screen} phase=${s.phase} ref=${s.ref} outfit=${s.outfit} match=${s.match} critics=${s.critics} clients=${s.clients} failed=${s.failed} score=${s.score} auto=${s.auto} paused=${s.paused} time=${s.time}`);
    if (s.screen === 'lose' || s.screen === 'win') break;
  }
  await browser.close();
  process.exit(0);
})().catch((e) => { console.error('PROBE CRASH:', e); process.exit(2); });
