# Second Glance — GameDistribution (HTML5) notes

## Status
- SDK: gd-defold (https://github.com/GameDistribution/gd-defold, main
  branch), vendored locally under `gamedistribution/` (upstream folder,
  verbatim) with `[library] include_dirs = gamedistribution` in
  `game.project`. The URL dependency line was removed: bob cannot fetch
  the zip through the egress proxy (see Toolchain traps in README.md).
- `[gamedistribution] game_id = "PLACEHOLDER"` — the parent fills the
  real HEX Game ID from the portal Upload tab before upload. The
  bundle's index.html already carries `GD_OPTIONS` (verified present in
  `dist/html5/Second Glance/`).
- Game: original dress-up memory game, Defold 1.14.0. **12 levels** with
  missions (match a target, please all 3 critics, copy the look exactly
  5/5, reach a score target), 1-3 stars per level by score, progress
  saved; plus an endless mode (clients keep coming, 3 unhappy guests
  end the run, best score saved). 28 garments in 5 categories, 3 critics
  with live demands that double as clues. Controls: mouse / touch (tap
  tabs and garments, tap PEEK / CLEAR / PRESENT), keyboard (Q/W/E/R/T
  switch category, 1-6 pick an item, K peek, Enter present, C clear, P
  pause). Hidden verification aids: press **A** to toggle an auto-play
  bot (dresses the exact reference, then presents); press **U** on the
  title screen to unlock all levels (QA aid, not a player feature).
- Audio: 10 synthesized SFX + 2 music loops, all generated locally by
  `tools/synth_audio.py` (numpy, no AI audio, no downloads). Art: all
  sprites drawn in code by `tools/make_art.py` (PIL, no AI images, no
  copied assets).

## Ads
- `main/game.script` wraps `gdsdk` with pcall guards (`if gdsdk then ...
  pcall(...) end`), so the game runs fine with no SDK / no network.
  Listener registered in `init()` via `pcall(gdsdk.set_listener, ...)`.
- Pre-roll interstitial on the **first Play tap only** (`ui_play`,
  gated by the saved `played_once` flag, persisted so it fires once
  ever). Never on load, never on a timer.
- Interstitial when the player taps **Next** on a level-complete screen
  (`ui_next` -> `show_ad`).
- `SDK_GAME_PAUSE` sets `self.ad_paused`, mutes audio
  (`audio.set_muted(true)`) and posts `gd_pause` to the GUI, which sets
  `self.paused = true` and blocks gameplay input. `SDK_GAME_START` /
  `CONTENT_RESUME_REQUESTED` clears the ad pause, restores the player's
  own mute preference (`audio.set_muted(self.muted)`) and posts
  `gd_resume`, which restores `paused` to the user's own pause state
  (`self.user_paused or false`). `SDK_ERROR` / `AD_ERROR` /
  `AD_SDK_CANCELED` also resume if ad-paused (ad-error resume fix: with
  a PLACEHOLDER id every ad errors instantly, and a failed interstitial
  must not freeze the game).
- `show_play` resets `self.user_paused` (stale-pause-flag fix: after
  pause -> quit-to-title -> new game, the next gd_resume would
  otherwise re-pause the game).

## Animations
- `main/gui.gui_script` — curtain drop over the model at the end of the
  glance, garment pop-in on pick (scale squash), score popups (+pts,
  PERFECT 5/5, Critics x/3), critic tick/cross updates, burst particles
  on pick and on perfect, win confetti, tweened panels (`gui.animate`
  scale pops on title/level-complete/star nodes, button press squash),
  mission banner slide-in. All tweens are callback-free where nodes can
  be deleted mid-tween.

## Input-overlay fix (Nov 23, rebuild 2)
- The win panel's NEXT LEVEL button (GUI 568,238) sits inside the
  wardrobe grid's bottom-row hitbox, and stale play-screen picks were
  checked first in `on_input`, so real clicks on NEXT LEVEL and RESUME
  did nothing (the click dressed a wardrobe item instead). Fix: a
  `self.overlay_up` flag, set by `panel()` and cleared by
  `clear_overlay()` / `clear_all()`; while it is up, only overlay picks
  are tested. First attempt also gated on `screen ~= "play"`, which
  blocked the title screen's own buttons entirely; the gate is now the
  panel flag only.

## Verification (Nov 23, verify/verify.js, headless Chromium)
- **21/21 checks passed** on the shipped build (verify/results.json):
  title loads, canvas non-blank, glance shows a full reference, timer
  runs, 2 peeks, glance ends into dress phase, mouse tab switch,
  mouse wrong-item pick changes the outfit (match < 500), peek costs
  one, P pauses + resumes, autoplay wins level 1 (score 750, match
  500/500, critics 3/3), NEXT LEVEL starts level 2, MENU returns to
  title, pause/resume in endless, endless serves a client (score 800),
  mute toggle, no page/console errors (excluding GD SDK network noise +
  favicon 404s).
- Known visual defects (seen in verify screenshots, NOT fixed: the 2
  rebuilds were used on the input-overlay fix): the mission banner
  covers the model's hat for the first ~1.6s of the glance (glance is
  6s on level 1, so the full look is still visible for most of it);
  the critics' demand text at the bottom is dark-on-dark and hard to
  read. Both are polish, not blockers; fix in a later touch-up build
  if the owner wants it.

## Rebuild
Use the exact command from the project README.md (extender reverse
proxy on 127.0.0.1:8080 + egress truststore + run-bob.sh wasm-web
build+bundle).
