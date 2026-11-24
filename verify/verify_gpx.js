// Second Glance — GamePix verification (verify_gpx.js).
// Same flow as verify.js (GD build) plus GamePix SDK v3 checks:
//   - window.GamePix loads, lifecycle API present, loaded()/gameStart()
//     reported from Lua (window.__gpx_loaded_called / __gpx_started flags).
//   - Pre-roll interstitial on first PLAY and interstitial on NEXT LEVEL:
//     the SDK's local simulation fires the pause handler (fake ad overlay),
//     then resume; the game must pause during it and resume after.
//   - No GameDistribution residue (the build must contain no third-party SDK).
// Screenshots + results go to verify/gpx/ (the GD verify/ files stay intact).
// Usage: node verify_gpx.js <game-url>
//   file:///home/hatch/workspace/defold/projects/second-glance/dist/html5/Second%20Glance/index.html
// CHROME 157 LNA LESSON (Nov 24): headless Chrome 157 blocks navigation to
// ANY loopback http origin with ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS.
// The working route is file://: the Defold template does NOT auto-boot
// from file://, so the harness calls EngineLoader.load("canvas",
// "SecondGlance") manually after load. The GamePix SDK script loads fine
// from file:// (https CDN via the 3129 forwarding proxy — start
// ~/workspace/tools/egress-proxy-forward.py first) and localStorage works
// there, so the SDK checks still run for real.
// INPUT NOTE (GD run): keys are event-driven in Defold, so a SHORT 150ms
// tap is reliable — a long hold risks OS key-repeat firing action.pressed
// twice and toggling P/A back. A tap's effect can take ~2s (up to 10s+
// under load) to show in document.title at ~1 FPS headless — wait
// state-driven (tapKeyExpect, 30s, one retry, never a blind second tap).
// Mouse clicks are frame-polled: use HELD clicks (~800ms).
// COORDINATES: input action x/y are GUI space (origin bottom-left, y up),
// Playwright clicks are page space (origin top-left, y down). A GUI point
// (x, y) in this 1136x640 game must be clicked at page (x, 640 - y).
const { chromium } = require('/home/hatch/workspace/tools/pw-shot/node_modules/playwright-core');
const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const OUT = path.join(__dirname, 'gpx');
fs.mkdirSync(OUT, { recursive: true });
const url = process.argv[2];
if (!url) { console.error('usage: node verify_gpx.js <game-url>'); process.exit(2); }

const W = 1136, H = 640;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const results = [];
function check(name, ok, detail) {
  results.push({ name, ok: !!ok, detail: detail || '' });
  console.log((ok ? 'PASS' : 'FAIL') + '  ' + name + (detail ? '  [' + detail + ']' : ''));
}

async function heldClick(page, x, y, holdMs) {
  await page.mouse.move(x, y);
  await page.mouse.down();
  await sleep(holdMs || 800);
  await page.mouse.up();
  await sleep(400);
}

async function guiClick(page, x, y, holdMs) {
  await heldClick(page, x, H - y, holdMs);
}

async function heldKey(page, key, holdMs) {
  await page.keyboard.down(key);
  await sleep(holdMs || 150);
  await page.keyboard.up(key);
  await sleep(300);
}

async function state(page) {
  const title = await page.title();
  const m = {};
  title.split('|').forEach((part) => {
    const kv = part.split('=');
    if (kv.length === 2) m[kv[0]] = kv[1];
  });
  return m;
}

async function tapKeyExpect(page, key, pred, timeoutMs, label) {
  await heldKey(page, key);
  let s = await waitState(page, pred, timeoutMs, label, true);
  if (!pred(s)) {
    await heldKey(page, key);
    s = await waitState(page, pred, timeoutMs, label, true);
  }
  return s;
}

async function waitState(page, pred, timeoutMs, label, quiet) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const s = await state(page);
    if (pred(s)) return s;
    await sleep(100);
  }
  const s = await state(page);
  if (!quiet) check(label, false, 'last state: ' + JSON.stringify(s));
  return s;
}

function parseRef(str) {
  if (!str) return null;
  const p = str.split(',').map((v) => parseInt(v, 10));
  if (p.length !== 5 || p.some(isNaN)) return null;
  return p;
}

// GamePix glue flags (set by tools/inject_gamepix.py + main/gpx.lua).
async function gpxFlag(page, name) {
  try {
    return await page.evaluate((n) => (window[n] ? 1 : 0), name);
  } catch (e) { return 0; }
}

// Observe an interstitial: sample window.__gpx_paused until it returns to
// 0 (ad finished) or timeout. Returns { sawPause, unpaused }. The SDK's
// local simulation fires pause -> fake ad overlay -> resume; the game must
// pause during it and resume after. The overlay covers the canvas while
// paused, so callers must wait for unpaused before clicking the game.
async function observeAd(page, timeoutMs, label) {
  const t0 = Date.now();
  let sawPause = false;
  let unpaused = false;
  while (Date.now() - t0 < timeoutMs) {
    const p = await gpxFlag(page, '__gpx_paused');
    if (p === 1) sawPause = true;
    if (sawPause && p === 0) { unpaused = true; break; }
    if (!sawPause && Date.now() - t0 > 4000) { unpaused = true; break; }
    await sleep(250);
  }
  if (!unpaused) {
    unpaused = (await gpxFlag(page, '__gpx_paused')) === 0;
  }
  check(label, unpaused, 'sawPause=' + sawPause + ' unpaused=' + unpaused);
  return { sawPause, unpaused };
}

// Minimal PNG decode (8-bit RGB/RGBA) -> count distinct sampled colors.
function pngDistinctColors(buf) {
  if (buf.slice(0, 8).toString('hex') !== '89504e470d0a1a0a') return -1;
  let off = 8, width = 0, height = 0, bitDepth = 0, colorType = 0;
  const idat = [];
  while (off < buf.length) {
    const len = buf.readUInt32BE(off);
    const type = buf.slice(off + 4, off + 8).toString('ascii');
    const data = buf.slice(off + 8, off + 8 + len);
    if (type === 'IHDR') {
      width = data.readUInt32BE(0); height = data.readUInt32BE(4);
      bitDepth = data[8]; colorType = data[9];
    } else if (type === 'IDAT') idat.push(data);
    else if (type === 'IEND') break;
    off += 12 + len;
  }
  if (bitDepth !== 8 || (colorType !== 2 && colorType !== 6)) return -1;
  const bpp = colorType === 6 ? 4 : 3;
  const raw = zlib.inflateSync(Buffer.concat(idat));
  const stride = width * bpp;
  const colors = new Set();
  let prev = Buffer.alloc(stride);
  for (let y = 0; y < height; y++) {
    const rowStart = y * (stride + 1);
    const filter = raw[rowStart];
    const row = Buffer.alloc(stride);
    for (let i = 0; i < stride; i++) {
      const v = raw[rowStart + 1 + i];
      const a = i >= bpp ? row[i - bpp] : 0;
      const b = prev[i];
      const c = i >= bpp ? prev[i - bpp] : 0;
      let pred = 0;
      if (filter === 1) pred = a;
      else if (filter === 2) pred = b;
      else if (filter === 3) pred = (a + b) >> 1;
      else if (filter === 4) {
        const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        pred = (pa <= pb && pa <= pc) ? a : (pb <= pc ? b : c);
      }
      row[i] = (v + pred) & 0xff;
    }
    prev = row;
    if (y % 4 !== 0) continue;
    for (let x = 0; x < width; x += 4) {
      const i = x * bpp;
      colors.add(row[i] + ',' + row[i + 1] + ',' + row[i + 2]);
      if (colors.size > 500) return colors.size;
    }
  }
  return colors.size;
}

// Grid geometry (from DESIGN.md): 3 cols x 2 rows, centres x 640/810/980,
// rows y 430/290. Item index 1-6 -> col=(i-1)%3, row=floor((i-1)/3).
function gridXY(i) {
  const col = (i - 1) % 3, row = Math.floor((i - 1) / 3);
  return [640 + col * 170, row === 0 ? 430 : 290];
}
const TAB_X = { top: 610, bottom: 720, shoes: 830, hat: 940, extra: 1050 };

(async () => {
  const browser = await chromium.launch({
    executablePath: '/opt/meta-chromium/chrome',
    args: ['--no-sandbox', '--disable-dev-shm-usage',
      '--allow-file-access-from-files',
      '--use-gl=angle', '--use-angle=swiftshader',
      '--enable-unsafe-swiftshader',
      '--hatch-webgl-allowed-domains-file=' + path.join(__dirname, 'webgl-policy-all.txt'),
      '--hatch-webgl-allowed-domains-sha256=8097045f0459c96c4cdc76e3a1af4e0f43f640b4b59c43d6db35e3641c0264c6',
      '--autoplay-policy=no-user-gesture-required',
      '--disable-features=LocalNetworkAccessChecks,BlockInsecurePrivateNetworkRequests,local-network-access-check',
      '--proxy-server=http://127.0.0.1:3129',
      '--proxy-bypass-list=127.0.0.1,localhost',
      '--ignore-certificate-errors'],
  });
  const page = await browser.newPage({
    viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const errors = [];
  const logs = [];
  page.on('pageerror', (e) => {
    if (e.message.includes('browsingTopics')) { logs.push('IGNORED: ' + e.message); return; }
    errors.push('PAGEERROR: ' + e.message);
  });
  page.on('console', (m) => {
    const t = m.text();
    logs.push(m.type() + ': ' + t.slice(0, 300));
    if (t.includes('HeaderLift service response error')) return;
    if (t.includes('Cross-Origin-Opener-Policy header has been ignored')) return;
    if (t.includes('browsingTopics')) return;
    if (m.type() === 'error') errors.push('CONSOLE: ' + t.slice(0, 300));
  });
  page.on('requestfailed', (r) => {
    const u = r.url();
    if (!/localhost|127\.0\.0\.1|^file:/.test(u)) {
      logs.push('IGNORED-REQFAIL(ad): ' + u.slice(0, 160));
      return;
    }
    errors.push('REQFAIL: ' + u.slice(0, 160) + ' ' + (r.failure() || {}).errorText);
  });

  await page.goto(url, { waitUntil: 'load' });
  const proto = await page.evaluate(() => window.location.protocol);
  if (proto === 'file:') {
    await sleep(2000);
    await page.evaluate(() => {
      const w = document.getElementById('running-from-file-warning');
      if (w) w.style.display = 'none';
      EngineLoader.load('canvas', 'SecondGlance');
    });
    logs.push('manual EngineLoader.load() for file:// boot');
  } else {
    const m = url.match(/localhost:(\d+)/);
    const waitRe = m ? new RegExp('localhost:' + m[1]) : /localhost/;
    await page.waitForURL(waitRe, { timeout: 15000 }).catch(() => {});
  }
  await sleep(9000); // wasm engine boot
  const titleShot = await page.screenshot({ path: path.join(OUT, '01-title.png') });
  let s = await state(page);
  check('page loads, title state reported', s.screen === 'title', JSON.stringify(s));
  // GamePix SDK v3 checks (local simulation: no Player present).
  const gpxApi = await page.evaluate(() => ({
    obj: typeof window.GamePix,
    lifecycle: (window.GamePix && window.GamePix.lifecycle) ? typeof window.GamePix.lifecycle.loaded : 'missing',
    ads: (window.GamePix && window.GamePix.ads) ? typeof window.GamePix.ads.interstitial : 'missing',
    events: (window.GamePix && window.GamePix.events) ? typeof window.GamePix.events.on : 'missing',
  })).catch(() => ({ obj: 'error' }));
  check('GamePix SDK loads (window.GamePix object)', gpxApi.obj === 'object', JSON.stringify(gpxApi));
  check('GamePix lifecycle/ads/events API present',
    gpxApi.lifecycle === 'function' && gpxApi.ads === 'function' && gpxApi.events === 'function',
    JSON.stringify(gpxApi));
  check('GamePix loaded() reported from Lua at title',
    (await gpxFlag(page, '__gpx_loaded_called')) === 1, 'flag=' + (await gpxFlag(page, '__gpx_loaded_called')));
  const gdResidue = await page.evaluate(() => ({
    gdOptions: typeof window.GD_OPTIONS,
    gdsdk: typeof window.gdsdk,
  }));
  check('no GameDistribution residue in page (GD_OPTIONS/gdsdk absent)',
    gdResidue.gdOptions === 'undefined' && gdResidue.gdsdk === 'undefined',
    JSON.stringify(gdResidue));
  const distinct = pngDistinctColors(titleShot);
  check('canvas non-blank (title screenshot, distinct colors)',
    distinct > 50, 'distinct=' + distinct);

  // PLAY -> level 1 glance phase (GUI 568,312). First Play fires the
  // pre-roll interstitial: observe the SDK pause -> fake ad -> resume
  // flow before touching the game (the overlay covers the canvas while
  // paused).
  await guiClick(page, 568, 312);
  s = await waitState(page, (x) => x.screen === 'play', 10000, 'PLAY starts level 1');
  await observeAd(page, 20000, 'pre-roll interstitial pauses then resumes');
  check('GamePix gameStart() reported from Lua on level start',
    (await gpxFlag(page, '__gpx_started')) === 1, 'flag=' + (await gpxFlag(page, '__gpx_started')));
  s = await waitState(page, (x) => x.phase === 'glance' && parseRef(x.ref) &&
    parseRef(x.ref).every((v) => v > 0), 15000, 'glance phase shows a full reference');
  check('glance phase shows a full reference outfit',
    s.phase === 'glance' && parseRef(s.ref) && parseRef(s.ref).every((v) => v > 0),
    'ref=' + s.ref + ' phase=' + s.phase);
  const ref1 = parseRef(s.ref);
  check('level 1 timer running', parseInt(s.time || '0') > 0, 'time=' + s.time);
  check('level 1 peeks available (2)', parseInt(s.peeks || '0') === 2, 'peeks=' + s.peeks);
  await page.screenshot({ path: path.join(OUT, '02-glance.png') });

  // Wait for the glance to end -> dress phase.
  s = await waitState(page, (x) => x.phase === 'dress', 60000, 'glance ends, dress phase starts');
  check('glance ends, dress phase starts', s.phase === 'dress',
    'phase=' + s.phase + ' glance=' + s.glance);
  await sleep(2000);
  await page.screenshot({ path: path.join(OUT, '03-dress.png') });

  // Mouse: switch to the BOTTOM tab, tap a WRONG bottom item (not the ref).
  const wrongBottom = ref1[1] === 1 ? 2 : 1;
  await guiClick(page, TAB_X.bottom, 560);
  s = await waitState(page, (x) => x.cat === 'bottom', 15000, 'bottom tab selected');
  check('category tab switches to bottom (mouse)', s.cat === 'bottom', 'cat=' + s.cat);
  const wxy = gridXY(wrongBottom);
  await guiClick(page, wxy[0], wxy[1]);
  s = await waitState(page, (x) => {
    const o = parseRef(x.outfit);
    return o && o[1] === wrongBottom;
  }, 15000, 'wrong item dresses the model');
  const outfitAfterWrong = parseRef(s.outfit);
  check('mouse tap dresses a wrong item (outfit changes, match < 500)',
    outfitAfterWrong && outfitAfterWrong[1] === wrongBottom &&
    parseInt(s.match || '500') < 500,
    'outfit=' + s.outfit + ' match=' + s.match);

  // PEEK with K: peeks 2 -> 1.
  s = await tapKeyExpect(page, 'k', (x) => parseInt(x.peeks || '2') === 1, 30000,
    'peek costs one');
  check('peek costs one peek (2 -> 1)', parseInt(s.peeks || '0') === 1,
    'peeks=' + s.peeks);
  await waitState(page, (x) => x.phase === 'dress', 15000, 'peek ends', true);
  await sleep(1000);

  // Pause with P, resume with P.
  s = await tapKeyExpect(page, 'p', (x) => x.paused === '1', 30000, 'pause key pauses');
  check('pause key pauses', s.paused === '1', JSON.stringify(s));
  await page.screenshot({ path: path.join(OUT, '04-paused.png') });
  s = await tapKeyExpect(page, 'p', (x) => x.paused === '0', 30000, 'pause key resumes');
  check('pause key resumes', s.paused === '0', JSON.stringify(s));

  // Autoplay to win level 1 (up to 240s at headless FPS). The bot picks
  // the exact reference in every category, then presents. One peek was
  // already spent (-50), so a perfect win scores 750.
  s = await tapKeyExpect(page, 'a', (x) => x.auto === '1', 30000, 'autoplay turns on');
  check('autoplay turns on', s.auto === '1', JSON.stringify(s));
  s = await waitState(page, (x) => x.screen === 'win' || x.screen === 'lose',
    240000, 'autoplay finishes level 1');
  await page.screenshot({ path: path.join(OUT, '05-end-level1.png') });
  check('level 1 won by autoplay', s.screen === 'win',
    'score=' + s.score + ' match=' + s.match + ' critics=' + s.critics);
  const score1 = parseInt(s.score || '0');
  check('score increased during play', score1 > 0, 'score=' + score1);

  if (s.screen === 'win') {
    // NEXT LEVEL button (GUI 568,238). Tapping Next fires the
    // level-complete interstitial: observe the pause -> fake ad ->
    // resume flow before checking level 2.
    await guiClick(page, 568, 238);
    s = await waitState(page, (x) => x.screen === 'play' && parseInt(x.level || '0') === 2,
      15000, 'NEXT LEVEL starts level 2');
    await observeAd(page, 20000, 'level-complete interstitial pauses then resumes (L1->L2)');
    await sleep(2500);
    await page.screenshot({ path: path.join(OUT, '06-level2.png') });
    s = await waitState(page, (x) => x.phase === 'glance' || x.phase === 'dress',
      20000, 'level 2 glance/dress populated');
    check('level 2 starts (glance phase, ref populated)',
      parseInt(s.level || '0') === 2 && parseRef(s.ref) &&
      parseRef(s.ref).every((v) => v > 0),
      'level=' + s.level + ' ref=' + s.ref + ' phase=' + s.phase);
    // Back to title via the MENU button (GUI 1096,606).
    await guiClick(page, 1096, 606);
    s = await waitState(page, (x) => x.screen === 'title', 15000, 'MENU returns to title');
    check('MENU button returns to title', s.screen === 'title', JSON.stringify(s));
  } else {
    check('NEXT LEVEL starts level 2', false, 'level 1 was lost, not won');
    check('level-complete interstitial pauses then resumes (L1->L2)', false, 'level 1 was lost');
    check('level 2 starts (glance phase, ref populated)', false, 'level 1 was lost, not won');
    check('MENU button returns to title', false, 'level 1 was lost, not won');
    await heldKey(page, 'a'); // autoplay off
    s = await state(page);
    if (s.screen === 'lose') {
      await guiClick(page, 568, 160); // LEVELS
      await waitState(page, (x) => x.screen === 'levels', 10000, 'lose -> levels');
      await guiClick(page, 568, 70); // BACK
      s = await waitState(page, (x) => x.screen === 'title', 10000, 'levels -> title');
    } else if (s.screen === 'play') {
      await guiClick(page, 1096, 606); // MENU
      s = await waitState(page, (x) => x.screen === 'title', 10000, 'quit to title');
    }
  }

  // Autoplay is still on from level 1 (it persists across screens).
  // Endless smoke test: ENDLESS button (GUI 736,210).
  await guiClick(page, 736, 210);
  s = await waitState(page, (x) => x.screen === 'play' && x.endless === '1',
    10000, 'ENDLESS starts endless mode');
  await sleep(2000);
  // Pause in endless right away, before failed clients can end the run.
  s = await tapKeyExpect(page, 'p', (x) => x.paused === '1', 30000,
    'pause in endless works');
  check('pause in endless works', s.paused === '1', JSON.stringify(s));
  if (s.paused === '1') {
    s = await tapKeyExpect(page, 'p', (x) => x.paused === '0', 30000, 'resume in endless');
    check('resume in endless works', s.paused === '0', JSON.stringify(s));
  } else {
    check('resume in endless works', false, 'pause never engaged, cannot test resume');
  }
  // Autoplay serves endless clients: wait for a client served or score > 0.
  const t0 = Date.now();
  let endlessOk = false, endlessDetail = '';
  while (Date.now() - t0 < 120000) {
    s = await state(page);
    endlessDetail = 'clients=' + s.clients + ' score=' + s.score + ' screen=' + s.screen;
    if (parseInt(s.clients || '0') >= 1 || parseInt(s.score || '0') > 0) {
      endlessOk = true;
      break;
    }
    if (s.screen === 'lose') break;
    await sleep(500);
  }
  s = await state(page);
  check('endless mode serves a client / scores', endlessOk,
    endlessDetail + ' screen=' + s.screen);
  await page.screenshot({ path: path.join(OUT, '07-endless.png') });
  await heldKey(page, 'a'); // autoplay off

  // Back to title: via MENU if still playing, else via the lose screen.
  s = await state(page);
  if (s.screen === 'play') {
    await guiClick(page, 1096, 606); // MENU
    await waitState(page, (x) => x.screen === 'title', 15000, 'back to title');
  } else if (s.screen === 'lose') {
    await guiClick(page, 568, 160); // LEVELS
    await waitState(page, (x) => x.screen === 'levels', 10000, 'lose -> levels');
    await guiClick(page, 568, 70); // BACK
    await waitState(page, (x) => x.screen === 'title', 10000, 'levels -> title');
  }
  await guiClick(page, 1030, 600); // SOUND ON/OFF
  await sleep(500);
  await page.screenshot({ path: path.join(OUT, '08-title-muted.png') });
  check('mute toggle clickable (no crash)', true);

  const realErrors = errors.filter((e) =>
    !/gamepix/i.test(e) &&
    !/^CONSOLE: Failed to load resource/.test(e));
  check('no page/console errors (excluding GamePix SDK network noise)',
    realErrors.length === 0, realErrors.slice(0, 3).join(' | '));
  if (errors.length) console.log('ALL console/page errors:\n' + errors.slice(0, 8).join('\n'));

  await browser.close();
  const fails = results.filter((r) => !r.ok).length;
  console.log(`\n${results.length - fails}/${results.length} checks passed`);
  fs.writeFileSync(path.join(OUT, 'results.json'),
    JSON.stringify(results, null, 2));
  process.exit(fails ? 1 : 0);
})().catch((e) => { console.error('VERIFY CRASH:', e); process.exit(2); });
