# audio.py — synthesizes the video's whole soundtrack in code: a chiptune
# loop (pad + bass + arpeggio, A minor), pickup blips on the exact pickup
# moments, and soft whooshes on every cut. Nothing sampled.
# 21.5 s, 44.1 kHz stereo WAV.

import math
import wave

import numpy as np

SR = 44100
DUR = 21.5
N = int(SR * DUR)
BPM = 116
BEAT = 60.0 / BPM
BAR = 4 * BEAT

# Chords (Hz): Am, F, C, G, repeated.
CHORDS = [
    [220.00, 261.63, 329.63],   # Am
    [174.61, 220.00, 261.63],   # F
    [261.63, 329.63, 392.00],   # C
    [196.00, 246.94, 293.66],   # G
]
ROOTS = [110.00, 87.31, 130.81, 98.00]

mix = np.zeros(N, dtype=np.float64)
t = np.arange(N) / SR


def add_pluck(start, freq, dur, amp, bright=1.0):
    i0 = int(start * SR)
    i1 = min(N, int((start + dur) * SR))
    if i1 <= i0:
        return
    tt = np.arange(i1 - i0) / SR
    env = np.exp(-tt * 6.0)
    wave_ = (np.sin(2 * np.pi * freq * tt)
             + 0.4 * bright * np.sin(2 * np.pi * freq * 2 * tt)
             + 0.15 * np.sin(2 * np.pi * freq * 3 * tt))
    mix[i0:i1] += amp * env * wave_


def add_pad(start, freqs, dur, amp):
    i0 = int(start * SR)
    i1 = min(N, int((start + dur) * SR))
    if i1 <= i0:
        return
    tt = np.arange(i1 - i0) / SR
    env = np.minimum(1.0, tt / 0.4) * np.minimum(1.0, (dur - tt) / 0.4)
    env = np.clip(env, 0, 1) ** 0.5
    sig = np.zeros(i1 - i0)
    for f in freqs:
        sig += np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 1.005 * tt)
    mix[i0:i1] += amp * env * sig / len(freqs)


def add_bass(start, freq, dur, amp):
    i0 = int(start * SR)
    i1 = min(N, int((start + dur) * SR))
    if i1 <= i0:
        return
    tt = np.arange(i1 - i0) / SR
    env = np.exp(-tt * 2.2)
    mix[i0:i1] += amp * env * (np.sin(2 * np.pi * freq * tt)
                               + 0.5 * np.sin(2 * np.pi * freq * 2 * tt))


def add_blip(start, f0=880.0, f1=1568.0):
    # Two-note pickup chime.
    add_pluck(start, f0, 0.16, 0.30)
    add_pluck(start + 0.09, f1, 0.24, 0.30)


def add_whoosh(start, dur=0.35):
    rng = np.random.RandomState(42)
    i0 = int(start * SR)
    i1 = min(N, int((start + dur) * SR))
    if i1 <= i0:
        return
    n = i1 - i0
    noise = rng.standard_normal(n)
    # Crude rising sweep: differentiate (high-pass) with a swell envelope.
    hp = np.diff(noise, prepend=0.0)
    tt = np.arange(n) / SR
    env = np.sin(np.pi * tt / dur) ** 2
    mix[i0:i1] += 0.10 * env * hp


# Music: 10 bars of Am F C G.
for bar in range(10):
    start = bar * BAR
    chord = CHORDS[bar % 4]
    root = ROOTS[bar % 4]
    add_pad(start, chord, BAR * 1.05, 0.10)
    for beat in range(4):
        add_bass(start + beat * BEAT, root, BEAT * 0.95, 0.22)
    # 8th-note arpeggio, two octaves up, pentatonic-ish walk.
    seq = [chord[0] * 2, chord[1] * 2, chord[2] * 2, chord[1] * 2,
           chord[2] * 2, chord[0] * 4, chord[1] * 2, chord[2] * 2]
    for k, f in enumerate(seq):
        add_pluck(start + k * BEAT / 2, f, 0.22, 0.13)

# Pickup blips at the video-time pickup moments (pair 2 D7, pair 3 D7, closing x2).
for tp in (9.1, 12.6, 15.2, 19.0):
    add_blip(tp)

# Whooshes on every cut.
for tc in (2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0):
    add_whoosh(tc - 0.12)

# Gentle fade out under the end card.
fade = np.ones(N)
tail = int(0.6 * SR)
fade[-tail:] = np.linspace(1, 0.15, tail)
mix *= fade

peak = np.max(np.abs(mix))
mix = mix / peak * 0.55  # -5 dB-ish headroom
stereo = np.stack([mix, mix], axis=1)
pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)

with wave.open("audio.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"audio.wav: {DUR}s, peak normalized to 0.55, {len(pcm)} samples")
