"""Construye «GALía · Replanteo del plano 1»: escenas 3D interactivas con voz y subtítulos.

    python3 construir.py
        -> pcia_replanteo.html        (página para publicar como Artifact)
        -> pcia_replanteo_sites.html  (documento HTML completo para Google Sites / un servidor web)

La animación 3D va en plantilla.html (three.js). Aquí están los textos de cada escena y
la locución (Piper, voz es-carlfm-x-low). Cada frase se sintetiza aparte y su inicio y
duración se guardan para que la animación se sincronice con la voz.
"""
import base64
import json
import re
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
    dict(id="inicio", short="Hola", title="Presentación de GALía", group="Inicio", caps=[
        ("¡Hola! Soy GALía, un auxiliar de Protección Civil de Inteligencia Artificial, creado por el profesor Joaquín Rueda para ayudarte con sus prácticas de Intervención Operativa.",
         "Hola, soy Galía, un auxiliar de Protección Civil de Inteligencia Artificial, creado por el profesor Joaquín Rueda para ayudarte con sus prácticas de Intervención Operativa."),
        ("Me ayudan GALía2 y GALía3. Podéis saltar a cualquier escena con los botones de arriba.",
         "Me ayudan Galía dos y Galía tres. Podéis saltar a cualquier escena con los botones de arriba."),
    ]),
    dict(id="objetivo", short="Objetivo", title="¿Para qué sirve replantear?", group="Inicio", caps=[
        ("Imagina una emergencia: hay que montar un campamento con tiendas, un hospital de campaña y un puesto de mando. Todo parte de una línea base.", None),
        ("Las filas y las calles salen perpendiculares a esa línea base. Así se aprovecha el espacio y se circula bien.", None),
        ("Con ángulos rectos, las distancias de seguridad, como los pasillos de evacuación y los cortafuegos, son iguales en todo el campamento.", None),
        ("Y si eres el encargado de anclar las patas de las carpas al suelo, debes conocer el punto exacto de cada anclaje.", None),
        ("Cuidado: un ángulo mal trazado al principio se desvía más cuanto más lejos llega la fila. Con 5 grados de error, a 9 metros te desvías casi 80 centímetros.",
         "Cuidado: un ángulo mal trazado al principio se desvía más cuanto más lejos llega la fila. Con cinco grados de error, a nueve metros te desvías casi ochenta centímetros."),
        ("En una emergencia puede que no haya estación total ni escuadra grande. Con cordel, tiza y cinta métrica se replantea en cualquier sitio.", None),
        ("Para practicarlo, replantearemos el plano 1: un rectángulo con triángulos y semicírculos. Primero, las técnicas; después, el plano paso a paso.",
         "Para practicarlo, replantearemos el plano uno: un rectángulo con triángulos y semicírculos. Primero, las técnicas; después, el plano paso a paso."),
    ]),
    dict(id="compas", short="Compás", title="El compás de cordel", group="Técnicas", caps=[
        ("Atamos una tiza cilíndrica al extremo del cordel con un nudo firme. Este es nuestro compás.", None),
        ("La mano izquierda sujeta el cordel en el centro, pegado al suelo, y no se mueve.", None),
        ("La derecha tensa el cordel y, sin aflojar, gira marcando el arco con la tiza. El radio es el cordel entre las dos manos.", None),
    ]),
    dict(id="metodo1", short="Radios iguales", title="Método de radios iguales", group="Métodos para perpendiculares", caps=[
        ("Perpendicular a una línea base por el punto de inicio. Método de radios iguales: todos los arcos con el mismo radio. Mano izquierda en el punto de inicio A: arco que corta la línea en el punto 1.",
         "Perpendicular a una línea base por el punto de inicio. Método de radios iguales: todos los arcos con el mismo radio. Mano izquierda en el punto de inicio a: arco que corta la línea en el punto uno."),
        ("Sin cambiar el radio, centro en 1: cortamos el arco en el punto 2. Centro en 2: cortamos en el 3.",
         "Sin cambiar el radio, centro en uno: cortamos el arco en el punto dos. Centro en dos: cortamos en el tres."),
        ("Desde el 2 y desde el 3, dos arcos más. Se cruzan en el punto 4.",
         "Desde el dos y desde el tres, dos arcos más. Se cruzan en el punto cuatro."),
        ("Tensamos el cordel desde A pasando por el 4 y marcamos la recta: ¡ángulo recto! Sirve en el extremo de la línea, sin prolongarla.",
         "Tensamos el cordel desde a, pasando por el cuatro, y marcamos la recta: ¡ángulo recto! Sirve en el extremo de la línea, sin prolongarla."),
    ]),
    dict(id="metodo2", short="Dos radios", title="Método de dos radios", group="Métodos para perpendiculares", caps=[
        ("Método de dos radios. Primer radio: con centro en el punto de inicio M y un radio corto, hacemos dos marcas en la línea base, una a cada lado.",
         "Método de dos radios. Primer radio: con centro en el punto de inicio eme y un radio corto, hacemos dos marcas en la línea base, una a cada lado."),
        ("Segundo radio, mayor: un arco desde cada marca. Donde se cruzan está la perpendicular.", None),
        ("Unimos el cruce con el punto de inicio M: esa es la vertical.",
         "Unimos el cruce con el punto de inicio eme: esa es la vertical."),
    ]),
    dict(id="pitagoras", short="3-4-5 · Pitágoras", title="Método 3-4-5: Pitágoras y semejanza", group="Métodos para perpendiculares", caps=[
        ("El método 3-4-5 se basa en el teorema de Pitágoras: en un triángulo rectángulo, el cuadrado de la hipotenusa es igual a la suma de los cuadrados de los catetos.", None),
        ("Con lados 3, 4 y 5: 3 al cuadrado son 9 cuadraditos, 4 al cuadrado son 16, y 9 más 16 son 25, que es 5 al cuadrado. Por eso el triángulo 3-4-5 tiene un ángulo recto.",
         "Con lados tres, cuatro y cinco: tres al cuadrado son nueve cuadraditos, cuatro al cuadrado son dieciséis, y nueve más dieciséis son veinticinco, que es cinco al cuadrado. Por eso el triángulo tres, cuatro, cinco tiene un ángulo recto."),
        ("Semejanza de triángulos: si multiplicamos los tres lados por el mismo número, el triángulo cambia de tamaño pero no de forma. Sus ángulos no cambian y el ángulo recto se mantiene.", None),
        ("Por eso valen 30-40-50 centímetros, 1,5-2-2,5 metros o 3-4-5 metros: son triángulos semejantes. Son las ternas que usaremos, según el espacio que tengamos.",
         "Por eso valen treinta, cuarenta y cincuenta centímetros; uno y medio, dos y dos y medio metros; o tres, cuatro y cinco metros: son triángulos semejantes. Son las ternas que usaremos, según el espacio que tengamos."),
    ]),
    dict(id="metodo3", short="3-4-5 · En el asfalto", title="Método 3-4-5 en el asfalto", group="Métodos para perpendiculares", caps=[
        ("Ahora, en el asfalto. Usamos la terna 1,5-2-2,5 metros, semejante a 3-4-5.",
         "Ahora, en el asfalto. Usamos la terna uno y medio, dos, dos y medio metros, semejante a tres, cuatro, cinco."),
        ("Desde el punto de inicio A, GALía2 y GALía3 miden 1,5 metros sobre la línea base y marcan.",
         "Desde el punto de inicio a, Galía dos y Galía tres miden metro y medio sobre la línea base, y marcan."),
        ("Arco de 2 metros con centro en A y arco de 2,5 metros con centro en la marca. Donde se cruzan está la perpendicular.",
         "Arco de dos metros con centro en a, y arco de dos metros y medio con centro en la marca. Donde se cruzan está la perpendicular."),
        ("Comprobación: 1,5² + 2² = 2,25 + 4 = 6,25 = 2,5². ¡Ángulo recto!",
         "Comprobación: uno y medio al cuadrado, más dos al cuadrado, da seis coma veinticinco, lo mismo que dos y medio al cuadrado. ¡Ángulo recto!"),
    ]),
    dict(id="mediatriz", short="Punto medio", title="Técnica del punto medio", group="Técnicas", caps=[
        ("¿Y si no conocemos el punto medio? Solo tenemos el segmento de A a B.",
         "¿Y si no conocemos el punto medio? Solo tenemos el segmento de a a be."),
        ("Con un radio mayor que la mitad del segmento, un arco desde A, por arriba y por abajo. Con el mismo radio, otro arco desde B.",
         "Con un radio mayor que la mitad del segmento, un arco desde a, por arriba y por abajo. Con el mismo radio, otro arco desde be."),
        ("Los arcos se cruzan en dos puntos. La recta que los une es perpendicular al segmento y lo corta justo en su punto medio M. Es la técnica del punto medio.",
         "Los arcos se cruzan en dos puntos. La recta que los une es perpendicular al segmento, y lo corta justo en su punto medio, eme. Es la técnica del punto medio."),
    ]),
    dict(id="cordel", short="Cordel", title="Trazar rectas con el cordel atirantado", group="Técnicas", caps=[
        ("Para trazar una recta usamos el cordel atirantado: GALía2 y GALía3 lo tensan pegado al suelo entre las dos marcas.",
         "Para trazar una recta usamos el cordel atirantado: Galía dos y Galía tres lo tensan pegado al suelo entre las dos marcas."),
        ("GALía pasa la tiza por el borde del cordel, en paralelo y sin moverlo, de un extremo al otro.",
         "Galía pasa la tiza por el borde del cordel, en paralelo y sin moverlo, de un extremo al otro."),
        ("Así la línea sale recta y en su sitio. En el plano lo haremos cada vez que una línea tenga sus dos extremos marcados.", None),
    ]),
    dict(id="plano", short="Plano 1", title="El plano 1", group="Plano 1", caps=[
        ("Este es el plano 1: un rectángulo de 2,50 por 3,50 metros con un triángulo rectángulo en cada lado.",
         "Este es el plano uno: un rectángulo de dos metros y medio por tres y medio, con un triángulo rectángulo en cada lado."),
        ("Cada triángulo sale de un trazo perpendicular desde el punto medio del lado y lleva un semicírculo con el centro en la mitad de uno de sus lados.", None),
        ("Material: cinta métrica, cordel con tiza atada y calculadora. Zona limpia, señalizada y sin tráfico.", None),
    ]),
    dict(id="paso0", short="Paso 0", title="Paso 0 · Centrar el replanteo en la zona", group="Plano 1", caps=[
        ("Paso 0: antes de dibujar, centramos el replanteo en la zona que nos dan. Así evitamos que, una vez dibujado, nos moleste una pared o un objeto.",
         "Paso cero: antes de dibujar, centramos el replanteo en la zona que nos dan. Así evitamos que, una vez dibujado, nos moleste una pared o un objeto."),
        ("Medimos la zona: 9 por 10,5 metros. El dibujo completo, con los semicírculos, ocupa 7,16 por 8,55 metros. Cabe.",
         "Medimos la zona: nueve por diez metros y medio. El dibujo completo, con los semicírculos, ocupa siete dieciséis por ocho cincuenta y cinco. Cabe."),
        ("Repartimos lo que sobra a partes iguales: unos 92 centímetros a cada lado y unos 98 arriba y abajo.",
         "Repartimos lo que sobra a partes iguales: unos noventa y dos centímetros a cada lado, y unos noventa y ocho arriba y abajo."),
        ("Así el punto A queda a 3,25 metros del borde izquierdo y a 2,98 del borde de abajo. Desde ahí empieza todo el replanteo.",
         "Así el punto a queda a tres veinticinco del borde izquierdo, y a dos noventa y ocho del borde de abajo. Desde ahí empieza todo el replanteo."),
    ]),
    dict(id="paso1", short="Paso 1", title="Paso 1 · Línea base AB", group="Plano 1", caps=[
        ("Paso 1: la línea base. GALía2 sujeta el cero de la cinta en A y GALía3 marca B a 2,50 metros.",
         "Paso uno: la línea base. Galía dos sujeta el cero de la cinta en a, y Galía tres marca be, a dos metros y medio."),
        ("Con los dos extremos marcados, tensamos el cordel y GALía traza AB en blanco.",
         "Con los dos extremos marcados, tensamos el cordel, y Galía traza a be en blanco."),
    ]),
    dict(id="paso2", short="Paso 2", title="Paso 2 · Perpendicular en A", group="Plano 1", caps=[
        ("Paso 2: perpendicular en A con el método de radios iguales. GALía2 fija el cordel en A y GALía3 traza un arco de 1,50 metros que corta la base: punto 1.",
         "Paso dos: perpendicular en a con el método de radios iguales. Galía dos fija el cordel en a, y Galía tres traza un arco de metro y medio que corta la base: punto uno."),
        ("Sin cambiar la medida, desde el punto 1 cortamos el arco en el punto 2, y desde el 2, en el punto 3.",
         "Sin cambiar la medida, desde el punto uno cortamos el arco en el punto dos, y desde el dos, en el punto tres."),
        ("Ahora, desde el 2 y desde el 3, dos arcos más de 1,50 metros. Se cruzan en el punto 4.",
         "Ahora, desde el dos y desde el tres, dos arcos más de metro y medio. Se cruzan en el punto cuatro."),
        ("La recta de A al punto 4 es perpendicular a la base. Por ella medimos 3,50 metros, marcamos D y trazamos AD en blanco.",
         "La recta de a al punto cuatro es perpendicular a la base. Por ella medimos tres metros y medio, marcamos de, y trazamos a de en blanco."),
    ]),
    dict(id="paso3", short="Paso 3", title="Paso 3 · Perpendicular en B y cierre", group="Plano 1", caps=[
        ("Paso 3: repetimos el método de radios iguales en B. Arco de 1,50 metros con centro en B: punto 1. Desde el 1, punto 2, y desde el 2, punto 3.",
         "Paso tres: repetimos el método de radios iguales en be. Arco de metro y medio con centro en be: punto uno. Desde el uno, punto dos, y desde el dos, punto tres."),
        ("Desde el 2 y desde el 3, dos arcos más. Se cruzan en el punto 4.",
         "Desde el dos y desde el tres, dos arcos más. Se cruzan en el punto cuatro."),
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
        ("Paso 6: triángulo de abajo. En M1 usamos el método de dos radios: con el cordel a 75 centímetros, dos marcas en la línea, una a cada lado.",
         "Paso seis: triángulo de abajo. En eme uno usamos el método de dos radios: con el cordel a setenta y cinco centímetros, dos marcas en la línea, una a cada lado."),
        ("Desde cada marca, un arco mayor, de 1,50 metros, hacia fuera. Donde se cruzan, punto 3: está en la perpendicular.",
         "Desde cada marca, un arco mayor, de metro y medio, hacia fuera. Donde se cruzan, punto tres: está en la perpendicular."),
        ("Desde M1, pasando por el punto 3, medimos 2 metros: es E. Trazamos M1E y EB en blanco.",
         "Desde eme uno, pasando por el punto tres, medimos dos metros: es el punto e. Trazamos eme uno e, y e be, en blanco."),
        ("El centro del semicírculo es el punto medio de M1E. Lo sacamos con la técnica del punto medio: arcos iguales desde M1 y desde E, por los dos lados.",
         "El centro del semicírculo es el punto medio de eme uno e. Lo sacamos con la técnica del punto medio: arcos iguales desde eme uno y desde e, por los dos lados."),
        ("La recta que une los cruces corta M1E en su punto medio: es O, el centro del semicírculo.",
         "La recta que une los cruces corta eme uno e en su punto medio: es o, el centro del semicírculo."),
        ("El radio no se mide: GALía3 pone la tiza en E y GALía2 sujeta el otro extremo del cordel en O. Con el cordel tenso, giramos hasta M1 y marcamos el semicírculo.",
         "El radio no se mide: Galía tres pone la tiza en e, y Galía dos sujeta el otro extremo del cordel en o. Con el cordel tenso, giramos hasta eme uno y marcamos el semicírculo."),
    ]),
    dict(id="paso7", short="Paso 7", title="Paso 7 · Triángulo derecho", group="Plano 1", caps=[
        ("Paso 7: triángulo de la derecha. Método de dos radios en M2: dos marcas a 75 centímetros y arcos mayores de 1,50.",
         "Paso siete: triángulo de la derecha. Método de dos radios en eme dos: dos marcas a setenta y cinco centímetros, y arcos mayores de metro y medio."),
        ("Por el cruce, 2 metros hasta F. Trazamos M2F y FB en blanco.",
         "Por el cruce, dos metros hasta efe. Trazamos eme dos efe, y efe be, en blanco."),
        ("Aquí el semicírculo va sobre FB, que mide 2,66 metros. Su centro es el punto medio de FB: técnica del punto medio, con arcos iguales desde F y desde B.",
         "Aquí el semicírculo va sobre efe be, que mide dos sesenta y seis. Su centro es el punto medio de efe be: técnica del punto medio, con arcos iguales desde efe y desde be."),
        ("Donde la recta de los cruces corta FB está O, el centro del semicírculo.",
         "Donde la recta de los cruces corta efe be está o, el centro del semicírculo."),
        ("Sin medir el radio: GALía3 pone la tiza en F y GALía2 sujeta el otro extremo del cordel en O. Con el cordel tenso, giramos hasta B.",
         "Sin medir el radio: Galía tres pone la tiza en efe, y Galía dos sujeta el otro extremo del cordel en o. Con el cordel tenso, giramos hasta be."),
    ]),
    dict(id="paso8", short="Paso 8", title="Paso 8 · Triángulo izquierdo", group="Plano 1", caps=[
        ("Paso 8: triángulo de la izquierda. Igual: método de dos radios desde M4, hacia fuera.",
         "Paso ocho: triángulo de la izquierda. Igual: método de dos radios desde eme cuatro, hacia fuera."),
        ("A 2 metros, el punto J. Trazamos M4J y JD en blanco.",
         "A dos metros, el punto jota. Trazamos eme cuatro jota, y jota de, en blanco."),
        ("El centro del semicírculo es el punto medio entre J y D. Técnica del punto medio: arcos iguales desde J y desde D, por los dos lados.",
         "El centro del semicírculo es el punto medio entre jota y de. Técnica del punto medio: arcos iguales desde jota y desde de, por los dos lados."),
        ("La recta de los cruces corta JD en O, el centro del semicírculo.",
         "La recta de los cruces corta jota de en o, el centro del semicírculo."),
        ("Igual que antes: tiza en J, el otro extremo del cordel en O y, con el cordel tenso, giramos hasta D.",
         "Igual que antes: tiza en jota, el otro extremo del cordel en o y, con el cordel tenso, giramos hasta de."),
    ]),
    dict(id="paso9", short="Paso 9", title="Paso 9 · Triángulo superior", group="Plano 1", caps=[
        ("Paso 9: triángulo de arriba. Método de dos radios en M3, esta vez hacia arriba.",
         "Paso nueve: triángulo de arriba. Método de dos radios en eme tres, esta vez hacia arriba."),
        ("Por el cruce medimos 2,50 metros hasta G y trazamos M3G en blanco.",
         "Por el cruce medimos dos metros y medio hasta ge, y trazamos eme tres ge en blanco."),
        ("Su punto medio H lo sacamos con la técnica del punto medio: arcos iguales desde M3 y desde G. La recta de los cruces corta M3G en H.",
         "Su punto medio, hache, lo sacamos con la técnica del punto medio: arcos iguales desde eme tres y desde ge. La recta de los cruces corta eme tres ge en hache."),
        ("Desde H, otra perpendicular con el método de dos radios, ahora hacia la derecha. A 2 metros, el punto I.",
         "Desde hache, otra perpendicular con el método de dos radios, ahora hacia la derecha. A dos metros, el punto i."),
        ("Trazamos HI, GI e I-M3 en blanco. El centro del semicírculo es el punto medio de GI: otra vez arcos iguales desde G y desde I.",
         "Trazamos hache i, ge i, e i eme tres, en blanco. El centro del semicírculo es el punto medio de ge i: otra vez arcos iguales desde ge y desde i."),
        ("Donde la recta de los cruces corta GI está O, el centro del semicírculo.",
         "Donde la recta de los cruces corta ge i está o, el centro del semicírculo."),
        ("Tiza en G, el otro extremo del cordel en O, y giramos hasta I. El radio sale solo, sin medir: 1,18 metros.",
         "Tiza en ge, el otro extremo del cordel en o, y giramos hasta i. El radio sale solo, sin medir: uno dieciocho."),
    ]),
    dict(id="final", short="Final", title="Plano terminado", group="Plano 1", caps=[
        ("¡Plano terminado! Rectángulo, cuatro triángulos y cuatro semicírculos, todo a tamaño real sobre el asfalto.", None),
        ("Recordad: en una esquina, radios iguales o 3-4-5; en un punto medio, dos radios; y si no conocéis el punto medio, la técnica del punto medio.",
         "Recordad: en una esquina, radios iguales o tres, cuatro, cinco; en un punto medio, dos radios; y si no conocéis el punto medio, la técnica del punto medio."),
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
        sr, pcm = synth((spoken or sub).replace("GALía", "Galía"), os.path.join(VOICE_DIR, f"e{idx:02d}_{k}.wav"))
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
