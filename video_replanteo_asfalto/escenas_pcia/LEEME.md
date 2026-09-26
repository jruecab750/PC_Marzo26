# PCia replantea el plano 1 · escenas 3D interactivas

Página web con 19 escenas en 3D, con voz y subtítulos. PCia (naranja), PCia2 (amarilla) y PCia3 (morada) enseñan:
- el compás de cordel: la mano izquierda fija el cordel en el centro y la derecha lo tensa con la tiza anudada;
- la perpendicular a una línea base por un punto de inicio, con tres métodos:
  - método 1: arcos de 60°;
  - método 2: dos marcas y arcos mayores;
  - método 3: triángulo 3-4-5 y sus ternas semejantes (1,5-2-2,5 m y 30-40-50 cm);
- la perpendicular por el punto medio desconocido: arcos desde los dos extremos;
- las rectas con cordel atirantado: dos robots tensan el cordel y el tercero pasa la tiza en paralelo;
- los 9 pasos del replanteo del plano 1.

La cinta métrica alterna decímetros amarillos y blancos, y el cordel es rojo.

Cada línea se traza en blanco en cuanto tiene marcados sus dos extremos.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `pcia_replanteo_sites.html` | **Documento completo (1,9 MB)** para Google Sites o cualquier web |
| `pcia_replanteo.html` | La misma página, preparada para publicarla como Artifact de Claude |
| `plantilla.html` | Código de la escena 3D (three.js): robots, acciones y cámaras de cada escena |
| `construir.py` | Textos de cada escena y generación de la voz (Piper); monta los dos HTML |

## Uso

- Botones de arriba: saltar a cualquier escena.
- Abajo: anterior, reproducir o pausar, siguiente, repetir, barra de avance (se puede pinchar para saltar), voz sí/no, «Seguir solo» (avance automático) y «Vista» (vuelve a la cámara de la escena).
- En la escena 3D: arrastra para girar la vista y usa la rueda o dos dedos para acercar.
- Teclado: espacio (reproducir o pausar), AvPág/RePág (escena siguiente o anterior).
- Enlace directo a una escena: añade `#paso3` (o `#compas`, `#metodo1`, `#metodo2`, `#metodo3`, `#mediatriz`, `#cordel`, `#plano`, `#paso1`…`#paso9`, `#final`) al final de la dirección.

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
