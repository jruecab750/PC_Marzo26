"""Construye «PCia · Replanteo del plano 1»: escenas 3D interactivas con voz y subtítulos.

    python3 construir.py
        -> pcia_replanteo.html        (página para publicar como Artifact)
        -> pcia_replanteo_sites.html  (documento HTML completo para Google Sites / un servidor web)

La animación 3D va en plantilla.html (three.js). Aquí están los textos de cada escena y
la locución (Piper, voz es-carlfm-x-low). Cada frase se sintetiza aparte y su inicio y
duración se guardan para que la animación se sincronice con la voz.
"""
import base64
import json
import os
import subprocess
import sys
import tarfile
import urllib.request
import wave

import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz"
VOICE_DIR = os.path.join(HERE, ".voz")
VOICE_MODEL = os.path.join(VOICE_DIR, "es-carlfm-x-low.onnx")
START, GAP, TAIL = 0.5, 0.55, 1.2  # silencios (s): inicio de escena, entre frases y al final

# Cada frase: (subtítulo, texto hablado o None si es el mismo)
SCENES = [
    dict(id="inicio", short="Hola", title="Presentación", group="Inicio", caps=[
        ("¡Hola! Soy PCia, de Protección Civil. Hoy vamos a replantear el plano 1 sobre el asfalto.",
         "¡Hola! Soy Pecía, de Protección Civil. Hoy vamos a replantear el plano uno sobre el asfalto."),
        ("Me ayudan PCia2 y PCia3. Podéis saltar a cualquier escena con los botones de arriba.",
         "Me ayudan Pecía dos y Pecía tres. Podéis saltar a cualquier escena con los botones de arriba."),
    ]),
    dict(id="compas", short="Compás", title="El compás de cordel", group="Compás", caps=[
        ("Atamos una tiza cilíndrica al extremo del cordel con un nudo firme. Este es nuestro compás.", None),
        ("La mano izquierda sujeta el cordel en el centro, pegado al suelo, y no se mueve.", None),
        ("La derecha tensa el cordel y, sin aflojar, gira marcando el arco con la tiza. El radio es el cordel entre las dos manos.", None),
    ]),
    dict(id="esquina", short="Esquina", title="Perpendicular en una esquina", group="Compás", caps=[
        ("Perpendicular en una esquina. Mano izquierda en A: arco que corta la línea en el punto 1.",
         "Perpendicular en una esquina. Mano izquierda en a: arco que corta la línea en el punto uno."),
        ("Sin cambiar el radio, centro en 1: cortamos el arco en el punto 2. Centro en 2: cortamos en el 3.",
         "Sin cambiar el radio, centro en uno: cortamos el arco en el punto dos. Centro en dos: cortamos en el tres."),
        ("Desde el 2 y desde el 3, dos arcos más. Se cruzan en el punto 4.",
         "Desde el dos y desde el tres, dos arcos más. Se cruzan en el punto cuatro."),
        ("Tensamos el cordel desde A pasando por el 4 y marcamos la recta: ¡ángulo recto!",
         "Tensamos el cordel desde a, pasando por el cuatro, y marcamos la recta: ¡ángulo recto!"),
    ]),
    dict(id="medio", short="Arcos iguales", title="Perpendicular en un punto medio", group="Compás", caps=[
        ("Perpendicular en un punto medio, con arcos iguales. Marcamos dos puntos a la misma distancia de M.",
         "Perpendicular en un punto medio, con arcos iguales. Marcamos dos puntos a la misma distancia de eme."),
        ("Con el mismo radio, un arco desde cada punto. Donde se cruzan está la perpendicular.", None),
        ("Unimos M con el cruce: otra perpendicular perfecta.", "Unimos eme con el cruce: otra perpendicular perfecta."),
    ]),
    dict(id="plano", short="Plano 1", title="El plano 1", group="Plano 1", caps=[
        ("Este es el plano 1: un rectángulo de 2,50 por 3,50 metros con un triángulo rectángulo en cada lado.",
         "Este es el plano uno: un rectángulo de dos metros y medio por tres y medio, con un triángulo rectángulo en cada lado."),
        ("Cada triángulo sale de un trazo perpendicular desde el punto medio del lado y lleva un semicírculo con el centro en la mitad de uno de sus lados.", None),
        ("Material: cinta métrica, cordel con tiza atada y calculadora. Zona limpia, señalizada y sin tráfico.", None),
    ]),
    dict(id="paso1", short="Paso 1", title="Paso 1 · Línea base AB", group="Plano 1", caps=[
        ("Paso 1: la línea base. PCia2 sujeta el cero de la cinta en A y PCia3 marca B a 2,50 metros.",
         "Paso uno: la línea base. Pecía dos sujeta el cero de la cinta en a, y Pecía tres marca be, a dos metros y medio."),
        ("Con los dos extremos marcados, trazamos AB en blanco. Cada línea que quede definida, la marcamos en el suelo.",
         "Con los dos extremos marcados, trazamos a be en blanco. Cada línea que quede definida, la marcamos en el suelo."),
    ]),
    dict(id="paso2", short="Paso 2", title="Paso 2 · Perpendicular en A", group="Plano 1", caps=[
        ("Paso 2: perpendicular en A con arcos. PCia2 fija el cordel en A y PCia3 traza un arco de 1,50 metros que corta la base: punto 1.",
         "Paso dos: perpendicular en a, con arcos. Pecía dos fija el cordel en a, y Pecía tres traza un arco de metro y medio que corta la base: punto uno."),
        ("Sin cambiar la medida, desde el punto 1 cortamos el arco en el punto 2, y desde el 2, en el punto 3.",
         "Sin cambiar la medida, desde el punto uno cortamos el arco en el punto dos, y desde el dos, en el punto tres."),
        ("Ahora, desde el 2 y desde el 3, dos arcos más de 1,50 metros. Se cruzan en el punto 4.",
         "Ahora, desde el dos y desde el tres, dos arcos más de metro y medio. Se cruzan en el punto cuatro."),
        ("La recta de A al punto 4 es perpendicular a la base. Por ella medimos 3,50 metros, marcamos D y trazamos AD en blanco.",
         "La recta de a al punto cuatro es perpendicular a la base. Por ella medimos tres metros y medio, marcamos de, y trazamos a de en blanco."),
    ]),
    dict(id="paso3", short="Paso 3", title="Paso 3 · Perpendicular en B y cierre", group="Plano 1", caps=[
        ("Paso 3: repetimos en B. Arco de 1,50 metros con centro en B, y de ahí los puntos 1, 2, 3 y 4, igual que antes.",
         "Paso tres: repetimos en be. Arco de metro y medio con centro en be, y de ahí los puntos uno, dos, tres y cuatro, igual que antes."),
        ("Medimos 3,50 metros por la perpendicular: punto C. Con C y D marcados, trazamos BC y DC en blanco.",
         "Medimos tres metros y medio por la perpendicular: punto ce. Con ce y de marcados, trazamos be ce, y de ce, en blanco."),
    ]),
    dict(id="paso4", short="Paso 4", title="Paso 4 · Comprobación", group="Plano 1", caps=[
        ("Paso 4: comprobamos. El lado DC tiene que medir 2,50 metros.",
         "Paso cuatro: comprobamos. El lado de ce tiene que medir dos metros y medio."),
        ("Y las dos diagonales, lo mismo: 4,30 metros. Si no coinciden, revisad las perpendiculares.",
         "Y las dos diagonales, lo mismo: cuatro metros y treinta centímetros. Si no coinciden, revisad las perpendiculares."),
    ]),
    dict(id="paso5", short="Paso 5", title="Paso 5 · Puntos medios", group="Plano 1", caps=[
        ("Paso 5: los puntos medios. En los lados de 2,50 medimos 1,25 metros; en los de 3,50, 1,75.",
         "Paso cinco: los puntos medios. En los lados de dos y medio, medimos uno veinticinco; en los de tres y medio, uno setenta y cinco."),
        ("De cada punto medio sale un trazo perpendicular hacia fuera, como dice la nota del plano.", None),
    ]),
    dict(id="paso6", short="Paso 6", title="Paso 6 · Triángulo inferior", group="Plano 1", caps=[
        ("Paso 6: triángulo de abajo. La perpendicular en M1 la hacemos con arcos iguales: dos puntos a 75 centímetros, uno a cada lado.",
         "Paso seis: triángulo de abajo. La perpendicular en eme uno la hacemos con arcos iguales: dos puntos a setenta y cinco centímetros, uno a cada lado."),
        ("Desde cada uno, un arco de 1,50 metros hacia fuera. Donde se cruzan, punto 3: está justo en la perpendicular.",
         "Desde cada uno, un arco de metro y medio hacia fuera. Donde se cruzan, punto tres: está justo en la perpendicular."),
        ("Desde M1, pasando por el punto 3, medimos 2 metros: es E. Trazamos M1E y EB en blanco.",
         "Desde eme uno, pasando por el punto tres, medimos dos metros: es el punto e. Trazamos eme uno e, y e be, en blanco."),
        ("El semicírculo tiene el centro en la mitad de M1E, a 1 metro. Con el cordel a 1 metro, giramos y lo marcamos.",
         "El semicírculo tiene el centro en la mitad de eme uno e, a un metro. Con el cordel a un metro, giramos y lo marcamos."),
    ]),
    dict(id="paso7", short="Paso 7", title="Paso 7 · Triángulo derecho", group="Plano 1", caps=[
        ("Paso 7: triángulo de la derecha. Mismo método en M2: dos puntos a 75 centímetros y arcos iguales de 1,50.",
         "Paso siete: triángulo de la derecha. Mismo método en eme dos: dos puntos a setenta y cinco centímetros, y arcos iguales de metro y medio."),
        ("Por el cruce, 2 metros hasta F. Trazamos M2F y FB en blanco.",
         "Por el cruce, dos metros hasta efe. Trazamos eme dos efe, y efe be, en blanco."),
        ("Aquí el semicírculo va sobre FB, que mide 2,66 metros: el centro está en su mitad y el radio es 1,33.",
         "Aquí el semicírculo va sobre efe be, que mide dos sesenta y seis: el centro está en su mitad, y el radio es uno treinta y tres."),
    ]),
    dict(id="paso8", short="Paso 8", title="Paso 8 · Triángulo izquierdo", group="Plano 1", caps=[
        ("Paso 8: triángulo de la izquierda. Igual: arcos iguales desde M4, hacia fuera.",
         "Paso ocho: triángulo de la izquierda. Igual: arcos iguales desde eme cuatro, hacia fuera."),
        ("A 2 metros, el punto J. Trazamos M4J y JD en blanco.",
         "A dos metros, el punto jota. Trazamos eme cuatro jota, y jota de, en blanco."),
        ("Centro en la mitad de JD, a 1,33 metros, y semicírculo de 1,33 de radio.",
         "Centro en la mitad de jota de, a uno treinta y tres, y semicírculo de uno treinta y tres de radio."),
    ]),
    dict(id="paso9", short="Paso 9", title="Paso 9 · Triángulo superior", group="Plano 1", caps=[
        ("Paso 9: triángulo de arriba. Arcos iguales en M3, esta vez hacia arriba.",
         "Paso nueve: triángulo de arriba. Arcos iguales en eme tres, esta vez hacia arriba."),
        ("Este trazo es más largo: 2,50 metros hasta G. Su punto medio, a 1,25, es H.",
         "Este trazo es más largo: dos metros y medio hasta ge. Su punto medio, a uno veinticinco, es hache."),
        ("Desde H, otra perpendicular con arcos iguales, ahora hacia la derecha. A 2 metros, el punto I.",
         "Desde hache, otra perpendicular con arcos iguales, ahora hacia la derecha. A dos metros, el punto i."),
        ("Trazamos HI, GI e I-M3 en blanco. El semicírculo va sobre GI, de 2,36 metros: radio 1,18.",
         "Trazamos hache i, ge i, e i eme tres, en blanco. El semicírculo va sobre ge i, de dos treinta y seis: radio uno dieciocho."),
    ]),
    dict(id="final", short="Final", title="Plano terminado", group="Plano 1", caps=[
        ("¡Plano terminado! Rectángulo, cuatro triángulos y cuatro semicírculos, todo a tamaño real sobre el asfalto.", None),
        ("Recordad: en una esquina, perpendicular con arcos desde el extremo; en un punto medio, arcos iguales.", None),
        ("¡Ahora os toca a vosotros! Replantead el plano 1 en el patio. Tolerancia: 2 centímetros.",
         "¡Ahora os toca a vosotros! Replantead el plano uno en el patio. Tolerancia: dos centímetros."),
    ]),
]


def ensure_voice():
    if os.path.exists(VOICE_MODEL):
        return
    os.makedirs(VOICE_DIR, exist_ok=True)
    tgz = os.path.join(VOICE_DIR, "voz.tar.gz")
    urllib.request.urlretrieve(VOICE_URL, tgz)
    with tarfile.open(tgz) as tf:
        tf.extractall(VOICE_DIR)
    os.remove(tgz)


def synth(text, path):
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE_MODEL, "-f", path, "--sentence-silence", "0.3"],
                   input=text.encode("utf-8"), check=True, capture_output=True)
    with wave.open(path) as w:
        return w.getframerate(), w.readframes(w.getnframes())


def build_audio(scene, idx):
    """Una pista por escena. Devuelve (caps con inicio/duración, duración total, mp3 en base64)."""
    frames, caps, sr, t = [], [], 16000, START
    frames.append(b"\x00\x00" * int(START * sr))
    for k, (sub, spoken) in enumerate(scene["caps"]):
        sr, pcm = synth(spoken or sub, os.path.join(VOICE_DIR, f"e{idx:02d}_{k}.wav"))
        d = len(pcm) / 2 / sr
        caps.append(dict(text=sub, t=round(t, 3), d=round(d, 3)))
        frames += [pcm, b"\x00\x00" * int(GAP * sr)]
        t += d + GAP
    total = t - GAP + TAIL
    frames.append(b"\x00\x00" * int(TAIL * sr))
    wav = os.path.join(VOICE_DIR, f"escena_{idx:02d}.wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(frames))
    mp3 = wav.replace(".wav", ".mp3")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", wav,
                    "-ac", "1", "-b:a", "24k", mp3], check=True)
    return caps, round(total, 3), base64.b64encode(open(mp3, "rb").read()).decode()


def main():
    ensure_voice()
    data = []
    for i, sc in enumerate(SCENES):
        caps, total, b64 = build_audio(sc, i)
        data.append(dict(id=sc["id"], short=sc["short"], title=sc["title"], group=sc["group"],
                         caps=caps, dur=total, audio="data:audio/mpeg;base64," + b64))
        print(f"{i:2d} {sc['id']:8s} {total:6.1f} s")
    tpl = open(os.path.join(HERE, "plantilla.html"), encoding="utf-8").read()
    page = tpl.replace("/*__DATOS__*/null", json.dumps(data, ensure_ascii=False))
    open(os.path.join(HERE, "pcia_replanteo.html"), "w", encoding="utf-8").write(page)
    full = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            '</head>\n<body>\n' + page + '\n</body>\n</html>\n')
    open(os.path.join(HERE, "pcia_replanteo_sites.html"), "w", encoding="utf-8").write(full)
    total = sum(s["dur"] for s in data)
    print(f"Total {total / 60:.1f} min · {len(page) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
