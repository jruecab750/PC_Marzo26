# Actualizar la web de replanteo en Google Sites con Claude (navegador)

Web: https://sites.google.com/g.educaand.es/iosonta26/iosonta-replanteo

## 1. Antes, tú (5 minutos)

Claude en el navegador no puede coger archivos de tu ordenador, así que súbelos tú primero a Google Drive:

1. Crea en tu Drive una carpeta, por ejemplo **«Replanteo GALía»**.
2. Sube estos archivos (los tienes en el chat de Claude Code o en GitHub, rama `claude/video-replanteo-asfalto-t3od8w`):
   - `galia_metodo345.mp4` (vídeo del método 3-4-5), carpeta `video_replanteo_asfalto/videos/`
   - `guia_replanteo_plano1.pdf`, `plano1_A4_escala_1-100.pdf`, `plano_practicas_A4_escala_1-100.pdf`, carpeta `video_replanteo_asfalto/pdf_replanteo/`
3. Selecciona la carpeta → **Compartir** → Acceso general: **«Cualquier persona con el enlace» · Lector**.
   Así heredan el permiso los cuatro archivos y el alumnado podrá verlos sin pedir acceso.
4. Ten a mano en el ordenador:
   - `portada_replanteos_sites.html`, de la carpeta `video_replanteo_asfalto/escenas_pcia/`
   - `galia_metodo345_sites.html`, de la misma carpeta. Es la página interactiva del 3-4-5 y es opcional.

## 2. En el chat de Claude

1. Ten instalada y activa la extensión **Claude in Chrome**. Abre Chrome con tu cuenta de `g.educaand.es` y entra una vez en la web de Sites para comprobar que tienes permiso de edición.
2. Abre un chat nuevo en claude.ai y **adjunta `portada_replanteos_sites.html`**.
3. Pega el mensaje del apartado 3, tal cual.

Notas:
- Pegar código muy largo con el navegador es lento. La portada es corta (unos 9 KB) y se puede hacer así.
- La página interactiva del 3-4-5 ocupa casi 1 MB. **Esa pégala tú**: Claude crea la página y el cuadro «Insertar código», y tú pegas el contenido de `galia_metodo345_sites.html` y pulsas «Siguiente» → «Insertar».

## 3. Mensaje para pegar en el chat

```
Necesito que actualices con Claude in Chrome mi web de Google Sites:
https://sites.google.com/g.educaand.es/iosonta26/iosonta-replanteo
(soy el profesor Joaquín Rueda y tengo permiso de edición con la sesión abierta en Chrome).
Antes de empezar, hazme las preguntas que necesites, y no pulses «Publicar» sin mostrarme antes cómo queda.

Te adjunto portada_replanteos_sites.html. Es una portada en HTML que se pega en un cuadro
«Insertar → Insertar código» de Sites. Tareas:

1. En Google Drive, abre mi carpeta «Replanteo GALía» y copia el enlace para compartir de estos archivos:
   galia_metodo345.mp4, guia_replanteo_plano1.pdf, plano1_A4_escala_1-100.pdf y plano_practicas_A4_escala_1-100.pdf.
   Comprueba que la carpeta está compartida como «Cualquier persona con el enlace · Lector».

2. En el archivo adjunto, dentro del bloque `const ENLACES = { ... }` del final, rellena entre las comillas:
   - p3_video: enlace del MP4
   - pdf_guia: enlace de guia_replanteo_plano1.pdf
   - pdf_plano1: enlace de plano1_A4_escala_1-100.pdf
   - pdf_practicas: enlace de plano_practicas_A4_escala_1-100.pdf
   No toques nada más del código. Enséñame el bloque ENLACES ya relleno.

3. En el editor de Sites, en la página «iosonta-replanteo», busca el cuadro de código insertado que tiene
   la portada «GALía replantea en el asfalto». Ábrelo con doble clic (o con el lápiz de «Editar código»),
   borra todo el código antiguo, pega el código nuevo completo (con los enlaces) y pulsa «Siguiente» → «Insertar».
   Si no hay ningún cuadro, créalo con Insertar → Insertar código. Ajusta su alto para que se vea entero
   sin barra de desplazamiento (unos 1.400 px en ordenador).

4. (Opcional, pregúntame antes) Crea una subpágina «Método 3-4-5» bajo «iosonta-replanteo» con:
   - el vídeo con Insertar → Drive → galia_metodo345.mp4, a todo el ancho;
   - debajo, un cuadro «Insertar → Insertar código» vacío y abierto: avísame y pego yo el código
     de galia_metodo345_sites.html, que es muy largo.
   Después pon la URL de esa subpágina en p3_web del bloque ENLACES (paso 2) y vuelve a pegar la portada (paso 3).

5. Antes de publicar, usa «Vista previa» en ordenador y en móvil y comprueba:
   - el vídeo se ve dentro de la tarjeta «Perpendicular con el 3-4-5»;
   - los tres botones de PDF están encendidos y abren el PDF;
   - los botones «Abrir» de los planos 1 y 2 siguen funcionando.
   Enséñame el resultado y, si te digo que sí, pulsa «Publicar».
```

## 4. Si algo falla

- **El vídeo sale con «No se puede reproducir» o pide acceso:** el MP4 no está compartido con «Cualquier persona con el enlace», o Drive aún lo está procesando. Espera unos minutos tras subirlo.
- **Un botón de PDF sale apagado:** su enlace está vacío en `ENLACES`.
- **La portada se corta:** sube el alto del cuadro de código en Sites.
- **Sin la extensión del navegador:** pídele a Claude solo los pasos 1 y 2. Te devolverá el código con los enlaces y lo pegas tú en Sites (doble clic en el cuadro → borrar → pegar → «Siguiente» → «Insertar» → «Publicar»).
