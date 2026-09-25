"""Genera el vídeo didáctico «Replanteo sobre asfalto: rectángulo + triángulos».

Uso:
    pip install pillow numpy imageio-ffmpeg
    python3 generar_video.py            # vídeo completo -> replanteo_asfalto.mp4 + .srt
    python3 generar_video.py --preview  # solo fotogramas de muestra en ./preview/

Plano de ejemplo (cotas en metros):
    Rectángulo ABCD 6,00 x 4,00  ->  A(0,0) B(6,0) C(6,4) D(0,4)
    Triángulo superior DCE: base 6,00, altura 4,00 -> E(3,8), lados 5,00
    Triángulo lateral BFC:  base 4,00, altura 1,50 -> F(7,5;2), lados 2,50
"""
import math
import os
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1920, 1080, 25
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/dejavu/"

# ---------------------------------------------------------------- estilo
BG_DARK = (22, 27, 38)
PANEL = (32, 38, 52)
CHALK = (246, 244, 232)
TAPE = (250, 204, 21)
ACCENT = (255, 140, 66)
OK = (74, 222, 128)
BLUE = (37, 99, 235)
MUTED = (160, 170, 190)
CREW = [((239, 68, 68), "1"), ((59, 130, 246), "2"), ((34, 197, 94), "3")]

_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        _fonts[key] = ImageFont.truetype(FONT_DIR + name, size)
    return _fonts[key]


# ---------------------------------------------------------------- geometría
FIELD = (0, 70, 1240, 930)  # zona de dibujo (x0, y0, x1, y1)
S, OX, OY = 80, 320, 815  # px por metro y origen del mundo en píxeles

A, B, C, D = (0, 0), (6, 0), (6, 4), (0, 4)
E, FF = (3, 8), (7.5, 2)
P_AUX, M_AUX, N_AUX = (3, 0), (3, 4), (6, 2)


def px(p):
    return (OX + p[0] * S, OY - p[1] * S)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def polar(c, r, deg):
    a = math.radians(deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def fmt_m(v):
    return f"{v:.2f}".replace(".", ",") + " m"


def rgba(col, a):
    return (*col, int(255 * clamp01(a)))


# Comprobaciones del plano (lo que el alumnado debe obtener)
assert abs(dist(A, P_AUX) - 3) < 1e-9 and abs(dist(A, D) - 4) < 1e-9 and abs(dist(P_AUX, D) - 5) < 1e-9
assert abs(dist(B, C) - 4) < 1e-9 and abs(dist(D, C) - 6) < 1e-9
assert abs(dist(D, E) - 5) < 1e-9 and abs(dist(C, E) - 5) < 1e-9
assert abs(dist(B, FF) - 2.5) < 1e-9 and abs(dist(C, FF) - 2.5) < 1e-9
DIAG = dist(A, C)  # 7,21 m


# ---------------------------------------------------------------- utilidades de texto
def wrap(text, fnt, width):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if fnt.getlength(test) <= width or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def shadow_text(d, xy, text, fnt, fill, anchor="la", alpha=1.0):
    x, y = xy
    d.text((x + 2, y + 2), text, font=fnt, fill=(0, 0, 0, int(180 * alpha)), anchor=anchor)
    d.text((x, y), text, font=fnt, fill=rgba(fill, alpha), anchor=anchor)


def label_box(d, center, text, fnt, fg, alpha=1.0, bg=(0, 0, 0)):
    x, y = center
    w = fnt.getlength(text)
    d.rounded_rectangle((x - w / 2 - 10, y - 18, x + w / 2 + 10, y + 18), 8, fill=rgba(bg, 0.78 * alpha))
    d.text((x, y), text, font=fnt, fill=rgba(fg, alpha), anchor="mm")


# ---------------------------------------------------------------- fondos
def make_asphalt():
    w, h = FIELD[2] - FIELD[0], FIELD[3] - FIELD[1]
    rng = np.random.default_rng(7)
    base = np.full((h, w), 62.0)
    low = Image.fromarray(rng.normal(0, 9, (h // 40 + 1, w // 40 + 1)).astype(np.float32), mode="F")
    base += np.asarray(low.resize((w, h), Image.BICUBIC))
    base += rng.normal(0, 11, (h, w))
    speck = rng.random((h, w)) > 0.985
    base[speck] += rng.uniform(25, 60, speck.sum())
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), mode="L").filter(ImageFilter.GaussianBlur(0.7))
    return Image.merge("RGB", (img, img, img.point(lambda v: min(255, v + 4))))


def make_paper():
    w, h = FIELD[2] - FIELD[0], FIELD[3] - FIELD[1]
    img = Image.new("RGB", (w, h), (246, 244, 236))
    d = ImageDraw.Draw(img)
    for i in range(-2, 11):
        x = OX + i * S - FIELD[0]
        d.line((x, 0, x, h), fill=(222, 229, 240), width=1)
    for j in range(-1, 10):
        y = OY - j * S - FIELD[1]
        d.line((0, y, w, y), fill=(222, 229, 240), width=1)
    return img


# ---------------------------------------------------------------- elementos animados
class El:
    def __init__(self, t0, t1=1e9, fade=0.4):
        self.t0, self.t1, self.fade = t0, t1, fade

    def alpha(self, T):
        a = clamp01((T - self.t0) / self.fade) if self.fade else 1.0
        if T > self.t1 - 0.6:
            a = min(a, clamp01((self.t1 - T) / 0.6))
        return a

    def active(self, T):
        return self.t0 <= T < self.t1


class Mark(El):
    """Cruz de tiza sobre el suelo con su nombre."""

    def __init__(self, t0, p, name, off=(-34, 30), aux=False, t1=1e9):
        super().__init__(t0, t1)
        self.p, self.name, self.off, self.aux = p, name, off, aux

    def draw(self, d, T):
        a = self.alpha(T)
        k = 1 + 0.6 * (1 - ease((T - self.t0) / 0.35))
        x, y = px(self.p)
        s = (10 if self.aux else 15) * k
        col = (205, 205, 205) if self.aux else CHALK
        wdt = 3 if self.aux else 5
        d.line((x - s, y - s, x + s, y + s), fill=rgba(col, a), width=wdt)
        d.line((x - s, y + s, x + s, y - s), fill=rgba(col, a), width=wdt)
        if self.name:
            fnt = font(24 if self.aux else 34, True)
            shadow_text(d, (x + self.off[0], y + self.off[1]), self.name, fnt,
                        (200, 200, 200) if self.aux else CHALK, anchor="mm", alpha=a)


class Tape(El):
    """Cinta métrica que se despliega de a hacia b mostrando la lectura."""

    tool = True

    def __init__(self, t0, dur, a, b, hold=1.5, lab_side=1, lab_at=0.5):
        super().__init__(t0, t0 + dur + hold + 0.6, fade=0)
        self.dur, self.a, self.b, self.lab_side, self.lab_at = dur, a, b, lab_side, lab_at
        self.L = dist(a, b)

    def prog(self, T):
        return ease((T - self.t0) / self.dur)

    def tip(self, p):
        return lerp(self.a, self.b, p)

    def crew(self, p):
        u = ((self.b[0] - self.a[0]) / self.L, (self.b[1] - self.a[1]) / self.L)
        n = (-u[1], u[0])
        t = self.tip(p)
        return [(self.a[0] - u[0] * 0.4, self.a[1] - u[1] * 0.4),
                (t[0] + u[0] * 0.4, t[1] + u[1] * 0.4),
                (t[0] - n[0] * 0.5 * self.lab_side, t[1] - n[1] * 0.5 * self.lab_side)]

    def draw(self, d, T):
        a = self.alpha(T)
        p = self.prog(T)
        pa, pt = px(self.a), px(self.tip(p))
        d.line((*pa, *pt), fill=rgba(TAPE, a), width=9)
        ux, uy = (pt[0] - pa[0]), (pt[1] - pa[1])
        ln = math.hypot(ux, uy) or 1
        ux, uy = ux / ln, uy / ln
        for m in range(1, int(self.L * p) + 1):
            q = (pa[0] + ux * m * S, pa[1] + uy * m * S)
            d.line((q[0] - uy * 5, q[1] + ux * 5, q[0] + uy * 5, q[1] - ux * 5), fill=rgba((40, 40, 40), a), width=3)
        d.rectangle((pa[0] - 7, pa[1] - 7, pa[0] + 7, pa[1] + 7), fill=rgba((60, 60, 60), a), outline=rgba(TAPE, a))
        mid = lerp(pa, pt, self.lab_at)
        lab = (mid[0] - uy * 36 * self.lab_side, mid[1] + ux * 36 * self.lab_side)
        label_box(d, lab, fmt_m(self.L * p), font(24, True), TAPE, a)


class Arc(El):
    """Arco trazado con la cinta tensa girando alrededor de un centro."""

    tool = True

    def __init__(self, t0, dur, c, r, a0, a1, t1=1e9):
        super().__init__(t0, t1, fade=0)
        self.dur, self.c, self.r, self.a0, self.a1 = dur, c, r, a0, a1

    def prog(self, T):
        return ease((T - self.t0) / self.dur)

    def tip(self, p):
        return polar(self.c, self.r, self.a0 + (self.a1 - self.a0) * p)

    def crew(self, p):
        t = self.tip(p)
        ux, uy = (t[0] - self.c[0]) / self.r, (t[1] - self.c[1]) / self.r
        return [(self.c[0] - ux * 0.4, self.c[1] - uy * 0.4),
                (t[0] + ux * 0.4, t[1] + uy * 0.4),
                (t[0] - uy * 0.5, t[1] + ux * 0.5)]

    def draw(self, d, T):
        a = self.alpha(T)
        p = self.prog(T)
        span = (self.a1 - self.a0) * p
        n = max(2, int(abs(span) / 0.8))
        pts = [px(polar(self.c, self.r, self.a0 + span * i / n)) for i in range(n + 1)]
        for i in range(len(pts) - 1):
            if (i // 3) % 4 != 3:
                d.line((*pts[i], *pts[i + 1]), fill=rgba((255, 236, 170), 0.9 * a), width=4)
        if T < self.t0 + self.dur + 0.8:
            ta = clamp01((self.t0 + self.dur + 0.8 - T) / 0.4)
            c, t = px(self.c), px(self.tip(p))
            d.line((*c, *t), fill=rgba(TAPE, ta), width=8)
            mid = ((c[0] + t[0]) / 2, (c[1] + t[1]) / 2 - 26)
            label_box(d, mid, "R = " + fmt_m(self.r), font(24, True), TAPE, ta)


class Snap(El):
    """Cordel de replanteo: se tensa, se «pellizca» y deja la línea de tiza."""

    def __init__(self, t0, a, b):
        super().__init__(t0, fade=0)
        self.a, self.b = a, b

    def draw(self, d, T):
        k = T - self.t0
        pa, pb = px(self.a), px(self.b)
        if k < 0.9:
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            lift = 18 * math.sin(clamp01(k / 0.5) * math.pi) if k < 0.5 else 0
            nx, ny = -(pb[1] - pa[1]), (pb[0] - pa[0])
            ln = math.hypot(nx, ny) or 1
            q = (mid[0] + nx / ln * lift, mid[1] + ny / ln * lift)
            d.line((*pa, *q, *pb), fill=(220, 38, 38, 255), width=3)
        if k >= 0.45:
            d.line((*pa, *pb), fill=rgba(CHALK, clamp01((k - 0.45) / 0.25)), width=7)


class PlanLine(El):
    def __init__(self, t0, dur, a, b, col=BLUE, width=5, dashed=False):
        super().__init__(t0, fade=0)
        self.dur, self.a, self.b, self.col, self.width, self.dashed = dur, a, b, col, width, dashed

    def draw(self, d, T):
        p = ease((T - self.t0) / self.dur)
        pa, pb = px(self.a), px(lerp(self.a, self.b, p))
        if not self.dashed:
            d.line((*pa, *pb), fill=self.col, width=self.width)
            return
        L = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
        n = int(L // 14)
        for i in range(0, n, 2):
            d.line((*lerp(pa, pb, i / max(n, 1)), *lerp(pa, pb, (i + 1) / max(n, 1))), fill=self.col, width=self.width)


class Dim(El):
    """Cota de plano: línea con marcas en los extremos y texto."""

    def __init__(self, t0, a, b, text, off, text_off=(0, 0)):
        super().__init__(t0)
        self.a, self.b, self.text, self.off, self.text_off = a, b, text, off, text_off

    def draw(self, d, T):
        al = self.alpha(T)
        pa, pb = px(self.a), px(self.b)
        ox, oy = self.off[0] * S, -self.off[1] * S
        qa, qb = (pa[0] + ox, pa[1] + oy), (pb[0] + ox, pb[1] + oy)
        col = rgba((190, 60, 30), al)
        d.line((*pa, *qa), fill=rgba((190, 60, 30), 0.5 * al), width=1)
        d.line((*pb, *qb), fill=rgba((190, 60, 30), 0.5 * al), width=1)
        d.line((*qa, *qb), fill=col, width=2)
        for q in (qa, qb):
            d.line((q[0] - 7, q[1] + 7, q[0] + 7, q[1] - 7), fill=col, width=3)
        m = ((qa[0] + qb[0]) / 2 + self.text_off[0], (qa[1] + qb[1]) / 2 + self.text_off[1])
        d.text(m, self.text, font=font(26, True), fill=col, anchor="mm")


class Poly(El):
    def __init__(self, t0, pts, col, a=0.3, t1=1e9, outline=None, width=3):
        super().__init__(t0, t1, fade=1.0)
        self.pts, self.col, self.a, self.outline, self.width = pts, col, a, outline, width

    def draw(self, d, T):
        al = self.alpha(T)
        pts = [px(p) for p in self.pts]
        d.polygon(pts, fill=rgba(self.col, self.a * al))
        if self.outline:
            d.line(pts + [pts[0]], fill=rgba(self.outline, al), width=self.width, joint="curve")


class RightAngle(El):
    def __init__(self, t0, t1, corner, u, v, s=0.45):
        super().__init__(t0, t1)
        self.c, self.u, self.v, self.s = corner, u, v, s

    def draw(self, d, T):
        a = self.alpha(T)
        c, s = self.c, self.s
        p1 = (c[0] + self.u[0] * s, c[1] + self.u[1] * s)
        p2 = (p1[0] + self.v[0] * s, p1[1] + self.v[1] * s)
        p3 = (c[0] + self.v[0] * s, c[1] + self.v[1] * s)
        d.line((*px(p1), *px(p2), *px(p3)), fill=rgba(OK, a), width=4)
        d.ellipse((px(c)[0] + (self.u[0] + self.v[0]) * S * 0.22 - 4, px(c)[1] - (self.u[1] + self.v[1]) * S * 0.22 - 4,
                   px(c)[0] + (self.u[0] + self.v[0]) * S * 0.22 + 4, px(c)[1] - (self.u[1] + self.v[1]) * S * 0.22 + 4),
                  fill=rgba(OK, a))


class Seg(El):
    """Segmento de color (p. ej. lados 3-4-5) con etiqueta."""

    def __init__(self, t0, t1, a, b, col, text=None, toff=(0, 0), width=5):
        super().__init__(t0, t1)
        self.a, self.b, self.col, self.text, self.toff, self.width = a, b, col, text, toff, width

    def draw(self, d, T):
        al = self.alpha(T)
        pa, pb = px(self.a), px(self.b)
        d.line((*pa, *pb), fill=rgba(self.col, al), width=self.width)
        if self.text:
            m = ((pa[0] + pb[0]) / 2 + self.toff[0], (pa[1] + pb[1]) / 2 + self.toff[1])
            label_box(d, m, self.text, font(26, True), self.col, al)


class FText(El):
    def __init__(self, t0, t1, xy, text, size=30, col=CHALK, box=True):
        super().__init__(t0, t1)
        self.xy, self.text, self.size, self.col, self.box = xy, text, size, col, box

    def draw(self, d, T):
        a = self.alpha(T)
        fnt = font(self.size, True)
        x, y = self.xy
        if self.box:
            w = fnt.getlength(self.text)
            d.rounded_rectangle((x - w / 2 - 18, y - self.size * 0.8, x + w / 2 + 18, y + self.size * 0.8), 12,
                                fill=(0, 0, 0, int(190 * a)))
        d.text((x, y), self.text, font=fnt, fill=rgba(self.col, a), anchor="mm")


class Materials(El):
    ITEMS = [
        ("cinta", "Cinta métrica de 20 m", "con el cero bien identificado"),
        ("tiza", "Tiza o spray de marcaje", "para cruces, arcos y líneas"),
        ("cordel", "Cordel de replanteo", "para trazar las rectas"),
        ("calc", "Calculadora y el plano", "para calcular los lados con Pitágoras"),
    ]

    def draw(self, d, T):
        a = self.alpha(T)
        d.text((80, 130), "Material", font=font(44, True), fill=rgba((30, 41, 59), a))
        for i, (ico, t1, t2) in enumerate(self.ITEMS):
            ai = a * clamp01((T - self.t0 - 0.6 * i) / 0.5)
            y = 215 + i * 92
            self.icon(d, ico, (115, y + 28), ai)
            d.text((175, y + 4), t1, font=font(32, True), fill=rgba((30, 41, 59), ai))
            d.text((175, y + 44), t2, font=font(24), fill=rgba((71, 85, 105), ai))
        ta = a * clamp01((T - self.t0 - 5.5) / 0.6)
        d.text((80, 610), "Equipo de 3 personas", font=font(40, True), fill=rgba((30, 41, 59), ta))
        roles = ["Sujeta el cero", "Tensa y lee la cinta", "Marca con tiza"]
        for i, ((col, num), role) in enumerate(zip(CREW, roles)):
            ai = ta * clamp01((T - self.t0 - 6 - 0.5 * i) / 0.5)
            x = 120 + i * 370
            draw_person(d, (x, 715), col, num, ai, r=30)
            d.text((x + 45, 715), role, font=font(26, True), fill=rgba((30, 41, 59), ai), anchor="lm")

    @staticmethod
    def icon(d, kind, c, a):
        x, y = c
        if kind == "cinta":
            d.ellipse((x - 30, y - 30, x + 30, y + 30), fill=rgba(TAPE, a), outline=rgba((60, 60, 60), a), width=3)
            d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=rgba((60, 60, 60), a))
            d.rectangle((x + 20, y + 16, x + 52, y + 26), fill=rgba(TAPE, a), outline=rgba((60, 60, 60), a))
        elif kind == "tiza":
            d.rounded_rectangle((x - 34, y - 10, x + 34, y + 10), 6, fill=rgba((255, 255, 255), a),
                                outline=rgba((120, 120, 120), a), width=2)
        elif kind == "cordel":
            pts = [(x - 36 + i * 6, y + 10 * math.sin(i * 0.9)) for i in range(13)]
            d.line(pts, fill=rgba((220, 38, 38), a), width=4)
        else:
            d.rounded_rectangle((x - 24, y - 32, x + 24, y + 32), 6, fill=rgba((51, 65, 85), a))
            d.rectangle((x - 16, y - 24, x + 16, y - 10), fill=rgba((190, 230, 200), a))
            for i in range(3):
                for j in range(3):
                    d.rectangle((x - 16 + i * 12, y - 4 + j * 11, x - 8 + i * 12, y + 3 + j * 11),
                                fill=rgba((226, 232, 240), a))


def draw_person(d, c, col, num, a=1.0, r=17):
    x, y = c
    d.ellipse((x - r + 3, y - r + 4, x + r + 3, y + r + 4), fill=(0, 0, 0, int(110 * a)))
    d.ellipse((x - r, y - r, x + r, y + r), fill=rgba(col, a), outline=rgba((255, 255, 255), a), width=3)
    d.text((x, y), num, font=font(int(r * 1.15), True), fill=rgba((255, 255, 255), a), anchor="mm")


# ---------------------------------------------------------------- guion (línea de tiempo)
EL, CAPS, PANELS = [], [], []


def cap(t0, t1, text):
    CAPS.append((t0, t1, text))


def panel(t0, t1, tag, title, bullets, formula=None, pts=(), segs=()):
    PANELS.append(dict(t0=t0, t1=t1, tag=tag, title=title, bullets=bullets, formula=formula, pts=pts, segs=segs))


TITLE_END, ASPHALT, END_T = 7.0, 34.0, 212.0

# --- El plano (7-22)
for i, (a, b) in enumerate([(A, B), (B, C), (C, D), (D, A)]):
    EL.append(PlanLine(7.5 + 0.8 * i, 0.8, a, b))
EL += [PlanLine(10.7, 0.7, D, E), PlanLine(11.4, 0.7, E, C), PlanLine(12.1, 0.7, B, FF), PlanLine(12.8, 0.7, FF, C)]
for p, nm, off in [(A, "A", (-30, 28)), (B, "B", (26, 28)), (C, "C", (-30, 26)), (D, "D", (-32, -10)),
                   (E, "E", (0, -30)), (FF, "F", (30, 0))]:
    EL.append(FText(13.5, ASPHALT, (px(p)[0] + off[0], px(p)[1] + off[1]), nm, 30, (30, 41, 59), box=False))
EL += [
    Dim(14.2, A, B, "6,00", (0, -0.45), (0, 20)),
    Dim(15.2, A, D, "4,00", (-0.5, 0), (-40, 0)),
    PlanLine(16.2, 0.8, M_AUX, E, (190, 60, 30), 2, dashed=True),
    FText(16.8, ASPHALT, (px(M_AUX)[0] + 50, px(E)[1] + 200), "h = 4,00", 26, (190, 60, 30), box=False),
    PlanLine(17.4, 0.6, N_AUX, FF, (190, 60, 30), 2, dashed=True),
    FText(17.8, ASPHALT, (px(N_AUX)[0] + 68, px(N_AUX)[1] + 26), "h = 1,50", 24, (190, 60, 30), box=False),
    FText(18.8, 22, (170, 110), "Cotas en metros", 24, (100, 116, 139), box=False),
]
cap(7, 14.5, "Este es el plano que vais a llevar al suelo: un rectángulo ABCD de 6 × 4 m con dos triángulos adosados.")
cap(14.5, 22, "Triángulo superior DCE: base 6 m y altura 4 m. Triángulo lateral BFC: base 4 m y altura 1,5 m. Los dos son isósceles.")
panel(7, 22, "EL PLANO", "¿Qué vamos a replantear?",
      ["Rectángulo ABCD: 6,00 × 4,00 m", "Triángulo DCE: base 6 m, altura 4 m",
       "Triángulo BFC: base 4 m, altura 1,5 m", "Replantear = llevar el plano al terreno a escala 1:1"])

for el in EL:
    el.t1 = min(el.t1, 22.4)

# --- Material (22-34)
EL.append(Materials(22.3, 33.6))
cap(22, 28, "Material: cinta métrica de 20 m, tiza o spray de marcaje, cordel de replanteo, calculadora y el plano.")
cap(28, 34, "Trabajad en grupos de tres: uno sujeta el cero, otro tensa y lee la cinta y el tercero marca.")
panel(22, 34, "PREPARACIÓN", "Material y equipo",
      ["Revisa que la cinta no esté doblada ni rota", "Decide antes quién hace cada función",
       "Rotad los papeles en cada figura"])

# --- Al asfalto (34-40)
EL.append(FText(34.5, 39.8, (620, 470), "Vista cenital de la zona de trabajo", 34))
cap(34, 40, "Pasamos al asfalto. Veremos la zona de trabajo desde arriba, como si la grabara un dron.")
panel(34, 40, "ANTES DE EMPEZAR", "Zona de trabajo",
      ["Zona limpia, seca y sin tráfico", "Delimita y señaliza la zona",
       "Deja 1 m de margen alrededor de la figura"])

# --- Paso 1: línea base (40-56)
EL += [Mark(40.5, A, "A"), Tape(42, 4, A, B, hold=2.2), Mark(46.2, B, "B", (30, 30))]
cap(40, 45, "Paso 1 · Línea base. Marcamos el punto A con una cruz de tiza: será el origen de todo el replanteo.")
cap(45, 56, "El alumno 1 sujeta el cero en A, el 2 tensa la cinta hasta 6,00 m y el 3 marca B. AB es la línea base.")
panel(40, 56, "PASO 1 / 7", "Línea base AB",
      ["Marca A con una cruz de unos 10 cm", "El cero de la cinta, en el centro de la cruz",
       "Cinta tensa, recta y pegada al suelo", "Marca B a 6,00 m"], pts=("A", "B"), segs=("AB",))

# --- Paso 2: ángulo recto 3-4-5 (56-88)
EL += [
    Tape(57, 2.5, A, P_AUX, hold=1.0), Mark(59.7, P_AUX, "P", (0, 28), aux=True),
    Arc(61.5, 4, A, 4, 68, 112, t1=180), Arc(66.5, 4, P_AUX, 5, 112, 142, t1=180),
    Mark(71, D, "D", (-34, -8)),
    FText(71.3, 78, (px(D)[0] + 150, px(D)[1] - 60), "D = corte de los dos arcos", 26, TAPE),
    RightAngle(72, 127, A, (1, 0), (0, 1)),
    Seg(73, 87, A, P_AUX, ACCENT, "3 m", (0, 30)),
    Seg(73.8, 87, A, D, ACCENT, "4 m", (-50, 0)),
    Seg(74.6, 87, P_AUX, D, ACCENT, "5 m", (40, -10)),
]
cap(56, 61, "Paso 2 · Ángulo recto con la regla 3-4-5. Desde A medimos 3,00 m sobre la línea base y marcamos el punto auxiliar P.")
cap(61, 70.5, "Con centro en A trazamos un arco de 4,00 m y con centro en P, uno de 5,00 m. La cinta siempre tensa, girando alrededor del centro.")
cap(70.5, 79, "Donde se cortan los dos arcos está D. El triángulo APD mide 3, 4 y 5 m, así que el ángulo en A es recto.")
cap(79, 88, "Truco: haced arcos largos, de unos 30°. Así el corte se ve claro aunque no acertéis la zona a la primera.")
panel(56, 88, "PASO 2 / 7", "Ángulo recto: regla 3-4-5",
      ["Mide 3,00 m sobre AB → punto P", "Arco de 4,00 m con centro en A", "Arco de 5,00 m con centro en P",
       "El corte de los arcos es D"], formula="3² + 4² = 9 + 16 = 25 = 5²", pts=("A", "D"), segs=("DA",))

# --- Paso 3: cerrar el rectángulo (88-104)
EL += [Arc(89, 3.5, B, 4, 72, 108, t1=180), Arc(93.5, 3.5, D, 6, -12, 12, t1=180), Mark(97.5, C, "C", (32, 26))]
cap(88, 97, "Paso 3 · Cerramos el rectángulo. Desde B trazamos un arco de 4,00 m y desde D un arco de 6,00 m.")
cap(97, 104, "El corte de ambos arcos es el punto C. Ya tenemos los cuatro vértices del rectángulo.")
panel(88, 104, "PASO 3 / 7", "Cerrar el rectángulo",
      ["Arco de 4,00 m con centro en B", "Arco de 6,00 m con centro en D", "El corte de los arcos es C"],
      pts=("B", "C", "D"), segs=("BC", "CD"))

# --- Paso 4: diagonales (104-122)
EL += [Tape(105, 3, A, C, hold=7.5, lab_side=-1, lab_at=0.3), Tape(109, 3, B, D, hold=3.5, lab_at=0.3),
       FText(113, 121.5, (px((3, 4))[0], px((3, 4))[1] - 70), "AC = BD = 7,21 m  ✔", 34, OK)]
cap(104, 112, "Paso 4 · Comprobación. En un rectángulo las dos diagonales miden lo mismo: √(6² + 4²) = 7,21 m.")
cap(112, 122, "Si las diagonales difieren más de 2 cm, el ángulo no es recto: revisad los pasos 2 y 3 antes de seguir.")
panel(104, 122, "PASO 4 / 7", "Comprobar las diagonales",
      ["Mide AC y BD", "Deben ser iguales: 7,21 m", "Diferencia > 2 cm → repite el ángulo recto"],
      formula="d = √(6² + 4²) = √52 = 7,21 m", pts=("A", "B", "C", "D"), segs=("AC", "BD"))

# --- Paso 5: triángulo superior (122-146)
EL += [
    Arc(127, 3.5, D, 5, 40, 67, t1=180), Arc(131.5, 3.5, C, 5, 113, 140, t1=180), Mark(135.5, E, "E", (0, -32)),
    Tape(137, 2, D, M_AUX, hold=0.4), Mark(139.2, M_AUX, "M", (0, 26), aux=True),
    Tape(140, 2, M_AUX, E, hold=3, lab_side=-1),
    FText(142.5, 145.8, (px(E)[0] + 210, px(E)[1] + 40), "ME = 4,00 m  ✔", 28, OK),
]
cap(122, 127, "Paso 5 · Triángulo superior. Calculamos sus lados con Pitágoras: la mitad de la base (3 m) y la altura (4 m).")
cap(127, 135.5, "Lado = √(3² + 4²) = 5,00 m. Trazamos un arco de 5,00 m desde D y otro de 5,00 m desde C.")
cap(135.5, 146, "El corte es E. Comprobamos: desde el punto medio M de DC hasta E deben salir 4,00 m.")
panel(122, 146, "PASO 5 / 7", "Triángulo superior DCE",
      ["Arco de 5,00 m con centro en D", "Arco de 5,00 m con centro en C", "El corte es E",
       "Comprueba la altura ME = 4,00 m"], formula="l = √(3² + 4²) = 5,00 m", pts=("D", "C", "E"),
      segs=("DE", "EC"))

# --- Paso 6: triángulo lateral (146-166)
EL += [
    Arc(150, 3, B, 2.5, 38, 68, t1=180), Arc(154, 3, C, 2.5, -68, -38, t1=180), Mark(157.5, FF, "F", (34, 0)),
    Tape(159, 1.5, B, N_AUX, hold=0.4, lab_side=-1), Mark(160.7, N_AUX, "N", (-28, 0), aux=True),
    Tape(161.5, 1.5, N_AUX, FF, hold=3),
    FText(163.2, 165.8, (px(FF)[0] - 30, px(FF)[1] - 150), "NF = 1,50 m  ✔", 28, OK),
]
cap(146, 150, "Paso 6 · Triángulo lateral. Mitad de la base: 2 m; altura: 1,5 m.")
cap(150, 157.5, "Lado = √(2² + 1,5²) = 2,50 m. Arcos de 2,50 m desde B y desde C.")
cap(157.5, 166, "El corte es F. Comprobación: desde el punto medio N de BC hasta F hay 1,50 m.")
panel(146, 166, "PASO 6 / 7", "Triángulo lateral BFC",
      ["Arco de 2,50 m con centro en B", "Arco de 2,50 m con centro en C", "El corte es F",
       "Comprueba la altura NF = 1,50 m"], formula="l = √(2² + 1,5²) = 2,50 m", pts=("B", "C", "F"),
      segs=("BF", "FC"))

# --- Paso 7: trazado con cordel (166-184)
for i, (a, b) in enumerate([(A, B), (B, FF), (FF, C), (C, E), (E, D), (D, A), (D, C), (B, C)]):
    EL.append(Snap(167 + 1.3 * i, a, b))
EL += [Poly(178.5, [A, B, C, D], (59, 130, 246), 0.28, t1=END_T + 1),
       Poly(179, [D, C, E], ACCENT, 0.28, t1=END_T + 1), Poly(179.5, [B, FF, C], ACCENT, 0.28, t1=END_T + 1)]
cap(166, 177, "Paso 7 · Trazado. Tensamos el cordel entre dos marcas, lo levantamos por el centro y lo soltamos: deja una recta perfecta.")
cap(177, 184, "Borramos los arcos auxiliares y ya tenemos el plano replanteado a escala real sobre el asfalto.")
panel(166, 184, "PASO 7 / 7", "Trazar las líneas",
      ["Cordel tenso entre dos cruces", "Levántalo por el centro y suéltalo", "Repasa con tiza si hace falta",
       "Borra los arcos auxiliares"], pts=("A", "B", "C", "D", "E", "F"),
      segs=("AB", "BF", "FC", "CE", "ED", "DA", "CD", "BC"))

# --- Resumen (184-204) y cierre (204-212)
cap(184, 194, "Claves: cinta siempre tensa y sin torsiones, el cero en el centro de la cruz y arcos largos para ver bien los cortes.")
cap(194, 204, "Y comprobad siempre: diagonales iguales en el rectángulo y la altura correcta en cada triángulo. Tolerancia: ±2 cm.")
panel(184, END_T, "RESUMEN", "Claves del replanteo",
      ["✔ Cinta tensa, recta y sin torsiones", "✔ Cero en el centro de la cruz", "✔ Arcos largos (unos 30°)",
       "✔ Diagonales iguales: 7,21 m", "✔ Alturas: 4,00 m y 1,50 m", "✔ Nombra cada punto en el suelo"],
      formula="Error típico: no leer desde el cero real de la cinta")
EL += [FText(204.3, END_T + 1, (620, 430), "¡Ahora os toca a vosotros!", 52, TAPE),
       FText(205, END_T + 1, (620, 520), "Replantead el plano de vuestro grupo · Tolerancia ±2 cm", 30, CHALK)]
cap(204, 211, "Ahora os toca a vosotros: replantead el plano de vuestro grupo.")

TOOLS = sorted([e for e in EL if getattr(e, "tool", False)], key=lambda e: e.t0)

# ---------------------------------------------------------------- equipo (alumnos 1, 2 y 3)
CREW_HOME = [(-0.6, -0.4), (0.2, -0.5), (-0.2, 0.5)]


def crew_positions(T):
    prev = CREW_HOME
    for tool in TOOLS:
        if tool.t0 > T:
            break
        start = tool.crew(0)
        if T - tool.t0 < 0.9:
            s = ease((T - tool.t0) / 0.9)
            return [lerp(a, b, s) for a, b in zip(prev, start)]
        prev = tool.crew(tool.prog(T) if T < tool.t0 + tool.dur else 1)
    return prev


# ---------------------------------------------------------------- panel lateral y cabecera
MINI_S, MINI_OX, MINI_OY = 28, 1475, 345
PT = {"A": A, "B": B, "C": C, "D": D, "E": E, "F": FF}
PLAN_SEGS = ["AB", "BC", "CD", "DA", "DE", "EC", "BF", "FC"]


def mini(p):
    return (MINI_OX + p[0] * MINI_S, MINI_OY - p[1] * MINI_S)


def draw_panel(d, T):
    d.rectangle((1240, 70, W, 930), fill=PANEL)
    cur = next((p for p in PANELS if p["t0"] <= T < p["t1"]), None)
    d.rounded_rectangle((1270, 90, 1890, 360), 14, fill=(24, 29, 41))
    d.text((1290, 104), "PLANO", font=font(18, True), fill=MUTED)
    for s in PLAN_SEGS:
        d.line((*mini(PT[s[0]]), *mini(PT[s[1]])), fill=(90, 100, 120), width=3)
    if cur:
        for s in cur["segs"]:
            d.line((*mini(PT[s[0]]), *mini(PT[s[1]])), fill=ACCENT, width=5)
        for k in cur["pts"]:
            x, y = mini(PT[k])
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=ACCENT)
    for k, off in zip("ABCDEF", [(-16, 12), (14, 12), (14, -10), (-16, -8), (0, -16), (16, 0)]):
        x, y = mini(PT[k])
        d.text((x + off[0], y + off[1]), k, font=font(18, True), fill=CHALK, anchor="mm")
    if not cur:
        return
    a = clamp01((T - cur["t0"]) / 0.5)
    d.text((1275, 385), cur["tag"], font=font(24, True), fill=rgba(ACCENT, a))
    y = 420
    for line in wrap(cur["title"], font(38, True), 600):
        d.text((1275, y), line, font=font(38, True), fill=rgba(CHALK, a))
        y += 48
    y += 14
    fnt = font(27)
    for i, b in enumerate(cur["bullets"]):
        ab = a * clamp01((T - cur["t0"] - 0.4 - 0.35 * i) / 0.4)
        lines = wrap(b, fnt, 570)
        if not b.startswith("✔"):
            d.ellipse((1278, y + 12, 1288, y + 22), fill=rgba(TAPE, ab))
        for j, line in enumerate(lines):
            d.text((1300 if not b.startswith("✔") else 1275, y), line, font=fnt, fill=rgba((226, 232, 240), ab))
            y += 36
        y += 10
    if cur["formula"]:
        af = a * clamp01((T - cur["t0"] - 1.5) / 0.5)
        lines = wrap(cur["formula"], font(28, True), 560)
        h = 30 + 40 * len(lines)
        y = max(y + 10, 900 - h)
        d.rounded_rectangle((1270, y, 1890, y + h), 12, fill=rgba((15, 23, 42), af), outline=rgba(TAPE, af), width=2)
        for j, line in enumerate(lines):
            d.text((1580, y + 35 + 40 * j), line, font=font(28, True), fill=rgba(TAPE, af), anchor="mm")


def draw_header(d, T):
    d.rectangle((0, 0, W, 70), fill=(15, 20, 30))
    d.text((30, 35), "Replanteo sobre asfalto", font=font(30, True), fill=CHALK, anchor="lm")
    d.text((455, 35), "· rectángulo + triángulos", font=font(26), fill=MUTED, anchor="lm")
    steps = ["PASO 1", "PASO 2", "PASO 3", "PASO 4", "PASO 5", "PASO 6", "PASO 7"]
    cur = next((p for p in PANELS if p["t0"] <= T < p["t1"]), None)
    x = 1060
    for i, s in enumerate(steps):
        on = cur and cur["tag"].startswith(s)
        done = cur and (cur["tag"] == "RESUMEN" or (cur["tag"].startswith("PASO") and int(cur["tag"][5]) > i + 1))
        col = ACCENT if on else (OK if done else (70, 80, 100))
        d.rounded_rectangle((x + i * 120, 20, x + i * 120 + 108, 50), 15, fill=col)
        d.text((x + i * 120 + 54, 35), str(i + 1), font=font(20, True), fill=(15, 20, 30), anchor="mm")


def draw_caption(d, T):
    d.rectangle((0, 930, W, H), fill=(10, 12, 18))
    cur = next((c for c in CAPS if c[0] <= T < c[1]), None)
    if not cur:
        return
    a = min(clamp01((T - cur[0]) / 0.3), clamp01((cur[1] - T) / 0.3))
    lines = wrap(cur[2], font(34), 1760)
    y0 = 1005 - (len(lines) - 1) * 22
    for i, line in enumerate(lines):
        d.text((W / 2, y0 + i * 44), line, font=font(34), fill=rgba((255, 255, 255), a), anchor="mm")


def draw_legend(d):
    x, y = 760, 105
    d.rounded_rectangle((x - 20, y - 22, 1225, y + 22), 12, fill=(0, 0, 0, 150))
    for i, ((col, num), role) in enumerate(zip(CREW, ["cero", "tensa/lee", "marca"])):
        draw_person(d, (x + i * 160, y), col, num, r=13)
        d.text((x + i * 160 + 20, y), role, font=font(20), fill=CHALK, anchor="lm")


def title_frame(T):
    im = Image.new("RGB", (W, H), BG_DARK)
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(H):
        d.line((0, i, W, i), fill=(30 + i // 60, 40 + i // 50, 60 + i // 40))
    a = min(clamp01(T / 0.8), clamp01((TITLE_END - T) / 0.6))
    d.text((W / 2, 330), "Replanteo sobre asfalto", font=font(84, True), fill=rgba(CHALK, a), anchor="mm")
    d.text((W / 2, 430), "Cómo llevar al suelo un plano con un rectángulo y dos triángulos",
           font=font(40), fill=rgba((203, 213, 225), a), anchor="mm")
    d.text((W / 2, 500), "Cinta métrica · tiza · cordel · regla 3-4-5 · Pitágoras",
           font=font(30, True), fill=rgba(TAPE, a), anchor="mm")
    s, ox, oy = 34, W / 2 - 3.75 * 34, 900
    segs = [(A, B), (B, C), (C, D), (D, A), (D, E), (E, C), (B, FF), (FF, C)]
    for i, (p, q) in enumerate(segs):
        k = ease((T - 1 - 0.45 * i) / 0.45)
        if k <= 0:
            continue
        pa = (ox + p[0] * s, oy - p[1] * s)
        pq = (ox + (p[0] + (q[0] - p[0]) * k) * s, oy - (p[1] + (q[1] - p[1]) * k) * s)
        d.line((*pa, *pq), fill=rgba(CHALK, a), width=5)
    return im


ASPHALT_IMG, PAPER_IMG = None, None


def render(T):
    if T < TITLE_END:
        return title_frame(T)
    im = Image.new("RGB", (W, H), BG_DARK)
    im.paste(PAPER_IMG if T < ASPHALT else ASPHALT_IMG, (FIELD[0], FIELD[1]))
    d = ImageDraw.Draw(im, "RGBA")
    for el in EL:
        if el.active(T) and (el.t0 >= ASPHALT) == (T >= ASPHALT):
            el.draw(d, T)
    if 38 <= T < 204:
        ca = min(clamp01((T - 38) / 0.6), clamp01((204 - T) / 0.6))
        for (col, num), p in zip(CREW, crew_positions(T)):
            draw_person(d, px(p), col, num, ca)
        draw_legend(d)
    if 204 <= T:
        d.rectangle(FIELD, fill=(0, 0, 0, int(140 * clamp01((T - 204) / 0.8))))
        for el in EL[-2:]:
            el.draw(d, T)
    draw_panel(d, T)
    draw_header(d, T)
    draw_caption(d, T)
    # fundidos entre escenas
    for tc in (TITLE_END, ASPHALT):
        k = abs(T - tc)
        if k < 0.4:
            d.rectangle(FIELD, fill=(0, 0, 0, int(255 * (1 - k / 0.4))))
    if T > END_T - 1:
        d.rectangle((0, 0, W, H), fill=(0, 0, 0, int(255 * clamp01(T - (END_T - 1)))))
    return im


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(path):
    with open(path, "w", encoding="utf-8") as f:
        for i, (t0, t1, text) in enumerate(CAPS, 1):
            f.write(f"{i}\n{srt_time(t0)} --> {srt_time(t1)}\n{text}\n\n")


def main():
    global ASPHALT_IMG, PAPER_IMG
    ASPHALT_IMG, PAPER_IMG = make_asphalt(), make_paper()
    if "--preview" in sys.argv:
        out = os.path.join(HERE, "preview")
        os.makedirs(out, exist_ok=True)
        for t in [3, 20, 30, 50, 68, 76, 100, 114, 136, 142, 162, 175, 190, 208]:
            render(t).save(os.path.join(out, f"f_{t:03d}.png"))
        return
    mp4 = os.path.join(HERE, "replanteo_asfalto.mp4")
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart", mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(END_T * FPS)
    for i in range(n):
        proc.stdin.write(render(i / FPS).tobytes())
        if i % 500 == 0:
            print(f"{i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    write_srt(os.path.join(HERE, "replanteo_asfalto.srt"))
    print("OK", mp4)


if __name__ == "__main__":
    main()
