"""Voz de GALía: locución en castellano con Piper (voz es-carlfm-x-low), la misma de las escenas de replanteo.

Uso:
    pip install piper-tts imageio-ffmpeg
    python3 voz_galia.py "Hola, soy Galía." salida.mp3          # una frase
    python3 voz_galia.py guion.txt salida.mp3                    # una frase por línea, con pausas entre ellas
    python3 voz_galia.py guion.txt salida.wav --tiempos          # además escribe salida.json con inicio y duración de cada frase

Todo es local y gratuito: la voz se descarga una vez (28 MB) en la carpeta .voz/ y después funciona sin conexión.
"""
import json, os, subprocess, sys, tarfile, urllib.request, wave

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz"
VOICE_DIR = os.path.join(HERE, ".voz")
VOICE_MODEL = os.path.join(VOICE_DIR, "es-carlfm-x-low.onnx")
START, GAP, TAIL = 0.5, 0.55, 1.2      # silencios en segundos: al principio, entre frases y al final
SENTENCE_SILENCE = "0.3"               # pausa de Piper entre oraciones dentro de una misma frase
MP3_BITRATE = "24k"                    # la voz es de 16 kHz: 24 kb/s en mono basta y pesa muy poco


def asegurar_voz():
    """Descarga y descomprime la voz la primera vez (release de GitHub; Hugging Face puede estar bloqueado)."""
    if os.path.exists(VOICE_MODEL):
        return
    os.makedirs(VOICE_DIR, exist_ok=True)
    tgz = os.path.join(VOICE_DIR, "voz.tar.gz")
    urllib.request.urlretrieve(VOICE_URL, tgz)
    with tarfile.open(tgz) as tf:
        tf.extractall(VOICE_DIR)
    os.remove(tgz)


def preparar(texto):
    """Ajustes de pronunciación que usamos con GALía."""
    texto = texto.replace("GALía", "Galía").replace("GALia", "Galía").replace("PCia", "Pecía")
    if texto.startswith("¡Hola!"):   # Piper convierte un «¡Hola!» suelto al principio en un chasquido
        texto = "Hola," + texto[len("¡Hola!"):]
    return texto


def sintetizar(texto, wav):
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE_MODEL, "-f", wav, "--sentence-silence", SENTENCE_SILENCE],
                   input=preparar(texto).encode("utf-8"), check=True, capture_output=True)
    with wave.open(wav) as w:
        return w.getframerate(), w.readframes(w.getnframes())


def locucion(frases, salida, tiempos=False):
    asegurar_voz()
    tmp = os.path.join(VOICE_DIR, "frase.wav")
    partes, marcas, sr, t = [], [], 16000, START
    partes.append(b"\x00\x00" * int(START * sr))
    for texto in frases:
        sr, pcm = sintetizar(texto, tmp)
        d = len(pcm) / 2 / sr
        marcas.append({"texto": texto, "inicio": round(t, 3), "duracion": round(d, 3)})
        partes += [pcm, b"\x00\x00" * int(GAP * sr)]
        t += d + GAP
    partes[-1] = b"\x00\x00" * int(TAIL * sr)
    wav = salida if salida.lower().endswith(".wav") else os.path.join(VOICE_DIR, "locucion.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(b"".join(partes))
    if not salida.lower().endswith(".wav"):
        import imageio_ffmpeg
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", wav, "-ac", "1", "-b:a", MP3_BITRATE, salida], check=True)
    if tiempos:
        json.dump(marcas, open(os.path.splitext(salida)[0] + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{salida}: {len(frases)} frases, {t - GAP + TAIL:.1f} s")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    fuente, salida = sys.argv[1], sys.argv[2]
    frases = [l.strip() for l in open(fuente, encoding="utf-8") if l.strip()] if os.path.isfile(fuente) else [fuente]
    locucion(frases, salida, "--tiempos" in sys.argv)
