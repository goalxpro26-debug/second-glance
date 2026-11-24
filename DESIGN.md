# Second Glance — Game 8 of the GD factory (Dress-up)

Original Defold 2D dress-up MEMORY game. Landscape 1136x640, Defold 1.14.0,
wasm-web. Project: ~/workspace/defold/projects/second-glance/. Template:
one-pan (same folder layout, vendored gamedistribution/ SDK, game_id =
PLACEHOLDER in game.project).

## Antialgorithm (Step 1, done Nov 23)
- DEFAULT (named, rejected): dress up a princess doll from a closet and
  pick the cutest outfit.
- MOVE: the client shows the look ONCE, then it is hidden; you rebuild it
  from memory while the guest stands at the mirror and will not leave
  until it matches. Three critics who do not get along judge it, each
  with a different demand. The seed's constraint (you cannot see it
  directly) IS the game, so memory, not taste, is the mechanic.
- NAME: "Second Glance" — the name is the mechanic (one glance at the
  reference, then dress from memory). Slug: second-glance.

## Setting / look
A small styling atelier above a night market at dusk in Kathmandu
(Nepal seed; smoke from the momo stall below drifts past the window).
Palette: dusk indigo walls, warm amber stall light, amber/gold is the one
hue in charge. Visual method: ledger / style-card look (spreadsheet-chart
seed) — the reference is a ledger sheet, labels are small type, the outfit
is built in deep layers (underlayer, main, outer, accessory). No AI art:
all sprites PIL-drawn, all audio numpy-synthesized.

## Core loop (one level)
1. GLANCE phase: the model wears the reference outfit for N seconds
   (glance time: 6s L1 shrinking to 3s by L12). A style-card frame + the
   client's name and occasion are shown. Then the curtain drops: the
   outfit is cleared to the plain base model.
2. DRESS phase: wardrobe panel, 5 category tabs (TOP, BOTTOM, SHOES, HAT,
   EXTRA). Each tab shows a grid of items. Tap an item to dress the model
   in it (replaces the current item in that category); tap the worn item
   again to remove it. The model updates live.
3. Critics: 3 critics watch from the side, each with a demand shown as
   small text + a live tick/cross:
   - Gran: wants WARM (any cozy-style item, or a hat/scarf worn)
   - Best Friend: wants BOLD (any red or purple item, or a bold-style item)
   - Photographer: wants MATCHED (no more than 3 distinct colors)
   Demands are CLUES: they describe the reference, so a player who reads
   them remembers more. Every level's reference MUST satisfy all 3
   demands (enforce in code: a load-time check that prints a console
   warning if a level's reference violates any demand; fix the level data).
4. PEEK: limited peeks per level (2 on L1-4, 1 on L5+). PEEK re-shows the
   reference outfit on the model for 2s, costs 50 points each. While a
   peek is showing, dressing is locked.
5. PRESENT: submit the outfit. Scoring per slot: exact garment = 100,
   same color different garment = 40, same style different garment = 20,
   else 0 (max match 500). Each satisfied critic = +100. Peeks cost 50
   each. Total = match + critic bonus - peek penalties.
   WIN: match >= level threshold AND critics satisfied >= level
   requirement (2 on L1-3, 3 on L4+). Otherwise the client leaves: level
   failed. Timer runs out = failed.
6. Stars by total score (per-level thresholds in levels.lua).

## Levels (12 + endless)
Mission types: "match" (reach a match target), "critics" (please all 3
critics), "perfect" (exact 5/5 match), "score" (reach a score target).
Level time limits 150-210s. Difficulty ramps: glance time 6s -> 3s,
peeks 2 -> 1, match threshold 250 -> 400, critic requirement 2 -> 3,
later levels add more similar garments (same color, different style) so
memory must be exact, not just color.
Endless: clients keep coming, glance 4s shrinking 0.2s per client to a
3s floor, 3 failed clients ends the run, best score saved.

## Garment catalog (28 items; id = category + index)
Categories in order: top, bottom, shoes, hat, extra.
- tops (6): 1 Red Tee (red, casual), 2 Blue Blouse (blue, smart),
  3 Green Sweater (green, cozy), 4 Black Jacket (black, smart),
  5 Yellow Shirt (yellow, casual), 6 Purple Hoodie (purple, sporty)
- bottoms (6): 1 Blue Jeans (blue, casual), 2 Red Skirt (red, bold),
  3 Black Trousers (black, smart), 4 Yellow Shorts (yellow, sporty),
  5 Green Skirt (green, casual), 6 Brown Cargo (brown, casual)
- shoes (5): 1 White Sneakers (white, sporty), 2 Brown Boots (brown, cozy),
  3 Red Heels (red, smart), 4 Yellow Sandals (yellow, casual),
  5 Blue Trainers (blue, sporty)
- hats (5): 1 Red Cap (red, sporty), 2 Green Beanie (green, cozy),
  3 Yellow Sunhat (yellow, casual), 4 Purple Beret (purple, smart),
  5 Black Fedora (black, smart)
- extras (6): 1 Red Scarf (red, cozy), 2 Gold Necklace (gold, smart),
  3 Black Glasses (black, smart), 4 Blue Bag (blue, casual),
  5 Brown Belt (brown, casual), 6 Pink Earrings (pink, bold)
Colors used: red, blue, green, yellow, purple, black, white, brown,
gold, pink. Styles: casual, smart, sporty, cozy, bold.
Reference outfit = one garment per category (5 slots). Outfit state is a
table {top=n, bottom=n, shoes=n, hat=n, extra=n} with 0 = empty.

## Layout (GUI coords, 1136x640, origin bottom-left)
- Background image fills the screen.
- Model stage left: model centre x=300, model drawn ~200 wide x 420 tall,
  feet at y=110, head top ~y=530. Model = stacked gui box nodes, all at
  (300, 320), size 200x420: body, bottom, top, shoes, hat, extra (draw
  order: body, bottom, shoes, top, hat, extra).
- Style-card frame around the model during GLANCE (a panel box behind
  the model + "STYLE CARD" label + client name/occasion text above).
- Critics row top-left: 3 critic portraits (72x72) at x=90, 210, 330,
  y=590... NO — top bar is HUD. Put critics bottom-left under the model:
  portraits at y=70, x=90/210/330, demand text under each (small, 0.7
  scale, wrap 110). Tick/cross drawn as colored text (✓/✗) next to each
  portrait — use text nodes, not sprites.
- Wardrobe right: panel x=560..1100. Category tabs row at y=560:
  5 tabs, each 100 wide x 44 tall, centres x=610, 720, 830, 940, 1050.
  Item grid: 3 cols x 2 rows, buttons 160x120, centres x=640, 810, 980,
  rows y=430 and y=290. Each button: garment sprite (96x96) + name label
  below (0.7 scale). Empty 6th cell in 5-item categories stays blank.
- HUD top: score text x=100 y=610; timer x=568 y=610; level + mission
  text x=568 y=580 (small); peeks text near PEEK button.
- Buttons: PEEK (x=640 y=150, 160x56), CLEAR (x=810 y=150, 160x56),
  PRESENT (x=980 y=150, 200x64, gold), MENU (x=1096 y=606, 52x48),
  pause button same as one-pan (top right "II").
- Title screen: big "Second Glance" text, tagline "One look. Then dress
  them from memory.", PLAY / LEVELS / ENDLESS / HOW TO PLAY buttons
  (same positions as one-pan title: PLAY 568,312; LEVELS 400,210;
  ENDLESS 736,210; HOW TO 568,130). Mute button 1030,600.
- Level select: same 4x3 grid as one-pan (x=218+col*240, y=460-row*150),
  lock + stars.
- Win screen: "LOOK NAILED IT!" + stars + score + match breakdown
  (match /500, critics x/3) + NEXT LEVEL (568,238) / REPLAY / LEVELS.
- Lose screen: "THE GUEST LEFT!" + reason + score + TRY AGAIN / LEVELS.
- Pause overlay: same as one-pan (RESUME 568,80 rel panel; RESTART;
  SOUND; QUIT TO TITLE at panel y -180 => GUI 568,140 when panel is
  centred at 320,230... copy one-pan's panel() centred at W/2,H/2 and
  the same button offsets, so QUIT lands at GUI (568,140) like one-pan).
- How-to overlay: explains glance/dress/peek/present/critics + keys.

## Keyboard
- 1-6: pick item 1-6 in the current category (during dress phase).
- Q/W/E/R/T: switch category tab to top/bottom/shoes/hat/extra.
- K: peek. Enter (or Space?): PRESENT. Use KEY_ENTER for present,
  KEY_K peek, KEY_C clear outfit, KEY_P/ESC pause, KEY_A autoplay,
  KEY_U unlock-all (title only), KEY_M mute? one-pan mute is a button
  only; keep button-only mute, plus M key is fine too (add KEY_M ->
  "mute_key").
- Autoplay bot (A): during dress phase, for each category in order,
  switch to it and press the item key for the reference garment
  (reads self.ref), then presses Enter to present. Bot runs on a
  0.9s tick like one-pan's do_autoplay. Bot must NOT act during
  glance/peek phases.

## State reporting (document.title, polled by verify)
Prefix SECONDGLANCE. Fields (pipe-separated k=v):
screen, phase (glance/dress/win/lose...), level, endless (0/1),
score, match (current match vs reference, computed live),
critics (satisfied count 0-3), peeks (left), time (seconds left),
ref (e.g. "3,2,1,4,5" = top,bottom,shoes,hat,extra indices),
outfit (same format, 0=empty), cat (current category name),
glance (seconds left in glance phase, 0 when dress),
presented (0/1), auto (0/1), paused (0/1), clients (endless clients
served), failed (endless failed count), mission (short text, no pipes).
Example: SECONDGLANCE|screen=play|phase=dress|level=1|score=0|match=200|
critics=2|peeks=2|time=140|ref=3,2,1,4,5|outfit=3,0,1,0,0|cat=top|
glance=0|presented=0|auto=0|paused=0

## GD SDK (copy one-pan game.script patterns exactly)
- Pre-roll interstitial on FIRST Play tap only (save.played_once).
- Interstitial on Next after level complete (ui_next).
- SDK_GAME_PAUSE: pause game + mute audio. SDK_GAME_START /
  CONTENT_RESUME_REQUESTED: resume + unmute. SDK_ERROR / AD_ERROR /
  AD_SDK_CANCELED: resume if ad-paused (ad-error resume fix).
- show_play resets self.user_paused (stale-pause-flag fix); show_title
  also resets paused/user_paused. gd_resume sets paused =
  user_paused or false. All gdsdk calls pcall-guarded.
- game.project [gamedistribution] game_id = PLACEHOLDER.

## Hard rules (from the task)
- FORWARD-DECLARE every local function referenced in an earlier closure
  (One Pan shipped a game-breaking bug: a slot-tap closure referenced
  serve_slot before its local declaration; real clicks did nothing).
- No AI images/text/audio. English only. No external links, no
  watermarks, no other sites' logos. Fully responsive scaling, no black
  screen over 5s, no dead buttons.
- Sounds live on the "/audio" game object as components in
  main/main.collection (top-level instance, NOT a nested .go component —
  Pocket Escape's nested-.go boot abort). audio/audio.go must list every
  .sound component used.
- 12 levels + endless, missions, stars, SFX + music, animations
  (curtain drop, garment pop-in, critic reactions, confetti on win,
  tweened panels, score popups).

## Files to write
- main/levels.lua — garment catalog, demand predicates, 12 level defs
  (each: ref outfit, glance time, peeks, time limit, mission, star
  thresholds, critic requirement), ENDLESS def, helpers.
- main/outfit.lua — pure logic: match scoring, critic checks,
  outfit state. (Replaces grill.lua's role.)
- main/game.script — controller: save, level flow, GD SDK, music
  (adapt one-pan's; SAVE_FILE = "second_glance").
- main/gui.gui_script — all screens + wardrobe + model + input +
  animations + state reporting (adapt one-pan's helpers: track/new_box/
  new_img/new_text/pick/button/panel/popup/burst/confetti).
- main/audio.lua — copy one-pan's.
- main/main.collection — copy one-pan's (audio instance + game + gui).
- main/gui.gui — copy one-pan's (atlas texture, default font).
- input/game.input_binding — mouse + touch + keys: 1-6 item, Q/W/E/R/T
  category, K peek, ENTER present, C clear, P/ESC pause, A autoplay,
  U unlock, M mute.
- game.project — title "Second Glance", version 1.0.0, game_id PLACEHOLDER,
  same display/input/library/html5 sections as one-pan.
- README.md — game description, build + verify instructions (adapt
  one-pan's, including extender reverse-proxy + truststore flow).
- docs/gamedistribution.md + docs/gd-listing.md — written later by the
  coordinator (NOT this build step).

## Art contract (for the art subagent)
See DESIGN.md "Art contract" — sprites listed in art/atlas.atlas (to be
written by the art agent). Garment sprites: 200x420 canvases aligned to
the body sprite regions (see art section below).

### Art: body regions (200x420 canvas, model centred)
- Head: y 330-410 (face ~y 350-400, hair top ~410). Hat region: y 380-430.
- Torso: y 190-340, x 55-145. Top garments cover torso (and arms to x 30-170).
- Legs: y 40-200, x 70-130. Bottom garments cover y 60-210.
- Feet: y 10-50. Shoes cover y 5-55.
- Extra: scarf y 300-350 around neck; necklace y 300-330; glasses on
  face y 360-385; bag at side x 140-185, y 150-260; belt y 195-215;
  earrings at ears y 360-375.
All garment PNGs are full 200x420 with transparency outside the garment.
Body sprite: neutral skin-tone figure, simple face, dark hair, plain
grey underclothes (so an empty slot reads as undressed, not naked —
  draw a plain light-grey tee + grey trousers as the BASE body, and
  garments layer OVER them).

## Audio contract (for the audio subagent)
SFX (numpy-synthesized, 44.1kHz 16-bit mono WAV): sfx_click, sfx_pick,
sfx_peek, sfx_present, sfx_perfect, sfx_critic, sfx_tick, sfx_mission,
sfx_win, sfx_lose. Music loops: bgm_menu, bgm_game (gentle, different
from one-pan). .sound files + audio.go components for each.
