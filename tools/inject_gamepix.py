#!/usr/bin/env python3
"""Inject the GamePix SDK v3 + glue JS into a built Defold HTML5 index.html.

Usage: python3 tools/inject_gamepix.py <bundle-dir>
  e.g. python3 tools/inject_gamepix.py "dist/html5/Bloom Bubbles"

What it does (see https://partners.gamepix.com/sdk/doc/javascript):
  1. Inserts, as the first scripts in <head> (before the game bundle):
     - window.GamePixConfig = { lifecycle: 'manual' }
     - <script src="https://integration.gamepix.com/sdk/v3/gamepix.sdk.js">
     - Glue JS: registers GamePix pause/resume handlers that set
       window.__gpx_paused, tracks page visibility in window.__gpx_hidden,
       and reports lifecycle.loading(0). The game (main/gpx.lua) reports
       loading(100) + loaded() when the title screen shows, and gameStart()
       on the first level start. All calls are guarded: if the SDK fails to
       load, the game runs normally.
  2. Adds touch-action:none on <body> (GamePix submission guidelines).
  3. Verifies the result: GamePix SDK present, and NO GameDistribution
     residue (GD_OPTIONS, gamedistribution.com, gdsdk) remains in the file.

Idempotent: running it twice does not double-inject (marker check).
Exits non-zero on any failure so the build pipeline stops.
"""
import sys
from pathlib import Path

SDK_URL = "https://integration.gamepix.com/sdk/v3/gamepix.sdk.js"
MARKER = "GamePix glue (injected by tools/inject_gamepix.py)"

INJECTION = """<script>
window.GamePixConfig = { lifecycle: 'manual' };
</script>
<script src="__SDK_URL__"></script>
<script>
// __MARKER__
// - Registers pause/resume handlers that set window.__gpx_paused.
// - Tracks page visibility in window.__gpx_hidden.
// - Reports loading(0); the game reports loading(100) + loaded() from
//   Lua when the title screen shows, and gameStart() on first level start.
// All calls are guarded: if the SDK fails to load, the game runs normally.
window.__gpx_paused = 0;
window.__gpx_hidden = 0;
(function () {
  try {
    if (window.GamePix && GamePix.events) {
      GamePix.events.on('pause', function () { window.__gpx_paused = 1; });
      GamePix.events.on('resume', function () { window.__gpx_paused = 0; });
    }
    if (window.GamePix && GamePix.lifecycle) {
      try { GamePix.lifecycle.loading(0); } catch (e) {}
    }
  } catch (e) {}
  document.addEventListener('visibilitychange', function () {
    window.__gpx_hidden = document.hidden ? 1 : 0;
  });
})();
</script>
<style>body{touch-action:none;-ms-touch-action:none}</style>
""".replace("__SDK_URL__", SDK_URL).replace("__MARKER__", MARKER)

# Anything GameDistribution in the built page means the GD extension is
# still wired in — a GamePix build must contain no third-party SDK.
FORBIDDEN = ("GD_OPTIONS", "gamedistribution", "gdsdk",
             "html5.api.gamedistribution.com", "GD_DEFOLD")

ANCHOR = "<!-- The above 5 meta tags *must* come first in the head"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: inject_gamepix.py <bundle-dir>", file=sys.stderr)
        return 2
    bundle = Path(sys.argv[1])
    index = bundle / "index.html"
    if not index.is_file():
        print(f"no index.html in {bundle}", file=sys.stderr)
        return 2
    text = index.read_text(encoding="utf-8")
    if MARKER in text:
        print("already injected, skipping")
    else:
        if ANCHOR in text:
            text = text.replace(ANCHOR, INJECTION + ANCHOR, 1)
        elif "<head>" in text:
            text = text.replace("<head>", "<head>\n" + INJECTION, 1)
        else:
            print("no <head> anchor found in index.html", file=sys.stderr)
            return 2
        index.write_text(text, encoding="utf-8")
        print(f"injected GamePix SDK into {index}")
    # Verify.
    text = index.read_text(encoding="utf-8")
    problems = []
    if SDK_URL not in text:
        problems.append("GamePix SDK script missing after injection")
    if MARKER not in text:
        problems.append("glue marker missing after injection")
    low = text.lower()
    for bad in FORBIDDEN:
        if bad.lower() in low:
            problems.append(f"GameDistribution residue found: {bad}")
    if problems:
        print("INJECTION VERIFICATION FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print("injection verified: GamePix SDK present, no GameDistribution residue")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
