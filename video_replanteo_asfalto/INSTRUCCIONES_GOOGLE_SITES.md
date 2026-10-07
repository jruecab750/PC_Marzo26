# Actualizar la web de replanteo en Google Sites con Claude (navegador)

Web: https://sites.google.com/g.educaand.es/iosonta26/iosonta-replanteo

## Lo que ya está hecho

- El vídeo y los tres PDF están en tu Drive, compartidos con «Cualquier persona con el enlace · Lector» (comprobado).
- `portada_replanteos_sites.html` ya lleva los cuatro enlaces dentro, en el bloque `ENLACES`:
  - vídeo `galia_metodo345.mp4`;
  - «Guia_completa para replanteo_plano 1 JRUEDA.pdf»;
  - «plano 1_para hacer en A4_escala_1-100 JRUEDA.pdf»;
  - «plano_practicas_para hacer en A4_escala_1-100 JRUEDA.pdf».

## Pasos

1. Abre Chrome con tu cuenta de `g.educaand.es`, con la extensión **Claude in Chrome** activa.
2. En claude.ai abre un chat nuevo, **adjunta `portada_replanteos_sites.html`** y pega este mensaje:

```
Necesito que, con Claude in Chrome, actualices mi web de Google Sites:
https://sites.google.com/g.educaand.es/iosonta26/iosonta-replanteo
Soy el profesor Joaquín Rueda y tengo la sesión abierta con permiso de edición.
Hazme antes las preguntas que necesites y no pulses «Publicar» sin enseñarme cómo queda.

Te adjunto portada_replanteos_sites.html: es el código de la portada, ya terminado y con los enlaces
de Drive dentro. No cambies nada del código.

1. Abre el editor de la web (botón del lápiz o «Editar» en sites.google.com) y ve a la página «iosonta-replanteo».
2. Busca el cuadro de código insertado que muestra la portada «GALía replantea en el asfalto».
   Selecciónalo y pulsa el lápiz «Editar código» (o haz doble clic). Borra todo el código antiguo,
   pega el contenido COMPLETO del archivo adjunto y pulsa «Siguiente» → «Insertar».
   Si no existe ese cuadro, créalo con Insertar → Insertar código → «Insertar código».
3. Ajusta el alto del cuadro arrastrando su borde inferior hasta que se vea toda la portada sin barra
   de desplazamiento: tres tarjetas arriba, la tarjeta «Replanteo en papel» y el recuadro «Cómo se usa»
   (unos 1.400 px en ordenador).
4. Pulsa «Vista previa» y comprueba en ordenador y en móvil:
   - la tarjeta «Perpendicular con el 3-4-5» muestra el reproductor del vídeo de Drive;
   - los botones «Guía del replanteo», «Plano 1 · escala 1:100» y «Plano de prácticas · 1:100» están
     encendidos y abren cada PDF en una pestaña nueva;
   - los botones «Abrir» de los planos 1 y 2 siguen funcionando.
5. Enséñame una captura del resultado. Si te digo que está bien, pulsa «Publicar».
```

3. Revisa lo que te enseñe y dale el visto bueno para publicar.

## Si algo falla

- **El vídeo dice «No se puede reproducir»:** Drive todavía está procesando el MP4. Espera unos minutos y recarga.
- **La portada se corta:** sube el alto del cuadro de código en el editor de Sites.
- **Claude no puede pegar el código o tarda mucho:** pégalo tú. Abre el archivo con el Bloc de notas → Ctrl+A → Ctrl+C. En Sites, doble clic en el cuadro → borra → Ctrl+V → «Siguiente» → «Insertar» → «Publicar».
- **Página interactiva del 3-4-5 (opcional):** crea una subpágina «Método 3-4-5», inserta un cuadro de código y pega tú el contenido de `galia_metodo345_sites.html`. Ocupa casi 1 MB, demasiado para que lo pegue Claude. Pásame luego su URL y la enlazo desde la portada.
