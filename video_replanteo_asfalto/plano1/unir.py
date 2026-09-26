"""Une la escena 3D (intro3d/intro.mp4) con el vídeo del plano 1 y fusiona los subtítulos.

    python3 unir.py   ->  replanteo_plano1_completo.mp4 + .srt
"""
import os
import re
import subprocess

import imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
INTRO, MAIN = os.path.join(HERE, "intro3d", "intro.mp4"), os.path.join(HERE, "replanteo_plano1.mp4")
OUT = os.path.join(HERE, "replanteo_plano1_completo.mp4")


def duration(path):
    info = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", info).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def shift_srt(text, offset, start_index):
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"

    def parse(x):
        h, m, s = x.replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    out = []
    for i, block in enumerate(b for b in text.strip().split("\n\n") if b.strip()):
        lines = block.split("\n")
        a, b = [parse(x.strip()) for x in lines[1].split("-->")]
        out.append(f"{start_index + i}\n{ts(a + offset)} --> {ts(b + offset)}\n" + "\n".join(lines[2:]))
    return out


subprocess.run([FF, "-y", "-loglevel", "error", "-i", INTRO, "-i", MAIN, "-filter_complex",
                "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-movflags", "+faststart", OUT], check=True)
d = duration(INTRO)
intro_srt = shift_srt(open(os.path.join(HERE, "intro3d", "intro.srt"), encoding="utf-8").read(), 0, 1)
main_srt = shift_srt(open(os.path.join(HERE, "replanteo_plano1.srt"), encoding="utf-8").read(), d, len(intro_srt) + 1)
with open(OUT.replace(".mp4", ".srt"), "w", encoding="utf-8") as f:
    f.write("\n\n".join(intro_srt + main_srt) + "\n")
print("OK", OUT, f"(escena 3D {d:.1f} s + plano 1 {duration(MAIN):.1f} s)")
