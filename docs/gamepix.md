# Second Glance — GamePix conversion notes

GamePix build: `dist/html5/Second Glance/` (8.6 MB) + upload pack
`dist/gpx-upload/` (zip, cover 1360x850, icon 256x256,
description/instructions/tags). GamePix SDK v3, manual lifecycle.
Second Glance has NO GameDistribution portal entry yet (game_id was
PLACEHOLDER; the GD pack in `dist/gd-upload/` is ready but unlisted),
so the GD lane for this game is just the local pack — untouched here.

## What the conversion changed (GamePix SDK v3, no native extension)

- New `main/gpx.lua`: pure-Lua bridge over `html5.run` (`pcall(require,
  "html5")`, so the game runs fully without the SDK). `loaded()` (once:
  `lifecycle.loading(100)` + `loaded()`, sets
  `window.__gpx_loaded_called=1`), `game_start()` (once, sets
  `window.__gpx_started=1`), `show_interstitial()` (fire-and-forget
  `GamePix.ads.interstitial()`), `happy_moment(kind)` / `sad_moment(kind)`,
  `poll_paused()` (true when `__gpx_paused` or `__gpx_hidden` is 1),
  `sdk_present()`. All calls guarded. Copied unchanged from One Pan.
- `main/game.script`: GD listener block removed; NEW `update()` added
  (Second Glance had none) polling `gpx.poll_paused()` once per frame
  and applying ad-pause transitions (mute + `ad_pause` / `ad_resume` GUI
  messages); `show_ad` calls `gpx.show_interstitial()`; `gpx.loaded()`
  in `show_title` (once-only guard inside); `gpx.game_start()` in
  `start_level`; `happy_moment("level_complete")` on `ui_level_won`;
  `sad_moment("game_over")` (endless) / `"level_failed"` (normal) on
  `ui_level_lost`.
- `main/gui.gui_script`: `gd_pause` / `gd_resume` messages renamed to
  `ad_pause` / `ad_resume`.
- `game.project`: `[library] include_dirs = gamedistribution` and
  `[gamedistribution] game_id = PLACEHOLDER` removed.
- `gamedistribution/` folder moved OUT of the project to sibling backup
  `~/workspace/defold/projects/second-glance-gd-extension/` (Defold
  discovers extensions by scanning for `ext.manifest`; removing the
  game.project lines alone does NOT stop bob from using it). The folder
  is tracked in git, so history preserves it too.
- `tools/inject_gamepix.py`: post-processes the built `index.html` —
  inserts `window.GamePixConfig = { lifecycle: 'manual' }` + the SDK
  script (`https://integration.gamepix.com/sdk/v3/gamepix.sdk.js`) +
  glue JS as the first scripts in `<head>`; glue registers
  pause/resume handlers setting `window.__gpx_paused`, tracks
  visibility in `window.__gpx_hidden`, calls `lifecycle.loading(0)`;
  adds `body{touch-action:none}`; verifies SDK present and NO
  GameDistribution residue; idempotent. Run after every rebuild.
- Ads: pre-roll interstitial on first Play tap, interstitial on
  Next Level (level complete). Pause during ads is automatic (SDK calls
  our pause handler before the ad, resume after); the game also mutes
  audio while paused. No rewarded ads (no reward flow in the game).

## Bugs found + fixed (GamePix build only; GD build untouched)

1. **Mission banner stuck behind ads (same latent bug as the other five
   games).** The banner (1.6s timer) was cleared by `clear_overlay`
   only when `not self.paused` — a pre-roll ad firing in the first 1.6s
   would leave it covering the board for the whole level. Fixed in
   `main/gui.gui_script`: the banner node is now tracked as
   `self.banner_node` and deleted directly on timer expiry, paused or
   not (shot 02 confirms no banner). SAME LATENT BUG EXISTS IN THE GD
   BUILD (same code, same pre-roll flow) — the GD build/pack was not
   touched; a GD rebuild + re-upload would be needed to fix it there.
2. **Mission banner covered the model's hat (known GD polish defect).**
   The banner sat at (568, 480), overlapping the model's hat for the
   whole 1.6s of the glance — the look's hat was hidden exactly when
   the player most needed to see it. Moved to (830, 615), 600x50, at
   the bottom of the wardrobe panel: no tabs (end y 582), no grid, no
   buttons, and clear of the model entirely. Shot 02 confirms the full
   dressed model, hat visible, with the banner parked bottom-right.
3. **Critics' demand text unreadable (known GD polish defect).** The
   ink demand texts sat dark-on-dark against the background at the
   bottom of the screen. A light panel strip (350x46 at 210, 22) now
   sits behind all three demand texts; the strip is below the model
   card frame (starts y 85) so it covers no gameplay. Shot 02
   confirms the demands are readable.

## Build (canonical, proven Nov 24, 2026)

From the project dir, with the egress truststore in JAVA_TOOL_OPTIONS:

```
export JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true -Djavax.net.ssl.trustStore=$HOME/workspace/tools/egress-truststore.jks -Djavax.net.ssl.trustStorePassword=changeit"
~/workspace/defold/run-bob.sh --platform wasm-web --variant release --archive --bundle-output dist/html5 resolve build bundle
python3 tools/inject_gamepix.py "dist/html5/Second Glance"
```

No `--build-server` needed (no native extensions in the GamePix build).
The `resolve build bundle` verbs are REQUIRED (without them bob exits 0
and writes no bundle). After any extension/template change, clean
`build/` and the bundle dir first — bob's incremental build reuses the
cached GD template otherwise. Always confirm the bundle timestamp
before injecting.

## Verify — Chrome 157 LNA lesson (Nov 24, 2026)

Headless Chrome 157 blocks navigation to ANY loopback http origin with
`ERR_BLOCKED_BY_LOCAL_NETWORK_ACCESS_CHECKS`. The working route is
**file://**: serve nothing, load
`file:///.../dist/html5/Second Glance/index.html` directly. The Defold
template does NOT auto-boot from file://, so the harness calls
`EngineLoader.load("canvas", "SecondGlance")` manually after load. The
GamePix SDK script loads fine from file:// (https CDN via the 3129
forwarding proxy — start `~/workspace/tools/egress-proxy-forward.py`
first) and localStorage works there, so the SDK checks still run for
real. Harness: `verify/verify_gpx.js` (adapted from One Pan's
verify_gpx.js + Second Glance's GD verify.js), with GamePix checks
added: SDK object + lifecycle/ads/events API, `__gpx_loaded_called`,
`__gpx_started`, pre-roll + level-complete interstitial pause/resume
observation, no GD residue, plus the full gameplay battery (glance
shows a full reference, dress phase, wrong-item pick, peek costs one,
pause/resume, autoplay wins L1, NEXT LEVEL to L2, endless scores,
mute toggle, no errors). Harness lessons kept: 150ms key taps (800ms
holds risk OS key-repeat double-toggling P/A), state-driven waits
(tapKeyExpect, 30s, one retry, never a blind second tap), held mouse
clicks (~800ms, frame-polled).

Verify run 1 (Nov 24, 2026): **28/28 PASS** — all GamePix SDK checks
pass (SDK loads, loaded()/gameStart() from Lua, pre-roll + level-
complete interstitials pause then resume with sawPause=true, no GD
residue, no errors); gameplay: glance shows a full reference
(3,5,2,2,1), timer running (150s), peeks 2, dress phase starts, wrong
bottom item dresses the model (match 20), peek costs one (2->1),
pause/resume, autoplay WINS L1 (score 750, match 500, critics 3/3),
NEXT LEVEL to L2 (ref populated), MENU returns to title, pause/resume
in endless, endless serves a client (clients 1, score 800), mute
toggle. Shots 02/03 confirm all three fixes (no banner, hat visible,
critics' demands readable on the light strip).
See `verify/gpx/results.json`.

## Assets (all from real GamePix-build gameplay, verify/gpx/)

- Cover 1360x850 (`dist/gpx-upload/cover_1360x850.jpg`, 102,994 bytes):
  glance shot 02 (model fully dressed in the L1 reference, green beanie
  + red scarf), crop (80,60,688,440) mirroring the GD thumbnails —
  model cut at the shins, button row and critics excluded, bold
  SECOND GLANCE title at the top (scale 0.7), hat fully visible below
  the title. Visually checked.
- Icon 256x256 (`dist/gpx-upload/icon_256x256.jpg`, 13,614 bytes):
  same shot, tighter crop (140,60,500,420), same bold title.
  Visually checked.
- Built with `~/workspace/defold/projects/tools/make_gpx_assets.py
  second-glance` (scoped run — the tool takes a project argument so one
  game's asset build never re-writes another game's loose files).

## Listing (GamePix dashboard)

- Description: `dist/gpx-upload/description.txt` (347 chars, fits the
  100-500 char field, no em-dashes). Instructions:
  `dist/gpx-upload/instructions.txt` (332 chars, fits the ≤500 char
  How to Play field). Tags: `dist/gpx-upload/tags.txt` — matching,
  logic, thinking, relaxing, arcade (all 5 verified to exist on GD;
  re-check against GamePix's own picker at listing time — Bloom's
  Nov 24 submission proved GamePix does NOT offer "matching",
  "logic" or "relaxing"; Tile Garden's submission proved the picker
  has 155 tags incl. mahjong, match-3, brain, casual; drop anything
  it doesn't offer, never invent replacements).
- Category: Dress-up. Main tag: puzzle (check the picker — Bloom used
  puzzle). Orientation: Landscape (game is 1136x640). Engine:
  HTML5-JS. SDK integration: checked. Desktop + Mobile friendly:
  both checked.
- "Allow Distribution": ON (owner maximises distribution; non-exclusive).
- REVIEW LOCK: once submitted for review the build is LOCKED (no
  withdraw/cancel; Build tab hides Browse) — Bloom's submission showed
  the Review tab DOES have a "Cancel review" button, so it is not
  literally irreversible, but submit only the verified final build.
- Title flag: "Second Glance" is 13 chars — check the title is not
  taken globally on GamePix ("Tile Garden" was taken by another
  developer; it went up as "Tile Garden Mahjong").

## Re-enable GameDistribution (GD lane, do NOT do this for GamePix)

1. Copy `~/workspace/defold/projects/second-glance-gd-extension/gamedistribution/`
   back into the project as `gamedistribution/`.
2. Restore `game.project` from git: `[library] include_dirs =
   gamedistribution` + `[gamedistribution] game_id = PLACEHOLDER`
   (no GD portal entry exists yet — get the real HEX ID from the
   portal Upload tab when one is created).
3. Rebuild with the extender reverse proxy + `--build-server
   http://127.0.0.1:8080` (GD extension needs the extender), verbs
   `resolve build bundle`, then re-zip into `dist/gd-upload/`.
4. The GamePix files (`main/gpx.lua`, injector, verify_gpx.js) stay in
   the repo unused by the GD build; `main/game.script` would need its
   GD listener restored from git (the GamePix edit replaced it).
