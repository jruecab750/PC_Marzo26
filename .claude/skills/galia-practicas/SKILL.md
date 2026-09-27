---
name: galia-practicas
description: Crea prácticas nuevas de Intervención Operativa (IOSONTA, profesor Joaquín Rueda, IES Galileo Galilei) como escenas 3D interactivas con voz, con la estética y los robots GALía, GALía2 y GALía3. Úsala cuando se pida «haz con GALía la práctica de…», «otra práctica con GALía», «nuevo replanteo/plano con GALía», o cambiar las páginas de replanteo existentes.
---

# Prácticas con GALía

Páginas web (un solo HTML) con escenas 3D en three.js, voz en castellano y subtítulos, que el
profesor pega en Google Sites (**Insertar → Insertar código**) y publica como Artifact de Claude.
El código vive en `video_replanteo_asfalto/escenas_pcia/`:

| Archivo | Qué es |
|---|---|
| `plantilla.html` | Motor 3D común: robots, herramientas, acciones, horario, reproductor, interfaz |
| `construir.py` | Textos (subtítulo + texto hablado) de cada escena, voz Piper y montaje de los HTML |
| `LEEME.md` | Uso para el profesor (Google Sites, enlaces directos, regenerar) |
| `pcia_replanteo*.html` | Plano 1 (21 escenas, con técnicas). `python3 construir.py` |
| `galia_plano2*.html` | Plano 2 (13 escenas, solo replanteo). `python3 construir.py plano2` |
| `portada_replanteos_sites.html` | Portada ligera con enlaces a los artefactos y a los HTML en Drive |

Cada página sale en dos versiones: `nombre.html` (se publica como Artifact, mismo `file_path` para
conservar la URL) y `nombre_sites.html` (documento completo para Google Sites).

## Antes de empezar: preguntar

El profesor quiere **preguntas aclaratorias antes de trabajar**. Confirma siempre: lectura del
plano o procedimiento (resume medidas y posiciones y pide conformidad), escenas que lleva, zona
de trabajo del paso 0, métodos por perpendicular, y si es fichero nuevo o cambio de uno existente.

## Estética (no cambiar sin que lo pida)

- Fondo asfalto oscuro, interfaz oscura: `--bg #15181b`, paneles `#1c2125`, naranja Protección Civil
  `#ff6b1a`, amarillo cinta `#f2c230`, verde OK `#5ce39a`, cian `#3fd4ff`.
- Tipos: Barlow Condensed (títulos), Atkinson Hyperlegible (texto), JetBrains Mono (fórmulas).
- Arriba: marca **GALía** + título; chips de escenas por grupos; menú desplegable para grupos largos.
  Ficha a la izquierda (etiqueta, título, viñetas, fórmula, minimapa del plano). Subtítulos abajo.
  Controles: anterior, reproducir, siguiente, repetir, barra, voz, «Seguir solo», «Vista», pantalla completa.
- Adaptada a móvil (Google Sites encoge el recuadro a ~350 × 260 px): controles en una fila, ficha plegada.
- Robots (diseño estilo EVE, levitan, pulgar y dos dedos, sin pulseras): **GALía** naranja `#ff5f14`,
  **GALía2** amarilla `#ffc21a`, **GALía3** morada `#8a4fd8`; nombre en la placa del pecho.
  Se escribe «GALía» y la voz dice «Galía» (`construir.py` lo sustituye). En la presentación no se
  dice «la amarilla / la morada».
- Material: cordel rojo `#ff1a0f`, tiza cilíndrica blanca anudada, flexómetro azul `#1f5fd1` con cinta
  de decímetros amarillo oscuro y negro. Trazos definitivos en **blanco**.

## Reglas didácticas (aprendidas con el profesor; respétalas)

1. **Papeles fijos** (el alumnado asume uno): GALía2 sujeta el centro de los arcos y el cero de la
   cinta; GALía3 lleva la tiza en los arcos y el extremo de la cinta; GALía dirige y traza las rectas
   mientras GALía2 y GALía3 tensan el cordel. No intercambiar papeles «para ahorrar pasos».
2. **Arcos de ~1 m o menos los traza un solo robot** (`solo: 'p2'`): una mano en el centro, la otra con
   la tiza. Así dos robots trabajan a la vez en dos sitios. Arcos mayores: equipo (`crew`).
3. **Todo trazo lo hace un robot**. Nada se dibuja solo (salvo líneas «dadas»: línea base de una
   demostración, borde de zona, que aparecen de golpe).
4. **Auxiliares**: cada ejercicio (una perpendicular, un punto medio…) con su color; al empezar el
   siguiente, el anterior baja al 50 % y el de antes desaparece. Envolver cada ejercicio en `EX([...])`;
   ejercicios en paralelo, en el mismo `EX`.
5. **Técnica del punto medio**: con GALía2 fija en un extremo, GALía3 marca los arcos **a los dos lados**
   antes de cambiar al otro extremo. La recta de los cruces ya es la perpendicular por el punto medio
   (no repetir otra perpendicular ahí; se mide sobre ella).
6. **Semicírculos sin medir el radio**: tiza en el extremo del diámetro y cordel en el centro O.
7. **Métodos**: esquinas y extremos → radios iguales (60°); puntos intermedios → dos radios; 3-4-5 con
   ternas 30-40-50 cm, 1,5-2-2,5 m y 3-4-5 m (Pitágoras y semejanza).
8. **Orden de trabajo**: cada parte (lado, trazo, triángulo) se mide y se traza antes de pasar a la
   siguiente; nada de cruzar el dibujo varias veces.
9. **Paso 0**: centrar el replanteo en la zona dada (margen = (zona − dibujo) ÷ 2) para que no molesten
   pared u obstáculos. La pared solo se ve en «Plano» y «Paso 0».
10. **Voz y dibujo a la par**: la voz espera a los robots (las escenas pueden durar más que la narración).

## Cómo se construye una práctica nueva

1. **Geometría** (`plantilla.html`): un objeto `GEOn` como `GEO2` (puntos, `polys` de relleno con color,
   `lines` sueltas, `segs` del minimapa, `labels`, `mini`, `dims` de cotas, `zone`). Elegir con `PLAN_ID`.
2. **Escenas** (`plantilla.html`): un objeto `DEFSn` como `DEFS2`. Cada escena `id: at => ({ cam, idle,
   acts, panel, plan?, site?, overlay?, fills? })`. `at(k, f)` = instante dentro de la frase k
   (0 inicio, 1 final). Ayudas: `tape`, `mark`, `lineAct`, `dosRadios`, `radiosIguales`, `win` (ventanas
   seguidas), `perpEqual`, `midAct`, `semiNoMeasure`, `EX`. `cam = [x, y, altura, destinoX, destinoY, destinoAltura]`.
   Para que `buildScenes` use el nuevo `DEFSn`, añadirlo junto a `DEFS2` en la selección por `PLAN_ID`.
3. **Textos** (`construir.py`): lista `SCENESn` con `(subtítulo, hablado)`; el hablado escribe letras y
   números como se dicen («eme uno», «metro y medio», «Galía dos»). Evitar «¡Hola!» al inicio del audio
   (Piper lo convierte en un chasquido): hablado «Hola, soy Galía…». Añadir la opción en `main()`.
4. **Construir**: `pip install piper-tts imageio-ffmpeg` y `python3 construir.py <opción>`. La voz
   `es-carlfm-x-low` se descarga de las releases de GitHub de rhasspy/piper (Hugging Face suele estar
   bloqueado). Cada frase se sintetiza aparte y marca los tiempos de la animación.
5. **Probar** (copiar `scripts/probar.mjs` a la carpeta): capturas de escenas clave en escritorio y
   móvil (`VW=350 VH=260`, `VW=390 VH=640`) y `REVISAR=1` hasta que no queden trazos sin robot.
   En consola del navegador: `PCia.revisar()`, `PCia.horario('paso3')`, `PCia.ir('paso3', 12)`.
6. **Publicar**: Artifact con el mismo `file_path` (conserva la URL; recordar que un artefacto nuevo es
   privado hasta que el profesor lo comparta); enviar `*_sites.html`; commit y push.

## Motor: cosas que ya resuelve (no romper)

- `retime()`: horario realista al cargar. Si los robots no llegan andando (~1,6 m/s), retrasa el trazo,
  sus marcas y las frases siguientes de la voz; la tiza nunca va más rápida de lo que anda el robot.
- Prioridad: el trazo en curso manda; los robots libres se quedan donde terminaron y dejan 0,8 m.
- Reproductor: un solo `Audio` reutilizado (en móvil las escenas siguientes suenan solas); dentro de una
  frase el audio marca el tiempo (en móvil la animación va a saltos).
- Varias tizas, cordeles y cintas a la vez (una por robot / pool).
- Tras saltar en el tiempo los robots aparecen en su sitio (`S.snap`).
