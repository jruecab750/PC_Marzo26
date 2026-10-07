"""Monta el vídeo horizontal: fotogramas de grabar_video.mjs + la voz de cada escena en su sitio.

    python3 montar_video.py DIR_FOTOGRAMAS IDX0 salida.mp4

Lee DIR/horario.json (escenas, frases con t = instante en el vídeo y ta = instante en el audio original)
y los WAV de la voz que dejó construir.py en escenas_pcia/.voz/escena_<IDX0 + n>.wav. Cada frase se
coloca en su instante (la voz espera a los robots, como en la página).
"""
import json
import os
import subprocess
import sys
import wave

import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
VOZ = os.path.join(HERE, "..", "escenas_pcia", ".voz")


def main(d, idx0, out):
    h = json.load(open(os.path.join(d, "horario.json")))
    fps, sr = h["fps"], 16000
    frames = sorted(f for f in os.listdir(d) if f.endswith(".jpg"))
    total = len(frames) / fps
    pista = bytearray(b"\x00\x00" * int(total * sr + sr))
    base = 0.0
    for n, sc in enumerate(h["escenas"]):
        with wave.open(os.path.join(VOZ, f"escena_{idx0 + n:02d}.wav")) as w:
            sr = w.getframerate()
            pcm = w.readframes(w.getnframes())
        for c in sc["caps"]:
            a0, a1 = int(c["ta"] * sr) * 2, int((c["ta"] + c["d"] + 0.15) * sr) * 2
            seg = pcm[a0:a1]
            o = int((base + c["t"]) * sr) * 2
            pista[o:o + len(seg)] = seg
        base += round(sc["dur"] * fps) / fps
    wav = os.path.join(d, "voz.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(bytes(pista[: int(total * sr) * 2]))
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-framerate", str(fps),
                    "-i", os.path.join(d, "%05d.jpg"), "-i", wav,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                    "-vf", "scale=1920:1080", "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
                    "-movflags", "+faststart", "-shortest", out], check=True)
    print(out, f"{total:.1f} s", f"{os.path.getsize(out) / 1e6:.1f} MB")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
