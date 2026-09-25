# Vídeo: Replanteo sobre asfalto (rectángulo + triángulos)

**Duración:** 3 min 57 s · 1920×1080 · locución en español + subtítulos incrustados + `replanteo_asfalto.srt`

**Voz:** Piper TTS, voz `es-carlfm-x-low` (dominio público), generada sin conexión. El script la descarga de GitHub la primera vez.
Cada subtítulo tiene una versión hablada con los números y las letras escritos como se pronuncian. Si una frase no cabe en su escena, la escena se alarga.

## Plano de ejemplo (cotas en metros)

| Figura | Datos | Vértices |
|---|---|---|
| Rectángulo ABCD | 6,00 × 4,00 | A(0,0) B(6,0) C(6,4) D(0,4) |
| Triángulo superior DCE | base 6, altura 4 → lados 5,00 | E(3,8) |
| Triángulo lateral BFC | base 4, altura 1,5 → lados 2,50 | F(7,5; 2) |

Diagonales del rectángulo: √(6² + 4²) = 7,21 m. Tolerancia propuesta: ±2 cm.

## Escenas

| Tiempo | Escena | Contenido |
|---|---|---|
| 0:00 | Portada | Título y técnicas: cinta, tiza, cordel, 3-4-5, Pitágoras |
| 0:10 | El plano | Dibujo acotado del rectángulo y los dos triángulos |
| 0:26 | Material y equipo | Cinta de 20 m, tiza/spray, cordel, calculadora; grupo de 3 (cero · tensa/lee · marca) |
| 0:42 | Antes de empezar | Zona limpia, señalizada y sin tráfico |
| 0:50 | Paso 1 | Línea base AB = 6,00 m |
| 1:08 | Paso 2 | Ángulo recto en A con la regla 3-4-5 (P a 3 m, arcos de 4 y 5 m → D) |
| 1:44 | Paso 3 | Arcos de 4 m desde B y de 6 m desde D → C |
| 2:00 | Paso 4 | Comprobación de diagonales AC = BD = 7,21 m |
| 2:20 | Paso 5 | Arcos de 5 m desde D y C → E; comprobación ME = 4,00 m |
| 3:10 | Paso 6 | Arcos de 2,5 m desde B y C → F; comprobación NF = 1,50 m |
| 2:47 | Paso 7 | Trazado con cordel y tiza; se borran los arcos auxiliares |
| 3:28 | Resumen | Claves y error típico |
| 3:48 | Cierre | «¡Ahora os toca a vosotros!» |

## Regenerar o modificar

```bash
pip install pillow numpy imageio-ffmpeg piper-tts
python3 generar_video.py            # vídeo + subtítulos
python3 generar_video.py --preview  # fotogramas de muestra en preview/
```

Las medidas, los textos (subtítulo y versión hablada) y los tiempos están en la sección «guion (línea de tiempo)» de `generar_video.py`.
