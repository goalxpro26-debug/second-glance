// Capture a clean hero shot for thumbnails: level 1, dress phase,
// model dressed in the exact reference outfit via keyboard, no banner,
// no popup. Usage: node capture_hero.js <game-url>
const { chromium } = require('/home/hatch/workspace/tools/pw-shot/node_modules/playwright-core');
const path = require('path');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const OUT = __dirname;
const url = process.argv[2];
if (!url) { console.error('usage: node capture_hero.js <game-url>'); process.exit(2); }
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
async function waitState(page, pred, timeoutMs) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const s = await state(page);
    if (pred(s)) return s;
    await sleep(200);
  }
  return await state(page);
}
async function heldKey(page, key, holdMs) {
  await page.keyboard.down(key);
  await sleep(holdMs || 250);
  await page.keyboard.up(key);
  await sleep(300);
}
async function keyExpect(page, key, pred, timeoutMs) {
  for (let i = 0; i < 3; i++) {
    await heldKey(page, key);
    const s = await waitState(page, pred, timeoutMs);
    if (pred(s)) return s;
  }
  return await state(page);
}
(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/meta-chromium/chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage',
      '--allow-file-access-from-files',
      '--use-gl=angle', '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--hatch-webgl-allowed-domains-file=' + path.join(OUT, 'webgl-policy-all.txt'),
      '--hatch-webgl-allowed-domains-sha256=8097045f0459c96c4cdc76e3a1af4e0f43f640b4b59c43d6db35e3641c0264c6',
      '--autoplay-policy=no-user-gesture-required',
      '--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests,local-network-access-check',
      '--no-proxy-server',
      '--ignore-certificate-errors'],
  });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: 'load' });
  if (url.startsWith('file://')) {
    await sleep(2000);
    await page.evaluate(() => {
      if (location.protocol !== 'file:') return;
      const w = document.getElementById('running-from-file-warning');
      if (w) w.style.display = 'none';
      EngineLoader.load('canvas', 'SecondGlance');
    });
  }
  await sleep(9000);
  // PLAY (GUI 568,312)
  await page.mouse.move(568, H - 312);
  await page.mouse.down(); await sleep(800); await page.mouse.up(); await sleep(400);
  let s = await waitState(page, (x) => x.screen === 'play', 10000);
  console.log('play:', s.screen, 'phase:', s.phase, 'ref:', s.ref);
  s = await waitState(page, (x) => x.phase === 'dress', 60000);
  console.log('dress phase, ref:', s.ref);
  const ref = s.ref.split(',').map((v) => parseInt(v, 10));
  const cats = ['q', 'w', 'e', 'r', 't']; // top bottom shoes hat extra
  for (let c = 0; c < 5; c++) {
    const want = ref.slice(0, c + 1);
    const pred = (x) => {
      const o = (x.outfit || '').split(',').map((v) => parseInt(v, 10));
      return o.length === 5 && want.every((v, i) => o[i] === v);
    };
    await keyExpect(page, cats[c], (x) => x.cat === ['top', 'bottom', 'shoes', 'hat', 'extra'][c], 15000);
    s = await keyExpect(page, String(ref[c]), pred, 20000);
    console.log('category', c, '-> outfit:', s.outfit, 'match:', s.match);
  }
  await sleep(1500);
  await page.screenshot({ path: path.join(OUT, 'hero-dressed.png') });
  s = await state(page);
  console.log('final:', JSON.stringify(s));
  await browser.close();
  process.exit(0);
})().catch((e) => { console.error('CAPTURE CRASH:', e); process.exit(2); });
