# Voz de GALía: qué es y cómo se genera

Instrucciones para usar en un proyecto nuevo **la misma voz** de las escenas de replanteo con GALía.
Puedes pegar este documento a Claude en el proyecto nuevo junto con `voz_galia.py`.

## 1. Qué voz es

| Dato | Valor |
|---|---|
| Programa | **Piper** (síntesis de voz neuronal, libre y local), paquete de Python `piper-tts` (probado con la 1.8.0) |
| Voz | **`es-carlfm-x-low`**: castellano, masculina, un solo locutor |
| Calidad / muestreo | x-low · 16 000 Hz · mono |
| Licencia | Datos de entrenamiento de dominio público (github.com/carlfm01/my-speech-datasets) |
| Descarga | `https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz` (28 MB) → `es-carlfm-x-low.onnx` y `es-carlfm-x-low.onnx.json` |
| Coste | Gratis; funciona sin conexión una vez descargada |

Se descarga de las *releases* de GitHub porque Hugging Face (donde están el resto de voces de Piper) suele estar
bloqueado en los entornos de Claude en la nube.

## 2. Ajustes exactos que usamos

- **Llamada a Piper**: `python3 -m piper -m es-carlfm-x-low.onnx -f frase.wav --sentence-silence 0.3`, con el texto por la entrada estándar.
  Velocidad y entonación por defecto (sin `--length-scale`).
- **Una síntesis por frase** (cada subtítulo), no el guion entero de golpe. Así se conoce la duración real de cada frase
  y la animación o el montaje se sincronizan con la voz.
- **Silencios**: 0,5 s al principio, 0,55 s entre frases y 1,2 s al final.
- **Formato final**: MP3 mono a 24 kb/s (la voz es de 16 kHz; así pesa muy poco y se puede incrustar en un HTML).
  Si se va a montar en vídeo, mejor el WAV.

## 3. Reglas de pronunciación (importantes)

1. **Texto hablado distinto del subtítulo** cuando haga falta: el subtítulo lleva cifras y letras; lo hablado, cómo se dice.
   - Letras de puntos: «a», «be», «ce», «de», «e», «efe», «ge», «hache», «i», «jota», «ka», «ele», «eme uno», «pe», «cu», «erre».
   - Números: «metro y medio» (1,50), «dos metros y medio» (2,50), «uno ochenta» (1,80), «cuatro veinticuatro» (4,24),
     «cincuenta centímetros». Evitar «1,50» tal cual: lo lee «uno coma cincuenta».
   - Nombres: se escribe **GALía** y se dice **«Galía»**; GALía2 → «Galía dos»; PCia → «Pecía».
2. **No empezar con «¡Hola!»** suelto: Piper lo convierte en un chasquido corto y saturado. Decir «Hola, soy Galía…».
3. Frases de una o dos oraciones; mejor comas que paréntesis o guiones.

`voz_galia.py` ya aplica 2 y los nombres; lo demás hay que escribirlo en el guion.

## 4. Uso rápido

```bash
pip install piper-tts imageio-ffmpeg
python3 voz_galia.py "Hola, soy Galía." saludo.mp3
python3 voz_galia.py guion.txt locucion.mp3 --tiempos   # una frase por línea; crea locucion.json con inicio y duración
```

## 5. Petición para Claude en el proyecto nuevo

> Usa la voz de GALía: Piper con la voz `es-carlfm-x-low` (release v0.0.2 de rhasspy/piper en GitHub), una síntesis por
> frase con `--sentence-silence 0.3`, silencios de 0,5 / 0,55 / 1,2 s, MP3 mono a 24 kb/s, y las reglas de pronunciación
> de INSTRUCCIONES_VOZ_GALIA.md. Puedes partir de `voz_galia.py`. Antes de empezar, hazme preguntas aclaratorias.

## 6. Si algún día quieres otra voz

Piper tiene voces femeninas en castellano (por ejemplo `es_ES-sharvard-medium`, con voz de mujer, o `es_MX-claude-high`) en
Hugging Face (`rhasspy/piper-voices`). Si el entorno no puede descargarlas, bájalas tú (archivos `.onnx` y `.onnx.json`),
pártelas en trozos si pesan mucho y súbelas; se usan igual cambiando `VOICE_MODEL` en el script.
