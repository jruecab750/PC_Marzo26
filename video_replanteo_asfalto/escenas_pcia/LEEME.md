# GALía replantea el plano 1 · escenas 3D interactivas

Página web con 21 escenas en 3D, con voz y subtítulos. GALía (naranja), GALía2 (amarilla) y GALía3 (morada) enseñan:
- para qué sirve replantear: un campamento de emergencia (tiendas, hospital de campaña y puesto de mando) en filas perpendiculares a una línea base, distancias de seguridad, anclajes de las carpas y cómo crece un error de ángulo;
- el compás de cordel: la mano izquierda fija el cordel en el centro y la derecha lo tensa con la tiza anudada;
- los métodos para perpendiculares a una línea base por un punto de inicio (menú desplegable «Métodos para perpendiculares»):
  - método 1, «Radios iguales»: arcos de 60° con el mismo radio;
  - método 2, «Dos radios»: dos marcas con un radio corto y arcos iguales con uno mayor;
  - método 3, «3-4-5»: teorema de Pitágoras y semejanza de triángulos, base de las ternas 30-40-50 cm, 1,5-2-2,5 m y 3-4-5 m; después, su uso en el asfalto;
- la técnica del punto medio: arcos desde los dos extremos (se usa para H y para los puntos medios de los pasos 6 a 9);
- las rectas con cordel atirantado: dos robots tensan el cordel y el tercero pasa la tiza en paralelo;
- el paso 0: centrar el replanteo en la zona asignada, comprobando que el dibujo completo cabe sin tocar paredes ni obstáculos;
- los 9 pasos del replanteo del plano 1 (los semicírculos se trazan sin medir el radio: tiza en el extremo y cordel en el centro O).

El flexómetro es azul y su cinta alterna decímetros amarillo oscuro y negros. El cordel es rojo.

Cada línea se traza en blanco en cuanto tiene marcados sus dos extremos. Cada robot tiene un papel fijo, para que el alumnado pueda asumirlo: GALía2 sujeta el centro de los arcos y el cero de la cinta; GALía3 lleva la tiza en los arcos y el extremo de la cinta; GALía dirige y pasa la tiza en las rectas, mientras GALía2 y GALía3 tensan el cordel. La pared de la zona solo aparece en las escenas «Plano 1» y «Paso 0». Los trazos auxiliares (arcos, marcas y rectas de ayuda) los traza siempre un robot. Cada ejercicio de un paso (una perpendicular, un punto medio…) tiene su color; cuando empieza el siguiente, el anterior baja al 50 % y el de antes desaparece.

Los robots andan a paso normal (unos 1,6 m/s). Si necesitan más tiempo para llegar a su sitio, el trazo espera y la voz también: cada frase empieza cuando los robots han terminado lo anterior, así que algunos pasos duran unos segundos más que su narración.


En la consola del navegador, `PCia.revisar()` simula todas las escenas y lista los momentos en que un trazo avanza sin que su robot esté en su sitio.

## Archivos

| Archivo | Para qué sirve |
|---|---|
| `pcia_replanteo_sites.html` | **Documento completo (2,8 MB)** para Google Sites o cualquier web |
| `pcia_replanteo.html` | La misma página, preparada para publicarla como Artifact de Claude |
| `plantilla.html` | Código de la escena 3D (three.js): robots, acciones y cámaras de cada escena |
| `construir.py` | Textos de cada escena y generación de la voz (Piper); monta los dos HTML |

## Uso

- Botones de arriba: saltar a cualquier escena.
- Abajo: anterior, reproducir o pausar, siguiente, repetir, barra de avance (se puede pinchar para saltar), voz sí/no, «Seguir solo» (avance automático) y «Vista» (vuelve a la cámara de la escena).
- Botón de pantalla completa (abajo a la derecha): muy útil en el móvil. Si el navegador no lo permite (iPhone), abre la página en una pestaña nueva.
- En cajas pequeñas (móvil dentro de Google Sites) la ficha de la escena empieza plegada: pulsa «+» para verla.
- En la escena 3D: arrastra para girar la vista y usa la rueda o dos dedos para acercar.
- Teclado: espacio (reproducir o pausar), AvPág/RePág (escena siguiente o anterior).
- Enlace directo a una escena: añade `#paso3` (o `#objetivo`, `#compas`, `#metodo1`, `#metodo2`, `#pitagoras`, `#metodo3`, `#mediatriz`, `#cordel`, `#plano`, `#paso0`, `#paso1`…`#paso9`, `#final`) al final de la dirección.

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

## Plano 2 (fichero aparte)

`python3 construir.py plano2` genera `galia_plano2.html` (Artifact) y `galia_plano2_sites.html` (Google Sites): solo el replanteo del plano 2, sin las escenas de métodos y técnicas. Tiene 13 escenas: Hola, Plano 2, Paso 0 (zona de 10 × 10 m) y pasos 1 a 9, más Final.

- Cuadrado ABCD de 3 × 3 m. Desde cada punto medio sale un trazo con un triángulo rectángulo: abajo, 3 m con cateto de 2 m (en E) hacia la derecha; a la derecha, 2 m con cateto de 2 m (en H) hacia arriba; a la izquierda, 3 m con cateto de 2 m (en P) hacia abajo; arriba, 2 m con cateto de 1,80 m (en el extremo L) hacia la derecha.
- Los arcos miden 1 m o menos y los traza un solo robot, con el cordel en una mano y la tiza en la otra. Así GALía2 y GALía3 trabajan a la vez en dos sitios (perpendiculares en A y B, en los puntos medios y en los triángulos).
- La cinta la llevan GALía2 (cero) y GALía3 (extremo), y las rectas las traza GALía con el cordel tensado por las otras dos.
- Cada trazo y cada triángulo se mide y se traza antes de pasar al siguiente.
