# Second Glance

An original dress-up memory game for GameDistribution (HTML5), built
with Defold 1.14.0. Game 8 of the GD factory queue. Landscape 1136x640.
Category: Casual.

## The game

A small styling atelier above a night market at dusk in Kathmandu. The
guest shows you their look ONCE — then the curtain drops and you rebuild
it from memory while three critics who do not get along judge it.

- **Glance, then dress**: the model wears the reference outfit for a few
  seconds (6s on level 1, shrinking to 3s by level 12) inside a style
  card, with the client's name and occasion. Then the curtain drops and
  the outfit is cleared to the plain base model.
- **Wardrobe**: 5 category tabs (TOP, BOTTOM, SHOES, HAT, EXTRA) with 28
  original garments. Tap an item to dress the model; tap the worn item
  again to remove it. The model updates live.
- **Critics**: Gran wants WARM (cozy, or a hat), your Friend wants BOLD
  (red or purple), the Photographer wants MATCHED (3 colors max). Live
  tick/cross marks update as you dress — the demands are clues to the
  look, and every reference satisfies all three (enforced by a
  load-time check in `levels.lua`).
- **Peek**: re-show the reference for 2s, costs 50 points (2 peeks on
  levels 1-4, 1 from level 5). Dressing is locked while peeking.
- **Present**: exact garment 100, same color 40, same style 20 per slot
  (max match 500), +100 per satisfied critic, -50 per peek. Win needs
  the level's match threshold AND its critic requirement, plus the
  mission (match / critics / perfect 5/5 / score).
- **12 levels** with missions and stars (1-3) by score; progress saved.
- **Endless mode**: clients keep coming, glance shrinking 4s to a 3s
  floor; 3 failed clients ends the run, best score saved.
- **Controls**: mouse / touch (tap garments, tabs, buttons), keyboard
  (1-6 pick an item, Q/W/E/R/T switch tabs, K peek, Enter present,
  C clear, P/Esc pause, M mute). Hidden verification aid: press **A**
  to toggle an auto-play bot (dresses the exact reference, then
  presents), and **U** on the title screen to unlock all levels.
- **Audio**: 10 synthesized SFX + 2 music loops, all generated locally
  by `tools/synth_audio.py` (numpy, no AI audio, no downloads).
- **Art**: all sprites drawn in code by `tools/make_art.py` (PIL, no AI
  images, no copied assets). 28 garment sprites on a 200x420 model
  canvas, 3 critic portraits, dusk-indigo atelier background.
- **Animations**: curtain drop, garment pop-in, critic tick/cross
  updates, score popups, confetti on win, tweened panels (gui.animate).

## GameDistribution SDK

- Extension vendored locally under `gamedistribution/` (bob cannot fetch
  the zip through the egress proxy) + `[library] include_dirs =
  gamedistribution` in `game.project`.
- `game.project` has `[gamedistribution] game_id = PLACEHOLDER` — the
  parent fills the real HEX Game ID from the portal Upload tab before
  upload.
- Ads only on user input: pre-roll interstitial on the first Play tap,
  interstitial when the player taps Next on a level-complete screen.
- `SDK_GAME_PAUSE` pauses the game + mutes audio; `SDK_GAME_START` /
  `CONTENT_RESUME_REQUESTED` resumes + unmutes; `SDK_ERROR` / `AD_ERROR`
  / `AD_SDK_CANCELED` also resume if ad-paused (ad-error resume fix,
  copied from Pocket Escape's gd_ads.lua — never ship the old
  pause-only listener). `show_play` resets `user_paused` (stale-pause
  fix). All `gdsdk` calls are guarded (`if gdsdk then`) so the game
  runs fine with no SDK / no network.

## Building (this VM)

```bash
# start the extender reverse proxy (once per VM boot)
setsid nohup python3 ~/workspace/tools/extender-reverse-proxy.py \
  >/tmp/extender-rproxy.log 2>&1 &
cd ~/workspace/defold/projects/second-glance
export JAVA_TOOL_OPTIONS="-Djava.net.preferIPv4Stack=true \
  -Djavax.net.ssl.trustStore=$HOME/workspace/tools/egress-truststore.jks \
  -Djavax.net.ssl.trustStorePassword=changeit"
~/workspace/defold/run-bob.sh --build-server http://127.0.0.1:8080 \
  --platform wasm-web --variant release --archive \
  --bundle-output dist/html5 resolve build bundle
# -> dist/html5/Second Glance/  (~8 MB)
```

HTML5 platform is `wasm-web` (not `js-web`). Engine artifacts are
pre-seeded in `~/workspace/defold/bob-root/wasm_pthread-web/`. The
egress-proxy CA rotates: rebuild `egress-truststore.jks` from
`/run/hatch/egress-tls/ca-bundle.pem` (last cert only) if extender builds
start failing with PKIX errors.

## Verifying

The game reports live state in `document.title`
(`SECONDGLANCE|screen=...|phase=...|level=...|score=...|match=...|
critics=...|peeks=...|time=...|ref=3,2,1,4,5|outfit=3,0,1,0,0|cat=top|
glance=...|presented=...|auto=...|paused=...|clients=...|failed=...|
mission=...`) which the verify script polls. Screenshots land in
`verify/`.

```bash
# serve the bundle on port 8907, then:
node verify/verify.js \
  "file:///home/hatch/workspace/defold/projects/second-glance/verify/redirect.html"
# (redirect.html navigates to http://localhost:8907/index.html)
```

**Headless-verification gotchas (carry over from the other games):**
1. Defold HTML5 input is **polled once per engine frame**; headless
   SwiftShader runs at a few FPS, so quick clicks fall between frames.
   Use **held inputs** (down, hold ~800 ms, up).
2. Input action x/y are in **GUI space (origin bottom-left, y up)**,
   but Playwright clicks in **page space (origin top-left, y down)**.
   A GUI point (x, y) in this 1136x640 game must be clicked at page
   (x, 640 - y).
3. Canvas blankness: decode the screenshot PNG and count distinct
   colors (drawImage returns blank without preserveDrawingBuffer).
4. `bob` without a command only **builds**; the bundle is written only
   when the `bundle` command is passed.
5. Glance/peek timers run in `update`, so slow headless frames stretch
   real time but never skip the phase transitions (dt-based countdowns).

## Files

- `main/` — `game.script` (controller/save/GD/music), `gui.gui_script`
  (all screens, wardrobe, model, critics, input, animations),
  `outfit.lua` (pure match/critic/mission logic), `levels.lua` (garment
  catalog, demand predicates, 12 levels + endless), `audio.lua`
- `art/` — PIL-drawn PNGs + `atlas.atlas`
- `audio/` — synthesized WAVs + `.sound` files + `audio.go`
- `tools/` — `make_art.py`, `synth_audio.py`
- `input/game.input_binding` — mouse + touch + keyboard
- `verify/` — Playwright verification script + screenshots
