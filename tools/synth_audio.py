#!/usr/bin/env python3
"""Second Glance - all audio synthesized locally with numpy. No AI audio,
no downloads. 44.1kHz 16-bit mono WAVs. Music loops are exactly periodic:
notes are scheduled on a grid and decay to silence well before the loop
boundary, so the loop point is clean.
"""
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "audio", "wav")
os.makedirs(OUT, exist_ok=True)

SR = 44100
rng = np.random.default_rng(20261123)


def write(name, data, peak_db=-3.0):
    data = np.asarray(data, dtype=np.float64)
    peak = np.max(np.abs(data)) + 1e-12
    target = 10 ** (peak_db / 20.0)
    data = np.clip(data * (target / peak), -1.0, 1.0)
    path = os.path.join(OUT, name)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())
    print("wrote", path, f"{len(data)/SR:.2f}s")


def env(n, attack=0.005, decay=None):
    t = np.arange(n) / SR
    a = np.minimum(1.0, t / attack)
    if decay is None:
        decay = n / SR
    d = np.exp(-t / max(decay, 1e-4))
    return a * d


def sine(freq, dur, amp=0.5, decay=0.15):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return amp * np.sin(2 * np.pi * freq * t) * env(n, decay=decay)


def tri(freq, dur, amp=0.4, decay=0.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ph = (freq * t) % 1.0
    wave_ = 4 * np.abs(ph - 0.5) - 1.0
    return amp * wave_ * env(n, decay=decay)


def noise_burst(dur, amp=0.5, cutoff=3000):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    alpha = cutoff / (cutoff + SR)
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc += alpha * (x[i] - acc)
        y[i] = acc
    return amp * y * env(n, attack=0.001, decay=dur / 4)


def sweep(f0, f1, dur, amp=0.4, decay=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    phase = 2 * np.pi * (f0 * t + (f1 - f0) * t * t / (2 * dur))
    return amp * np.sin(phase) * env(n, decay=decay or dur / 2)


def mix_at(base, sig, start_s):
    i = int(start_s * SR)
    end = min(len(base), i + len(sig))
    base[i:end] += sig[: end - i]
    return base


def mix(*sigs):
    n = max(len(s) for s in sigs)
    out = np.zeros(n)
    for s in sigs:
        out[:len(s)] += s
    return out


# ------------------------------------------------------------------ SFX --
# click: short soft tick (0.15s)
write("sfx_click.wav", sine(660, 0.15, 0.4, decay=0.07))
# pick: garment pop - quick two-note blip up
write("sfx_pick.wav", mix(
    sine(523, 0.12, 0.45, decay=0.05),
    mix_at(np.zeros(int(0.25 * SR)), sine(784, 0.14, 0.45, decay=0.06), 0.06)))
# peek: curtain whoosh - filtered noise sweep down + soft chime
write("sfx_peek.wav", mix(
    noise_burst(0.35, 0.25, 2500),
    sweep(1200, 500, 0.3, 0.25, decay=0.15)))
# present: confident two-note fanfare
p = np.zeros(int(0.6 * SR))
for i, f in enumerate([659, 880]):
    p = mix_at(p, tri(f, 0.3, 0.45, 0.14), i * 0.14)
write("sfx_present.wav", p)
# perfect: five-note rising sparkle
p = np.zeros(int(0.8 * SR))
for i, f in enumerate([523, 659, 784, 1046, 1318]):
    p = mix_at(p, tri(f, 0.25, 0.4, 0.12), i * 0.08)
write("sfx_perfect.wav", p)
# critic: warm approving hum (two-note, major third)
c = np.zeros(int(0.5 * SR))
c = mix_at(c, sine(440, 0.3, 0.4, decay=0.14), 0.0)
c = mix_at(c, sine(554, 0.35, 0.4, decay=0.16), 0.12)
write("sfx_critic.wav", c)
# tick: last-seconds clock tick (0.15s)
write("sfx_tick.wav", mix(sine(1200, 0.15, 0.35, decay=0.06),
                          noise_burst(0.05, 0.2, 4000)))
# mission: mission-complete chime
m = np.zeros(int(0.7 * SR))
m = mix_at(m, tri(784, 0.25, 0.45, 0.12), 0.0)
m = mix_at(m, tri(1046, 0.4, 0.45, 0.2), 0.12)
write("sfx_mission.wav", m)
# win: warm ascending arpeggio (0.8s)
w = np.zeros(int(0.8 * SR))
for i, f in enumerate([440, 554, 659, 880]):
    w = mix_at(w, tri(f, 0.3, 0.45, 0.14), i * 0.1)
write("sfx_win.wav", w)
# lose: gentle descending phrase (the guest leaves, 0.7s)
l = np.zeros(int(0.7 * SR))
for i, f in enumerate([330, 294, 262]):
    l = mix_at(l, tri(f, 0.3, 0.4, 0.14), i * 0.15)
write("sfx_lose.wav", l)


# ---------------------------------------------------------------- music --
def note(freq, start, dur, amp=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = amp * np.sin(2 * np.pi * freq * t) * np.exp(-t / (dur * 0.6))
    sig += 0.4 * amp * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t / (dur * 0.4))
    return start, sig


def loop_melody(events, total_s, name):
    out = np.zeros(int(total_s * SR))
    for freq, start, dur, amp in events:
        _, sig = note(freq, start, dur, amp)
        i = int(start * SR)
        out[i:i + len(sig)] += sig[:len(out) - i]
    write(name, out, peak_db=-6.0)


# Menu loop: gentle A-minor waltz, 12s, 0.5s steps, last note ends at 11.5s
A, B, C, D, E, F, G = 440.0, 493.88, 523.25, 587.33, 659.25, 698.46, 783.99
A5, C5, E5, G5 = 880.0, 1046.5, 1318.5, 1568.0
menu = []
mel = [A5, E5, C5, E5, G5, E5, C5, A, B, C5, E5, C5, A, G, E, C]
for i, f in enumerate(mel):
    menu.append((f, i * 0.5, 0.45, 0.18))
    menu.append((f / 2, i * 0.5, 0.48, 0.1))
# soft root pad under the first bar
for start in (0.0, 3.0, 6.0, 9.0):
    menu.append((110.0, start, 2.8, 0.08))
loop_melody(menu, 12.0, "bgm_menu.wav")

# Game loop: light C-major, upbeat but calm, 12s, 0.4s steps
game = []
mel2 = [C5, E5, G5, E5, A5, G5, E5, C5, D, E, G, E,
        F, E, D, C, E, G, A5, G5, E5, D, C, E]
for i, f in enumerate(mel2):
    game.append((f, i * 0.4, 0.38, 0.16))
    game.append((f / 2, i * 0.4, 0.4, 0.09))
# gentle bass on the beat, every 1.2s
for i, f in enumerate([130.81, 130.81, 174.61, 196.0, 130.81, 130.81,
                       174.61, 196.0, 130.81, 146.83]):
    game.append((f, i * 1.2, 0.5, 0.1))
loop_melody(game, 12.0, "bgm_game.wav")
print("audio done")
