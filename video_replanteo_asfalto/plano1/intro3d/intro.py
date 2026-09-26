"""Escena inicial 3D: el robot de Protección Civil enseña el compás de cordel.

Flujo (desde esta carpeta):
    python3 intro.py voz          # 1) locución + warp.json (ajuste de tiempos a la voz)
    blender -b -P escena_blender.py -- [--preview]   # 2) render de fotogramas en frames/
    python3 intro.py montar       # 3) rótulos + subtítulos + voz -> intro.mp4

Requisitos: pip install pillow numpy imageio-ffmpeg piper-tts ; Blender 4.x (Eevee).
"""
import json
import os
import subprocess
import sys
import tarfile
import urllib.request
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1920, 1080, 25
END_T = 101.0  # duración del guion (s), antes de ajustar a la voz

# (inicio, fin, subtítulo, texto hablado). Los tiempos coinciden con la animación de escena_blender.py.
CAPS = [
    (0.3, 6.5, "¡Hola! Soy Robi, de Protección Civil. Antes de replantear, os enseño a trazar arcos y perpendiculares con un cordel y una tiza.", None),
    (6.5, 16, "Atamos una tiza cilíndrica al extremo del cordel con un nudo firme. Este es nuestro compás.", None),
    (16, 23.5, "La mano izquierda sujeta el cordel en el centro, pegado al suelo, y no se mueve.", None),
    (23.5, 31, "La derecha tensa el cordel y, sin aflojar, gira marcando el arco con la tiza. El radio es el cordel que queda entre las dos manos.", None),
    (31, 39, "Perpendicular en una esquina. Mano izquierda en A: arco que corta la línea en el punto 1.",
     "Perpendicular en una esquina. Mano izquierda en a: arco que corta la línea en el punto uno."),
    (39, 49, "Sin cambiar el radio, centro en 1: cortamos el arco en el punto 2. Centro en 2: cortamos en el 3.",
     "Sin cambiar el radio, centro en uno: cortamos el arco en el punto dos. Centro en dos: cortamos en el tres."),
    (49, 58, "Desde el 2 y desde el 3, dos arcos más. Se cruzan en el punto 4.",
     "Desde el dos y desde el tres, dos arcos más. Se cruzan en el punto cuatro."),
    (58, 68, "Tensamos el cordel desde A pasando por el 4 y marcamos la recta: ¡ángulo recto!",
     "Tensamos el cordel desde a, pasando por el cuatro, y marcamos la recta: ¡ángulo recto!"),
    (68, 76, "Perpendicular en un punto medio, con arcos iguales. Marcamos dos puntos a la misma distancia de M.",
     "Perpendicular en un punto medio, con arcos iguales. Marcamos dos puntos a la misma distancia de eme."),
    (76, 86, "Con el mismo radio, un arco desde cada punto. Donde se cruzan está la perpendicular.", None),
    (86, 95, "Unimos M con el cruce: otra perpendicular perfecta.",
     "Unimos eme con el cruce: otra perpendicular perfecta."),
    (95, 101, "¡Ya sabéis usar el compás de cordel! Ahora, vamos con el plano 1.",
     "¡Ya sabéis usar el compás de cordel! Ahora, vamos con el plano uno."),
]
CAPS = [(a, b, s, sp or s) for a, b, s, sp in CAPS]

VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz"
VOICE_DIR = os.path.join(HERE, ".voz")
VOICE_MODEL = os.path.join(VOICE_DIR, "es-carlfm-x-low.onnx")
LEAD, TAIL = 0.3, 0.5


def ensure_voice():
    if os.path.exists(VOICE_MODEL):
        return
    os.makedirs(VOICE_DIR, exist_ok=True)
    tgz = os.path.join(VOICE_DIR, "voz.tar.gz")
    urllib.request.urlretrieve(VOICE_URL, tgz)
    with tarfile.open(tgz) as tf:
        tf.extractall(VOICE_DIR)
    os.remove(tgz)


def synth(text, idx):
    import numpy as np
    path = os.path.join(VOICE_DIR, f"frase_{idx:02d}.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE_MODEL, "-f", path, "--sentence-silence", "0.35"],
                   input=text.encode("utf-8"), check=True, capture_output=True)
    with wave.open(path) as w:
        sr = w.getframerate()
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return audio, sr


def voz():
    """Genera la locución y warp.json (tiempo del guion <-> tiempo del vídeo)."""
    import numpy as np
    ensure_voice()
    clips = [synth(c[3], i) for i, c in enumerate(CAPS)]
    sr = clips[0][1]
    ks, kv = [0.0], [0.0]
    for (t0, t1, _, _), (audio, _) in zip(CAPS, clips):
        ks.append(t0)
        kv.append(kv[-1] + t0 - ks[-2])
        ks.append(t1)
        kv.append(kv[-1] + max(t1 - t0, LEAD + len(audio) / sr + TAIL))
    ks.append(END_T)
    kv.append(kv[-1] + END_T - ks[-2])
    track = np.zeros(int((kv[-1] + 1) * sr), dtype=np.float32)
    for (t0, *_), (audio, _) in zip(CAPS, clips):
        i = int((float(np.interp(t0, ks, kv)) + LEAD) * sr)
        track[i:i + len(audio)] += audio
    track *= 0.9 / max(1e-6, np.abs(track).max())
    with wave.open(os.path.join(VOICE_DIR, "narracion.wav"), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((track * 32767).astype(np.int16).tobytes())
    n = int(kv[-1] * FPS)
    script_t = [float(np.interp(i / FPS, kv, ks)) for i in range(n)]
    with open(os.path.join(HERE, "warp.json"), "w") as f:
        json.dump({"ks": ks, "kv": kv, "frames": script_t}, f)
    print(f"Duración con locución: {kv[-1]:.1f} s · {n} fotogramas")


def montar():
    """Superpone cabecera y subtítulos a los fotogramas de Blender y añade la voz."""
    import imageio_ffmpeg
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    fd = "/usr/share/fonts/truetype/dejavu/"
    f_cap, f_h, f_hs = (ImageFont.truetype(fd + "DejaVuSans.ttf", 34), ImageFont.truetype(fd + "DejaVuSans-Bold.ttf", 30),
                        ImageFont.truetype(fd + "DejaVuSans.ttf", 26))
    warp = json.load(open(os.path.join(HERE, "warp.json")))
    frames = warp["frames"]
    limit = float(sys.argv[2]) if len(sys.argv) > 2 else None  # segundos (muestra)
    if limit:
        frames = frames[:int(limit * FPS)]

    def wrap(text, fnt, width):
        lines, cur = [], ""
        for word in text.split():
            test = (cur + " " + word).strip()
            if fnt.getlength(test) <= width or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        return lines + ([cur] if cur else [])

    out = os.path.join(HERE, "muestra_intro.mp4" if limit else "intro.mp4")
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", os.path.join(VOICE_DIR, "narracion.wav"),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    last = None
    for i, T in enumerate(frames):
        p = os.path.join(HERE, "frames", f"{i:05d}.png")
        if os.path.exists(p):
            last = p
        im = Image.open(last).convert("RGB")
        if im.size != (W, H):
            im = im.resize((W, H), Image.LANCZOS)
        d = ImageDraw.Draw(im, "RGBA")
        d.rectangle((0, 0, W, 70), fill=(15, 20, 30, 215))
        d.text((30, 35), "Antes de replantear", font=f_h, fill=(246, 244, 232), anchor="lm")
        d.text((345, 35), "· El compás de cordel", font=f_hs, fill=(160, 170, 190), anchor="lm")
        d.rectangle((0, 930, W, H), fill=(10, 12, 18, 235))
        cur = next((c for c in CAPS if c[0] <= T < c[1]), None)
        if cur:
            a = min(1, (T - cur[0]) / 0.3, (cur[1] - T) / 0.3)
            lines = wrap(cur[2], f_cap, 1760)
            y0 = 1005 - (len(lines) - 1) * 22
            for j, line in enumerate(lines):
                d.text((W / 2, y0 + j * 44), line, font=f_cap, fill=(255, 255, 255, int(255 * max(0, a))), anchor="mm")
        if i < 12:  # fundido de entrada
            d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(255 * (1 - i / 12))))
        if i > len(frames) - 13:
            d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(255 * (1 - (len(frames) - 1 - i) / 12))))
        proc.stdin.write(np.asarray(im).tobytes())
    proc.stdin.close()
    proc.wait()
    print("OK", out)


def srt():
    """Subtítulos de la escena 3D en tiempo de vídeo -> intro.srt"""
    import numpy as np
    warp = json.load(open(os.path.join(HERE, "warp.json")))

    def ts(t):
        ms = int(round(float(np.interp(t, warp["ks"], warp["kv"])) * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    with open(os.path.join(HERE, "intro.srt"), "w", encoding="utf-8") as f:
        for i, (t0, t1, text, _) in enumerate(CAPS, 1):
            f.write(f"{i}\n{ts(t0)} --> {ts(t1)}\n{text}\n\n")


if __name__ == "__main__":
    {"voz": voz, "montar": montar, "srt": srt}[sys.argv[1]]()
