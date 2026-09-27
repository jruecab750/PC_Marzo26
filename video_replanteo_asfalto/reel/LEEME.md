# Reel vertical (Instagram) con GALía

1. `node grabar.mjs clips.json`: graba los clips de GALía fotograma a fotograma (1080 × 1920, 30 fps)
   con `PCia.grabar` de las páginas de `../escenas_pcia/` (ajusta las rutas del principio del script).
   Después convierte cada carpeta a vídeo: `ffmpeg -framerate 30 -i <clip>/%04d.png -c:v libx264 -pix_fmt yuv420p clip_<clip>.mp4`.
2. `python3 musica.py`: música original de 30 s (120 bpm, La menor), sintetizada y sin derechos de terceros.
3. `python3 montar_reel.py guion.json`: alterna los tramos (vídeos reales y clips de GALía), recorta a vertical,
   añade rótulos en la zona segura y la música. Cada tramo: `fuente`, `desde`, `dur`, `texto`, `arriba`, `grande`, `centro_x`.

`vista_previa_galia.mp4` es la parte de GALía sola (22 s), a falta de los vídeos del alumnado.
