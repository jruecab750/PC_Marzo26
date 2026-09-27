# Música original para el reel (sintetizada, sin derechos de terceros): 120 bpm, 30 s, La menor.
import numpy as np, wave
SR, BPM, DUR = 44100, 120, 30.0
beat = 60 / BPM; N = int(SR * DUR); mix = np.zeros((N, 2))
t_all = np.arange(N) / SR
def note_hz(n): return 440 * 2 ** ((n - 69) / 12)
def add(sig, start, pan=0.0, gain=1.0):
    i = int(start * SR); j = min(N, i + len(sig))
    if i >= N: return
    s = sig[: j - i] * gain
    mix[i:j, 0] += s * (1 - pan) * 0.7071 * 1.4142 / 2 * 2 ** 0.5
    mix[i:j, 1] += s * (1 + pan) * 0.7071 * 1.4142 / 2 * 2 ** 0.5
def env(n, a=0.005, d=0.1, s=0.6, r=0.1, hold=None):
    hold = n / SR if hold is None else hold
    t = np.arange(n) / SR
    e = np.where(t < a, t / a, np.where(t < a + d, 1 - (1 - s) * (t - a) / d, s))
    rel = np.clip((t - hold) / r, 0, 1); return e * (1 - rel)
def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9)
def snare():
    n = int(0.22 * SR); t = np.arange(n) / SR
    noise = np.random.default_rng(1).standard_normal(n)
    return (0.6 * noise * np.exp(-t * 20) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25))
def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR); t = np.arange(n) / SR
    noise = np.random.default_rng(2).standard_normal(n); noise = np.diff(np.concatenate([[0], noise]))
    return noise * np.exp(-t * (18 if open_ else 70))
def saw(freq, n, detune=0.004):
    t = np.arange(n) / SR; out = 0
    for d in (-detune, 0, detune): out = out + 2 * ((t * freq * (1 + d)) % 1) - 1
    return out / 3
def lowpass(x, k):  # filtro sencillo de un polo
    y = np.zeros_like(x); a = k; acc = 0.0
    for i in range(len(x)): acc += a * (x[i] - acc); y[i] = acc
    return y
# Acordes Am F C G (2 s cada uno)
prog = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
bars = int(DUR / (4 * beat))
for b in range(bars):
    t0 = b * 4 * beat; chord = prog[b % 4]; intro = b < 2; outro = b >= bars - 1
    # pad
    n = int(4 * beat * SR); pad = sum(saw(note_hz(m), n, 0.006) for m in chord) / 3
    pad = lowpass(pad, 0.04 if intro else 0.09) * env(n, 0.3, 0.2, 0.8, 0.4, hold=4 * beat - 0.3)
    add(pad, t0, 0, 0.22)
    if outro: continue
    # bajo en corcheas
    for k in range(8):
        n = int(0.5 * beat * SR); root = chord[0] - 12
        bs = lowpass(saw(note_hz(root + (12 if k % 4 == 3 else 0)), n, 0.0), 0.12) * env(n, 0.005, 0.08, 0.5, 0.05)
        add(bs, t0 + k * 0.5 * beat, 0, 0.0 if intro else 0.5)
    # batería
    for k in range(4):
        tb = t0 + k * beat
        add(kick(), tb, 0, 0.9)
        if k in (1, 3) and not intro: add(snare(), tb, 0.1, 0.45)
        add(hat(), tb + 0.5 * beat, -0.3, 0.25)
        if not intro: add(hat(), tb, -0.3, 0.12)
    # arpegio en semicorcheas desde el compás 4
    if b >= 3:
        seq = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 24]
        for k in range(16):
            n = int(0.25 * beat * SR); m = seq[k % 4]
            ar = saw(note_hz(m), n, 0.002) * env(n, 0.002, 0.06, 0.2, 0.03)
            add(ar, t0 + k * 0.25 * beat, 0.35 if k % 2 else -0.35, 0.16)
# golpe final
fin = (bars - 1) * 4 * beat
add(kick(), fin, 0, 1.0); add(snare(), fin, 0, 0.5)
n = int(2.2 * SR); add(sum(saw(note_hz(m), n) for m in (57, 64, 69, 72)) / 4 * env(n, 0.005, 0.5, 0.4, 1.2, hold=0.8), fin, 0, 0.3)
# fundido final y normalizado
fade = np.clip((DUR - t_all) / 1.2, 0, 1)[:, None]; mix *= fade
mix /= np.abs(mix).max() / 0.89
with wave.open('musica.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok', DUR, 's')
