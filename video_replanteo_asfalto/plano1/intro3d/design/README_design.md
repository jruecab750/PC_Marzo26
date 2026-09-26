# Handoff: GalileIA — robot 3D de replanteo en suelo

## Overview
Escena 3D didáctica para FP: un robot flotante original llamado **GalileIA** enseña a replantear planos en el suelo con **tiza**, **cordel/bota de azulete** y **flexómetro**. La escena incluye la solera con el contorno de un tabique replanteado, hueco de puerta, cruces de esquina, triángulo 3‑4‑5 para el ángulo recto, cordel tenso entre dos clavos con la línea azul marcada y la cinta del flexómetro extendida.

## About the Design Files
`Robot Replanteo.html` es una **referencia de diseño en HTML/three.js** (prototipo), no código de producción. La tarea es recrear el modelo en el entorno del proyecto destino (three.js / React Three Fiber / Unity / Blender, etc.) con sus patrones propios. Si no hay entorno, three.js puro con estos mismos primitivos es la opción directa: el código del modelo es reutilizable casi tal cual.

Alternativa sin código: abrir el HTML y pulsar **Download GLB** (conserva jerarquía, nombres, materiales PBR y la textura del nombre) o **OBJ + MTL** (sin textura del nombre).

## Fidelity
**Alta fidelidad** en forma, proporciones, colores y materiales. Todo el modelo es procedural (sin texturas salvo la placa del pecho).

## Convenciones
- Unidades: metros reales, eje Y arriba. Suelo en y = 0 (cara superior de la solera).
- Robot: `robot.position = (0.55, 0.09, 0.35)`, `rotation.y = -0.35`. Flota 9 cm sobre el suelo.
- Todas las mallas y materiales tienen nombre en español (se conservan en OBJ/GLB).
- three.js 0.184.0. Solo se usan primitivas del core (Box, Cylinder, Sphere, Torus, Capsule, Lathe, Extrude) + CanvasTexture.

## Jerarquía (Group `escena_replanteo`)
### `suelo`
- `solera`: Box 3.4 × 0.04 × 2.8, centro y = −0.02.
- Trazos (Box 0.002 de alto, en y = 0.0015; ancho 0.012 salvo indicado):
  - `trazo_tabique_1..4`: rectángulo (−1.3,−1.0) → (1.3,−1.0) → (1.3,0.4) → (−1.3,0.4). Coordenadas (x,z).
  - `trazo_hueco_puerta_a/b`: x = −0.5 y x = 0.3, de z −1.0 a −0.85.
  - `escuadra_345_cateto_3` (1.3,0.4)→(1.3,−0.2); `cateto_4` (1.3,0.4)→(0.5,0.4); `hipotenusa_5` (1.3,−0.2)→(0.5,0.4). Ancho 0.008. (Escala 0.6/0.8/1.0 m.)
  - `marca_x{0..3}_a/b`: aspa de ±0.05 m en cada esquina, ancho 0.01.
  - `linea_azulete_eje`: (−1.55,0.95)→(1.55,0.95), material azul, ancho 0.01.
- `clavo_1/2`: cilindro r 0.005, alto 0.06 en (±1.55, 0, 0.95); `cabeza_clavo_1/2`: cilindro r 0.012, alto 0.004 en y 0.062.
- `cordel`: cilindro r 0.0018 entre los clavos, y = 0.045.
- `bota_de_azulete` (Group, en (1.3, 0.024, 1.12), rotY 0.8π): `carcasa_bota` = Extrude de lágrima (arco r 0.055 de 0.2π a 1.8π + punta a x 0.1), profundidad 0.04, bisel 0.006; `manivela_bota` cilindro r 0.02.

### `robot_repla`
- `cuerpo`: LatheGeometry (64 seg.) de perfil huevo, alto H = 0.66, radio R = 0.27. Para a ∈ [−π/2, π/2] (49 puntos): r = R·cos(a)·(0.86 + 0.14·sin(a)), y = H/2·(1 + sin(a)). Más ancho arriba.
- `placa_galileia`: cilindro abierto concéntrico al cuerpo (radio del perfil a y 0.44 + 0.003), alto 0.085, arco 1.25 rad centrado en +Z. Textura canvas 1024×256: fondo `#111418`, texto “Galile” `#F4F2EE` + “IA” `#3FD4FF`, system‑ui 700 170 px.
- `filete_placa_inf/sup`: toros de arco (tubo 0.004) en y 0.44 ± 0.045, material LED.
- `anillo_cuello`: toro r 0.07, tubo 0.008, y = H + 0.012, material LED.
- `cabeza` (Group): y = H + 0.17, rot (0.18, 0.25, 0), escala (1.15, 0.82, 1). Radio HR = 0.2.
  - `craneo`: esfera HR.
  - `visor`: casquete de esfera HR·1.012, phiStart π/2 − 1.05, phiLength 2.1, thetaStart 1.0, thetaLength 0.95 (banda frontal).
  - `ojo_izquierdo/derecho`: toro semicircular (arco sonrisa) r 0.032, tubo 0.011, en dirección normalizada (±0.38, −0.12, 0.92)·HR·1.03, orientado hacia fuera.
- Brazos flotantes (`brazo_izquierdo` / `brazo_derecho`): pivote en (±0.285, 0.54, 0).
  - Izquierdo (tiza): rot (−1.05, 0, 0.15). Derecho (flexómetro): rot (−0.7, 0, −0.2).
  - `_carcasa`: esfera unitaria escalada (0.055, 0.2, 0.075) en y −0.19. `_puno`: toro r 0.052 naranja en y −0.3. `_mano`: nodo vacío en y −0.37.
- `tiza`: cilindro r 0.011, largo 0.1, en la mano izquierda (y −0.03, rotX 0.5).
- `flexometro` (en mano derecha, pos (0,−0.05,0), rot (0.7,0,0.2)): `carcasa_flexometro` = Extrude de cuadrado 0.15 con esquina redondeada r 0.022, prof. 0.04, bisel 0.008; `tapa_goma_a/b` cilindros r 0.045; `freno_flexometro` box 0.03×0.012×0.02.

### Sueltos en la escena
- `cinta_flexometro_colgante`: box 0.019 × 0.002 desde la boca del flexómetro (punto local (0.07,−0.07,0) de la carcasa en mundo) hasta (1.28, y≈0.0035, 0.32).
- `cinta_flexometro_suelo`: de (1.28, 0.0035, 0.32) a (0.5, 0.0035, 0.38).
- `gancho_flexometro`: box 0.004×0.02×0.022 en (0.498, 0.01, 0.38).
- `marca_cinta_1..15`: rayitas de graduación negras sobre la cinta (cada 5ª más larga).
- `trazo_tiza_en_curso`: trazo de 0.25 m que termina bajo la punta de la tiza.

## Materiales (MeshStandardMaterial)
| nombre | color | roughness | metalness | notas |
|---|---|---|---|---|
| carcasa_blanca | #F4F2EE | 0.28 | 0 | cuerpo, cabeza, brazos |
| visor_negro | #111418 | 0.12 | 0.2 | |
| ojos_led | #3FD4FF | 0.4 | 0 | emissive #3FD4FF, intensidad 1.2 |
| naranja_seguridad | #F26A1B | 0.45 | 0 | puños |
| amarillo_flexometro | #F2C230 | 0.4 | 0 | carcasa y cinta |
| acero | #B8BDC2 | 0.35 | 0.35 | clavos, gancho |
| goma_negra | #2A2A2A | 0.8 | 0 | |
| tiza_blanca | #FAFAF7 | 0.95 | 0 | tiza y trazos |
| azulete_cordel | #2F6FD6 | 0.85 | 0 | cordel, línea, bota |
| solera_hormigon | #B9B4AA | 0.95 | 0 | |
| placa_nombre | #FFFFFF + map | 0.3 | 0 | CanvasTexture sRGB |

## Iluminación / visor
Iluminación de estudio neutra (hemisférica + key + fill), sombra suave en suelo, sin mapa de entorno (por eso metalness ≤ 0.35). Fondo papel cálido. Cámara auto‑encuadrada, OrbitControls, autorotación lenta. Todo esto vive en `three-d-stage.js` y es opcional en el destino.

## Notas
- Diseño original: inspirado en robots flotantes de carcasa blanca, **no** es una réplica de ningún personaje con derechos.
- Coplanares separados ~0.001–0.003 m para evitar z‑fighting.
- Posibles ampliaciones: animar la tiza trazando, el cordel “restallando” y la cinta enrollándose; etiquetas didácticas por herramienta.

## Files
- `Robot Replanteo.html` — escena completa; el modelo está en el `<script type="module">`.
- `three-d-stage.js` — visor/exportador (render, luces, órbita, descarga OBJ/GLB).
