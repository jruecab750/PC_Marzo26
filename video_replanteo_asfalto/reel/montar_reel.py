# Monta el reel vertical (1080x1920, 30 fps, 30 s): alterna vídeos reales del alumnado con clips de GALía,
# añade rótulos y la música original. Uso: python3 montar_reel.py guion.json
import json, os, subprocess, sys
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont
FF = imageio_ffmpeg.get_ffmpeg_exe(); W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, 'tmp'); os.makedirs(TMP, exist_ok=True)
FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def rotulo(texto, path, arriba=True, grande=False, color=(255, 255, 255), fondo=(255, 107, 26)):
    """PNG transparente con un rótulo en franja naranja (zona segura del reel: ni arriba del todo ni abajo)."""
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FB, 78 if grande else 62)
    palabras, lineas, cur = texto.split(), [], ''
    for p in palabras:
        prueba = (cur + ' ' + p).strip()
        if d.textlength(prueba, font=f) <= W - 180: cur = prueba
        else: lineas.append(cur); cur = p
    lineas.append(cur)
    lh = int(f.size * 1.22); alto = lh * len(lineas) + 50
    y0 = 300 if arriba else H - 520 - alto
    for i, l in enumerate(lineas):
        tw = d.textlength(l, font=f); x = (W - tw) / 2; y = y0 + 25 + i * lh
        d.rounded_rectangle((x - 28, y - 10, x + tw + 28, y + lh - 2), 18, fill=fondo + (235,))
        d.text((x, y), l, font=f, fill=color)
    im.save(path)

def main(guion):
    g = json.load(open(guion))
    partes, filtros, entradas = [], [], []
    for k, tramo in enumerate(g['tramos']):
        src, dur = tramo['fuente'], tramo['dur']
        entradas += ['-ss', str(tramo.get('desde', 0)), '-t', str(dur), '-i', src]
        # recorte a vertical: escala para cubrir 1080x1920 y recorta el centro (o el punto indicado)
        cx = tramo.get('centro_x', 0.5)
        filtros.append(f"[{k}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}:(iw-{W})*{cx}:(ih-{H})/2,fps={FPS},setsar=1,format=yuv420p[v{k}]")
        partes.append(f"[v{k}]")
    n = len(g['tramos'])
    filtros.append(''.join(partes) + f"concat=n={n}:v=1:a=0[vid]")
    # rótulos
    t, ultimo = 0.0, '[vid]'
    idx = n
    for k, tramo in enumerate(g['tramos']):
        if tramo.get('texto'):
            png = os.path.join(TMP, f'rotulo_{k}.png'); rotulo(tramo['texto'], png, tramo.get('arriba', True), tramo.get('grande', False))
            entradas += ['-i', png]
            filtros.append(f"{ultimo}[{idx}:v]overlay=0:0:enable='between(t,{t + 0.15:.2f},{t + tramo['dur'] - 0.1:.2f})'[o{k}]")
            ultimo = f'[o{k}]'; idx += 1
        t += tramo['dur']
    # audio: música + ambiente bajo de los vídeos reales (si lo tienen)
    entradas += ['-i', g['musica']]; mus = idx; idx += 1
    filtros.append(f"[{mus}:a]atrim=0:{t},afade=t=out:st={t - 1.2}:d=1.2,volume=0.9[mus]")
    cmd = [FF, '-y', '-loglevel', 'error', *entradas, '-filter_complex', ';'.join(filtros), '-map', ultimo, '-map', '[mus]',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS),
           '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', g['salida']]
    subprocess.run(cmd, check=True)
    print('OK', g['salida'], f'{t:.1f} s')

if __name__ == '__main__':
    main(sys.argv[1])
