# PCia replantea el plano 1 · escenas 3D interactivas

Página web con 15 escenas en 3D, con voz y subtítulos. PCia, PCia2 y PCia3 enseñan:
- el compás de cordel: la mano izquierda fija el cordel en el centro y la derecha lo tensa con la tiza anudada;
- la perpendicular en una esquina, con arcos desde el extremo;
- la perpendicular en un punto medio, con arcos iguales;
- los 9 pasos del replanteo del plano 1.

Cada línea se traza en blanco en cuanto tiene marcados sus dos extremos.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `pcia_replanteo_sites.html` | **Documento completo (1,5 MB)** para Google Sites o cualquier web |
| `pcia_replanteo.html` | La misma página, preparada para publicarla como Artifact de Claude |
| `plantilla.html` | Código de la escena 3D (three.js): robots, acciones y cámaras de cada escena |
| `construir.py` | Textos de cada escena y generación de la voz (Piper); monta los dos HTML |

## Uso

- Botones de arriba: saltar a cualquier escena.
- Abajo: anterior, reproducir o pausar, siguiente, repetir, barra de avance (se puede pinchar para saltar), voz sí/no, «Seguir solo» (avance automático) y «Vista» (vuelve a la cámara de la escena).
- En la escena 3D: arrastra para girar la vista y usa la rueda o dos dedos para acercar.
- Teclado: espacio (reproducir o pausar), AvPág/RePág (escena siguiente o anterior).
- Enlace directo a una escena: añade `#paso3` (o `#compas`, `#esquina`, `#medio`, `#plano`, `#paso1`…`#paso9`, `#final`) al final de la dirección.

## Google Sites

1. Abre tu sitio y entra en **Insertar → Insertar → Insertar código**.
2. Abre `pcia_replanteo_sites.html` con un editor de texto (el Bloc de notas vale), copia todo y pégalo.
3. Agranda el recuadro para que ocupe todo el ancho de la página y tenga unos 700 px de alto.

La página carga three.js y las fuentes desde Internet (jsDelivr y Google Fonts). La voz y los subtítulos van dentro del archivo.

Si Google Sites no admite un código tan largo, súbelo a un alojamiento web estático (por ejemplo, GitHub Pages) e insértalo con **Insertar → Por URL**.

## Regenerar tras cambiar textos o escenas

```bash
pip install piper-tts imageio-ffmpeg
python3 construir.py
```
