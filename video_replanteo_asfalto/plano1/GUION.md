# Vídeo: Replanteo sobre asfalto · Plano 1

**Vídeo completo:** `replanteo_plano1_completo.mp4` = escena 3D inicial (`intro3d/intro.mp4`) + replanteo del plano (`replanteo_plano1.mp4`).

## Escena inicial 3D: el compás de cordel

Robi, un robot con chaleco de Protección Civil, enseña con las manos:
- **El compás:** una tiza cilíndrica anudada al extremo del cordel. La mano izquierda fija el cordel en el centro, pegado al suelo; la derecha tensa el cordel y traza el arco con la tiza.
- **Perpendicular en una esquina:** arcos desde el extremo (puntos 1 → 2 → 3 → 4) y recta de A al 4.
- **Perpendicular en un punto medio:** arcos iguales desde dos puntos a la misma distancia de M.

Se ha hecho con Blender 4 (Eevee), mediante `intro3d/escena_blender.py`.

```bash
cd intro3d
python3 intro.py voz                       # locución + warp.json
blender -b -P escena_blender.py -- --width 1280 --height 720 --samples 12 --step 2
python3 intro.py montar && python3 intro.py srt
cd .. && python3 unir.py                   # vídeo completo + subtítulos
```

En la parte cenital, los arcos se trazan con el compás de cordel (cordel rojo con la tiza en la punta). La cinta métrica solo se usa para medir distancias.

Basado en el «Plano a replantear 1» del documento *P00_A_REPLANTEO TAMAÑO REAL* (IOSONTA, 2º EPC).

**Formato:** 1920×1080 · locución en español (Piper, voz `es-carlfm-x-low`) + subtítulos incrustados + `replanteo_plano1.srt`

## Plano 1 (cotas en metros, origen en A)

| Elemento | Datos | Puntos |
|---|---|---|
| Rectángulo azul ABCD | 2,50 × 3,50 | A(0;0) B(2,5;0) C(2,5;3,5) D(0;3,5) |
| Puntos medios | AB y DC a 1,25 · AD y BC a 1,75 | M1, M2, M3, M4 |
| Triángulo inferior M1-E-B | trazo M1E = 2,00 | E(1,25;−2) |
| Triángulo derecho M2-F-B | trazo M2F = 2,00 | F(4,5;1,75) |
| Triángulo izquierdo M4-J-D | trazo M4J = 2,00 | J(−2;1,75) |
| Triángulo superior M3-G-I | trazo M3G = 2,50; H = mitad de M3G; HI = 2,00 | G(1,25;6) H(1,25;4,75) I(3,25;4,75) |
| Semicírculos | centro en la mitad de M1E (R 1,00), FB y JD (R 1,33), GI (R 1,18) | |

Comprobado con las cotas de SketchUp: radios 100 / 132,9 / 132,9 / 117,9 cm, ancho total 650 cm y alto total 855,4 cm.
Diagonales del rectángulo: √(2,5² + 3,5²) = 4,30 m.

## Métodos

- **Esquinas (A y B): perpendicular en un extremo con arcos.** Arco de radio 1,50 m con centro en la esquina, que corta la base en el punto 1. Con el mismo radio, desde 1 se corta el arco en el punto 2, y desde 2 en el punto 3 (saltos de 60°). Desde 2 y 3 se trazan dos arcos más, que se cortan en el punto 4, a 90°.
- **Puntos medios: arcos iguales.** Dos puntos a 0,75 m a cada lado del punto medio y arcos de 1,50 m desde ambos. El cruce cae en la perpendicular.
- **Líneas en blanco:** cada segmento se traza con tiza blanca en cuanto sus dos extremos están marcados.

## Pasos

1. Línea base AB (2,50 m).
2. Perpendicular en A con arcos → D a 3,50 m.
3. Perpendicular en B con arcos → C a 3,50 m; se trazan BC y DC.
4. Comprobación: DC = 2,50 m y diagonales de 4,30 m.
5. Puntos medios M1–M4.
6. Triángulo inferior (arcos iguales en detalle) y semicírculo R 1,00.
7. Triángulo derecho y semicírculo R 1,33.
8. Triángulo izquierdo y semicírculo R 1,33.
9. Triángulo superior (dos perpendiculares con arcos iguales) y semicírculo R 1,18.

Después vienen el plano terminado coloreado, un resumen de claves y el cierre «¡Ahora os toca a vosotros!».

## Regenerar

```bash
pip install pillow numpy imageio-ffmpeg piper-tts
python3 generar_video_plano1.py --preview   # fotogramas de muestra
python3 generar_video_plano1.py             # vídeo + subtítulos
```
