-- GamePix SDK bridge (GamePix SDK v3, https://partners.gamepix.com/sdk/doc/javascript).
-- The SDK script + glue JS are injected into the built index.html by
-- tools/inject_gamepix.py: GamePixConfig manual lifecycle, pause/resume
-- handlers that set window.__gpx_paused, and a visibility handler that
-- sets window.__gpx_hidden. All calls here are guarded: the game runs
-- fully without the SDK (local dev, no network, or a failed SDK load).
--
-- Pause/resume flow: the GamePix Player calls the registered pause/resume
-- handlers around ads; the glue sets the flags; game.script polls
-- poll_paused() once per frame (update) and applies the ad-pause. The
-- flags are the source of truth, not one-shot events, so a missed or
-- erroring ad can never leave the game stuck paused: when the ad ends
-- (or errors / has no fill) the SDK fires resume and the flag clears.
local M = {}

local ok_html5, html5 = pcall(require, "html5")

local function run(js)
  if not ok_html5 then return "" end
  local ok, res = pcall(html5.run, js)
  if ok and type(res) == "string" then return res end
  return ""
end

local loaded_called = false
local started = false

-- Report loading complete + game ready (manual lifecycle). Once only.
-- Called when the title screen first shows: the game can be shown.
-- Sets window.__gpx_loaded_called so the verify harness can confirm the
-- lifecycle call landed (the SDK itself shows no observable state for it).
function M.loaded()
  if loaded_called then return end
  loaded_called = true
  run("window.__gpx_loaded_called=1;if(window.GamePix&&GamePix.lifecycle){try{GamePix.lifecycle.loading(100)}catch(e){}try{GamePix.lifecycle.loaded()}catch(e){}}")
end

-- Report real gameplay start (manual lifecycle). Once only.
-- Called on the first start_level: a level, timer, or active loop begins.
function M.game_start()
  if started then return end
  started = true
  run("window.__gpx_started=1;if(window.GamePix&&GamePix.lifecycle){try{GamePix.lifecycle.gameStart()}catch(e){}}")
end

-- Interstitial ad at a natural break (level complete / Next / game over).
-- Fire and forget: the SDK calls the registered pause handler before the
-- ad and the resume handler after; poll_paused() applies both. Safe to
-- call when no ad can be shown (resolves success:false, no pause).
function M.show_interstitial()
  run("if(window.GamePix&&GamePix.ads){try{GamePix.ads.interstitial()}catch(e){}}")
end

-- Positive gameplay moment (level complete, high score). Optional signal.
function M.happy_moment(kind)
  run("if(window.GamePix){try{GamePix.happyMoment('" .. tostring(kind or "level_complete") .. "')}catch(e){}}")
end

-- Negative gameplay moment (level failed, game over). Optional signal.
function M.sad_moment(kind)
  run("if(window.GamePix){try{GamePix.sadMoment('" .. tostring(kind or "game_over") .. "')}catch(e){}}")
end

-- True when the GamePix Player wants the game paused right now: an ad is
-- showing (SDK pause handler) or the page is hidden (visibilitychange).
-- Polled once per frame by game.script update().
function M.poll_paused()
  if not ok_html5 then return false end
  return run("(window.__gpx_paused?1:0)|(window.__gpx_hidden?1:0)") == "1"
end

-- 1 when the GamePix SDK script loaded (verify harness probe).
function M.sdk_present()
  return run("typeof GamePix!=='undefined'?'1':'0'") == "1"
end

return M
