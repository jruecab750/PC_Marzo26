"""Genera el vídeo «Replanteo sobre asfalto · Plano 1» (documento P00_A_REPLANTEO TAMAÑO REAL).

Uso:
    pip install pillow numpy imageio-ffmpeg piper-tts
    python3 generar_video_plano1.py            # vídeo -> replanteo_plano1.mp4 + .srt
    python3 generar_video_plano1.py --preview  # fotogramas de muestra en ./preview/

Plano 1 (cotas en metros, origen en A):
    Rectángulo ABCD 2,50 x 3,50.
    Trazos perpendiculares desde los puntos medios M1..M4: 2,00 m (el superior 2,50 m).
    Triángulo superior: desde H (mitad del trazo M3G) otra perpendicular de 2,00 m hasta I.
    Semicírculos con centro en la mitad de M1E (R 1,00), FB y JD (R 1,33) y GI (R 1,18).
Métodos: perpendicular en un extremo con arcos de 60° (esquinas) y arcos iguales (puntos medios).
"""
import math
import os
import subprocess
import sys
import tarfile
import urllib.request
import wave

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


# ---------------------------------------------------------------- geometría (Plano 1, cotas en metros)
FIELD = (0, 70, 1240, 930)  # zona de dibujo (x0, y0, x1, y1)
S, OX, OY = 88, 510, 698  # px por metro y origen del mundo en píxeles

# Rectángulo azul 2,50 x 3,50
A, B, C, D = (0, 0), (2.5, 0), (2.5, 3.5), (0, 3.5)
# Puntos medios de los lados
M1, M2, M3, M4 = (1.25, 0), (2.5, 1.75), (1.25, 3.5), (0, 1.75)
# Extremos de los trazos perpendiculares (hacia fuera)
E, F, G, J = (1.25, -2), (4.5, 1.75), (1.25, 6.0), (-2, 1.75)
# Triángulo superior: H = punto medio de M3G; I a 2,00 m perpendicular desde H
H_, I_ = (1.25, 4.75), (3.25, 4.75)


def px(p):
    return (OX + p[0] * S, OY - p[1] * S)


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def mid(a, b):
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


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


def ang(c, p):
    return math.degrees(math.atan2(p[1] - c[1], p[0] - c[0]))


def fmt_m(v):
    return f"{v:.2f}".replace(".", ",") + " m"


def rgba(col, a):
    return (*col, int(255 * clamp01(a)))


def semicircle(p, q, inner):
    """Semicírculo de diámetro pq, hacia el lado contrario a «inner». Devuelve (centro, radio, a0, a1)."""
    c, r = mid(p, q), dist(p, q) / 2
    a0 = ang(c, p)
    # probamos a girar +180 desde p; si pasa por el lado de «inner», giramos -180
    test = polar(c, r, a0 + 90)
    if dist(test, inner) < dist(polar(c, r, a0 - 90), inner):
        return c, r, a0, a0 - 180
    return c, r, a0, a0 + 180


# Semicírculos del plano (centro en el punto medio del lado indicado)
SEMI_INF = semicircle(M1, E, B)   # R 1,00 sobre el trazo M1E
SEMI_DER = semicircle(F, B, M2)   # R 1,33 sobre FB
SEMI_IZQ = semicircle(J, D, M4)   # R 1,33 sobre JD
SEMI_SUP = semicircle(G, I_, H_)  # R 1,18 sobre GI

# Comprobaciones del plano frente a las cotas de SketchUp
assert abs(dist(A, B) - 2.5) < 1e-9 and abs(dist(B, C) - 3.5) < 1e-9
assert abs(SEMI_DER[1] - 1.329) < 1e-3 and abs(SEMI_IZQ[1] - 1.329) < 1e-3
assert abs(SEMI_SUP[1] - 1.179) < 1e-3 and abs(SEMI_INF[1] - 1.0) < 1e-9
assert abs((SEMI_SUP[0][1] + SEMI_SUP[1]) - E[1] - 8.554) < 1e-3  # alto total 855,4 cm
assert abs(F[0] - J[0] - 6.5) < 1e-9  # ancho 650 cm
DIAG = dist(A, C)  # 4,30 m

# Construcción de la perpendicular en un extremo (arcos de 60°), radio 1,50 m
R_EXT = 1.5
P1, P2, P3 = polar(A, R_EXT, 0), polar(A, R_EXT, 60), polar(A, R_EXT, 120)
P4 = (P2[0] + P3[0] - A[0], P2[1] + P3[1] - A[1])  # rombo: queda en la vertical de A
Q1, Q2, Q3 = polar(B, R_EXT, 180), polar(B, R_EXT, 120), polar(B, R_EXT, 60)
Q4 = (Q2[0] + Q3[0] - B[0], Q2[1] + Q3[1] - B[1])
assert abs(P4[0] - A[0]) < 1e-9 and abs(Q4[0] - B[0]) < 1e-9
for a, b in [(P1, P2), (P2, P3), (P2, P4), (P3, P4), (Q1, Q2), (Q2, Q3), (Q2, Q4), (Q3, Q4)]:
    assert abs(dist(a, b) - R_EXT) < 1e-9

# Arcos iguales: dos puntos a 0,75 m del punto medio y arcos de 1,50 m
D_EQ, R_EQ = 0.75, 1.5
H_EQ = math.sqrt(R_EQ ** 2 - D_EQ ** 2)  # 1,299 m


def equal_arcs(m, u, n):
    """m: punto medio; u: dirección del lado; n: normal hacia fuera. Devuelve (K1, K2, X)."""
    k1 = (m[0] - u[0] * D_EQ, m[1] - u[1] * D_EQ)
    k2 = (m[0] + u[0] * D_EQ, m[1] + u[1] * D_EQ)
    x = (m[0] + n[0] * H_EQ, m[1] + n[1] * H_EQ)
    return k1, k2, x


EQ_INF = equal_arcs(M1, (1, 0), (0, -1))
EQ_DER = equal_arcs(M2, (0, 1), (1, 0))
EQ_IZQ = equal_arcs(M4, (0, 1), (-1, 0))
EQ_SUP = equal_arcs(M3, (1, 0), (0, 1))
EQ_H = equal_arcs(H_, (0, 1), (1, 0))
for k1, k2, x in (EQ_INF, EQ_DER, EQ_IZQ, EQ_SUP, EQ_H):
    assert abs(dist(k1, x) - R_EQ) < 1e-9 and abs(dist(k2, x) - R_EQ) < 1e-9


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
    for i in range(-6, 12):
        x = OX + i * S - FIELD[0]
        d.line((x, 0, x, h), fill=(222, 229, 240), width=1)
    for j in range(-3, 11):
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


class Chalk(El):
    """Línea blanca de tiza que se traza en cuanto sus dos extremos están marcados."""

    def __init__(self, t0, a, b, dur=0.9):
        super().__init__(t0, fade=0)
        self.a, self.b, self.dur = a, b, dur

    def draw(self, d, T):
        p = ease((T - self.t0) / self.dur)
        d.line((*px(self.a), *px(lerp(self.a, self.b, p))), fill=CHALK, width=6)


class ChalkArc(Arc):
    """Semicírculo del plano: se traza en blanco girando la cinta desde el centro."""

    def draw(self, d, T):
        p = self.prog(T)
        span = (self.a1 - self.a0) * p
        n = max(2, int(abs(span) / 2))
        pts = [px(polar(self.c, self.r, self.a0 + span * i / n)) for i in range(n + 1)]
        d.line(pts, fill=CHALK, width=6, joint="curve")
        if T < self.t0 + self.dur + 0.8:
            ta = clamp01((self.t0 + self.dur + 0.8 - T) / 0.4)
            c, t = px(self.c), px(self.tip(p))
            d.line((*c, *t), fill=rgba(TAPE, ta), width=8)
            m = ((c[0] + t[0]) / 2, (c[1] + t[1]) / 2 - 26)
            label_box(d, m, "R = " + fmt_m(self.r), font(24, True), TAPE, ta)


class Semi(El):
    """Semicírculo relleno (plano en papel y resultado final)."""

    def __init__(self, t0, semi, fill, a=1.0, outline=None, t1=1e9, fade=0.6):
        super().__init__(t0, t1, fade=fade)
        self.semi, self.fill, self.a, self.outline = semi, fill, a, outline

    def draw(self, d, T):
        al = self.alpha(T)
        c, r, a0, a1 = self.semi
        pts = [px(polar(c, r, a0 + (a1 - a0) * i / 60)) for i in range(61)]
        d.polygon(pts, fill=rgba(self.fill, self.a * al))
        if self.outline:
            d.line(pts + [pts[0]], fill=rgba(self.outline, al), width=3, joint="curve")


def arc_to(t0, dur, c, target, span=22, t1=1e9):
    """Arco de radio |c-target| centrado en c, que pasa por target."""
    a = ang(c, target)
    return Arc(t0, dur, c, dist(c, target), a - span, a + span, t1=t1)


def semi_arc(t0, dur, semi):
    c, r, a0, a1 = semi
    return ChalkArc(t0, dur, c, r, a0, a1)


# ---------------------------------------------------------------- guion (línea de tiempo)
EL, CAPS, PANELS = [], [], []


def cap(t0, t1, text, spoken=None):
    """Subtítulo en pantalla y locución (spoken: texto con números/letras escritos como se pronuncian)."""
    CAPS.append((t0, t1, text, spoken or text))


def panel(t0, t1, tag, title, bullets, formula=None, pts=(), segs=(), semis=()):
    PANELS.append(dict(t0=t0, t1=t1, tag=tag, title=title, bullets=bullets, formula=formula, pts=pts,
                       segs=segs, semis=semis))


def perp_equal(t, m, eq, end, name, name_off, aux_t1, k=1.0):
    """Perpendicular por un punto medio con arcos iguales. k > 1 = más despacio."""
    k1, k2, x = eq
    els = [Tape(t, 1.0 * k, m, k1, hold=0.2), Mark(t + 1.1 * k, k1, "1", (18, -18), aux=True, t1=aux_t1),
           Tape(t + 1.5 * k, 1.0 * k, m, k2, hold=0.2), Mark(t + 2.6 * k, k2, "2", (18, -18), aux=True, t1=aux_t1),
           arc_to(t + 3.0 * k, 2.0 * k, k1, x, t1=aux_t1), arc_to(t + 5.5 * k, 2.0 * k, k2, x, t1=aux_t1),
           Mark(t + 7.7 * k, x, "3", (18, -18), aux=True, t1=aux_t1),
           Tape(t + 8.0 * k, 2.0 * k, m, end, hold=0.8), Mark(t + 8.0 * k + 2.2, end, name, name_off)]
    return els


TITLE_END, ASPHALT, END_T = 7.0, 36.0, 288.0
STEPS = 9

cap(0.8, 7, "¿Cómo se replantea el plano 1? Hoy vamos a llevarlo al asfalto con cinta, tiza y cordel, y sin usar el 3-4-5.",
    "¿Cómo se replantea el plano uno? Hoy vamos a llevarlo al asfalto con cinta, tiza y cordel, y sin usar el tres, cuatro, cinco.")

# --- El plano (7-24)
PAPER = []
PAPER += [Poly(7.5, [A, B, C, D], (91, 134, 214), 0.95, outline=(20, 30, 50)),
          Poly(9.0, [M1, E, B], (252, 213, 180), 1, outline=(20, 30, 50)),
          Poly(9.5, [M2, F, B], (252, 213, 180), 1, outline=(20, 30, 50)),
          Poly(10.0, [M4, J, D], (252, 213, 180), 1, outline=(20, 30, 50)),
          Poly(10.5, [M3, G, I_], (252, 213, 180), 1, outline=(20, 30, 50)),
          Poly(10.5, [G, H_, I_], (196, 120, 84), 1, outline=(20, 30, 50))]
for i, s in enumerate((SEMI_INF, SEMI_DER, SEMI_IZQ, SEMI_SUP)):
    PAPER.append(Semi(11.5 + 0.5 * i, s, (253, 245, 120), 1, outline=(20, 30, 50)))
for p, nm, off in [(A, "A", (-24, 22)), (B, "B", (24, 22)), (C, "C", (24, -16)), (D, "D", (-24, -16)),
                   (E, "E", (0, 26)), (F, "F", (28, 0)), (G, "G", (-24, -10)), (J, "J", (-28, 0)),
                   (I_, "I", (26, 0)), (H_, "H", (-24, 0)), (M1, "M1", (-30, 20)), (M2, "M2", (-34, 0)),
                   (M3, "M3", (-34, 16)), (M4, "M4", (34, 0))]:
    PAPER.append(FText(13.5, ASPHALT, (px(p)[0] + off[0], px(p)[1] + off[1]), nm, 24, (30, 41, 59), box=False))
PAPER += [
    Dim(15, A, B, "2,50", (0, -2.3), (85, 0)),
    Dim(15.6, B, C, "3,50", (2.55, 0), (38, 0)),
    FText(16.5, ASPHALT, (px(mid(M1, E))[0] + 40, px(mid(M1, E))[1]), "2,00", 22, (190, 60, 30), box=False),
    FText(16.8, ASPHALT, (px(mid(M2, F))[0], px(mid(M2, F))[1] - 18), "2,00", 22, (190, 60, 30), box=False),
    FText(17.1, ASPHALT, (px(mid(M4, J))[0], px(mid(M4, J))[1] + 18), "2,00", 22, (190, 60, 30), box=False),
    FText(17.4, ASPHALT, (px(mid(M3, H_))[0] - 40, px(mid(M3, H_))[1]), "2,50", 22, (190, 60, 30), box=False),
    FText(17.7, ASPHALT, (px(mid(H_, I_))[0], px(mid(H_, I_))[1] + 16), "2,00", 22, (190, 60, 30), box=False),
    FText(18.5, ASPHALT, (px(SEMI_INF[0])[0] - 45, px(SEMI_INF[0])[1]), "R 1,00", 22, (190, 60, 30), box=False),
    FText(18.8, ASPHALT, (px(SEMI_DER[0])[0] + 40, px(SEMI_DER[0])[1] + 20), "R 1,33", 22, (190, 60, 30), box=False),
    FText(19.1, ASPHALT, (px(SEMI_IZQ[0])[0] - 30, px(SEMI_IZQ[0])[1] - 20), "R 1,33", 22, (190, 60, 30), box=False),
    FText(19.4, ASPHALT, (px(SEMI_SUP[0])[0] + 20, px(SEMI_SUP[0])[1] - 30), "R 1,18", 22, (190, 60, 30), box=False),
    FText(20, 24, (150, 110), "Cotas en metros", 24, (100, 116, 139), box=False),
]
for el in PAPER:
    el.t1 = min(el.t1, 24.4)
EL += PAPER
cap(7, 15.5, "Este es el plano 1: un rectángulo de 2,50 por 3,50 metros con un triángulo rectángulo en cada lado.",
    "Este es el plano uno: un rectángulo de dos metros y medio por tres y medio, con un triángulo rectángulo en cada lado.")
cap(15.5, 24, "Cada triángulo sale de un trazo perpendicular desde el punto medio del lado, y lleva un semicírculo con el centro en la mitad de uno de sus lados.",
    "Cada triángulo sale de un trazo perpendicular desde el punto medio del lado, y lleva un semicírculo con el centro en la mitad de uno de sus lados.")
panel(7, 24, "EL PLANO 1", "¿Qué vamos a replantear?",
      ["Rectángulo ABCD: 2,50 × 3,50 m", "Trazos perpendiculares desde los puntos medios: 2,00 m (arriba 2,50 m)",
       "4 triángulos rectángulos", "4 semicírculos: R 1,00 · 1,33 · 1,33 · 1,18"])

# --- Material (24-36)
EL.append(Materials(24.3, 35.6))
cap(24, 30, "¿Qué necesitáis? Una cinta métrica de 20 metros, tiza o spray, un cordel, la calculadora y el plano.",
    "¿Qué necesitáis? Una cinta métrica de veinte metros, tiza o espray, un cordel, la calculadora y el plano.")
cap(30, 36, "Trabajad en grupos de tres: uno sujeta el cero, otro tensa y lee la cinta, y el tercero marca en el suelo.")
panel(24, 36, "PREPARACIÓN", "Material y equipo",
      ["Revisa que la cinta no esté doblada ni rota", "Decide antes quién hace cada función",
       "Rotad los papeles en cada triángulo"])

# --- Al asfalto (36-42)
EL.append(FText(36.5, 41.8, (620, 470), "Vista cenital de la zona de trabajo", 34))
cap(36, 42, "Ya estamos en el asfalto, vista desde arriba. Antes de nada: zona limpia, señalizada y sin tráfico.")
panel(36, 42, "ANTES DE EMPEZAR", "Zona de trabajo",
      ["Zona limpia, seca y sin tráfico", "Delimita y señaliza la zona",
       "Necesitas unos 7 × 9 m libres"])

# --- Paso 1: línea base (42-54)
EL += [Mark(42.5, A, "A", (-30, 28)), Tape(44, 3, A, B, hold=1.5), Mark(47.2, B, "B", (30, 28)), Chalk(48.5, A, B)]
cap(42, 47, "Paso 1: la línea base. Marcamos A con una cruz de tiza y medimos 2,50 metros hasta B.",
    "Paso uno: la línea base. Marcamos a con una cruz de tiza y medimos dos metros y medio hasta el punto be.")
cap(47, 54, "Con los dos extremos marcados, trazamos AB en blanco. Cada línea que quede definida, la marcamos en el suelo.",
    "Con los dos extremos marcados, trazamos a be en blanco. Cada línea que quede definida, la marcamos en el suelo.")
panel(42, 54, "PASO 1 / 9", "Línea base AB",
      ["Cruz de tiza en A", "Cero de la cinta en el centro de la cruz", "Marca B a 2,50 m",
       "Traza AB en blanco con el cordel"], pts=("A", "B"), segs=(("A", "B"),))

# --- Paso 2: perpendicular en el extremo A con arcos (54-92)
AUX2 = 92
EL += [
    Arc(54.5, 3.5, A, R_EXT, -8, 135, t1=AUX2), Mark(58.2, P1, "1", (0, 24), aux=True, t1=AUX2),
    arc_to(59.5, 2, P1, P2, t1=AUX2), Mark(61.8, P2, "2", (18, -14), aux=True, t1=AUX2),
    arc_to(63, 2, P2, P3, t1=AUX2), Mark(65.3, P3, "3", (-20, -10), aux=True, t1=AUX2),
    arc_to(67, 2, P2, P4, t1=AUX2), arc_to(69.5, 2, P3, P4, t1=AUX2),
    Mark(72, P4, "4", (22, 0), aux=True, t1=AUX2),
    Tape(73, 3, A, D, hold=1.5, lab_side=-1), Mark(76.3, D, "D", (-30, -14)), Chalk(77, A, D),
    RightAngle(77.5, 128, A, (1, 0), (0, 1), s=0.3),
    FText(82, 91.5, (px(A)[0] - 20, px(P4)[1] - 150), "60° + 60° → el 4 queda a 90°", 26, TAPE),
]
cap(54, 59, "Paso 2: perpendicular en A con arcos. Con centro en A trazamos un arco de 1,50 metros que corte la base: punto 1.",
    "Paso dos: perpendicular en a, con arcos. Con centro en a, trazamos un arco de metro y medio que corte la base: punto uno.")
cap(59, 66, "Sin cambiar la medida, desde el punto 1 cortamos el arco en el punto 2, y desde el 2, en el punto 3.",
    "Sin cambiar la medida, desde el punto uno cortamos el arco en el punto dos, y desde el dos, en el punto tres.")
cap(66, 73, "Ahora, desde el 2 y desde el 3, dos arcos más de 1,50 metros. Se cruzan en el punto 4.",
    "Ahora, desde el dos y desde el tres, dos arcos más de metro y medio. Se cruzan en el punto cuatro.")
cap(73, 82, "La recta de A al punto 4 es perpendicular a la base. Por ella medimos 3,50 metros, marcamos D y trazamos AD en blanco.",
    "La recta de a al punto cuatro es perpendicular a la base. Por ella medimos tres metros y medio, marcamos de, y trazamos a de en blanco.")
cap(82, 92, "¿Por qué funciona? Cada arco avanza 60 grados: el 2 está a 60 y el 3 a 120. El punto 4 queda justo en medio, a 90.",
    "¿Por qué funciona? Cada arco avanza sesenta grados: el dos está a sesenta y el tres a ciento veinte. El punto cuatro queda justo en medio, a noventa.")
panel(54, 92, "PASO 2 / 9", "Perpendicular en un extremo",
      ["Arco R 1,50 m con centro en A → punto 1", "Desde 1, mismo radio → punto 2; desde 2 → punto 3",
       "Arcos desde 2 y 3 → punto 4", "Por A y 4: medimos 3,50 m → D"],
      formula="Saltos de 60°: el 4 queda a 90°", pts=("A", "D"), segs=(("A", "D"),))

# --- Paso 3: perpendicular en B y cierre (92-114)
AUX3 = 114
EL += [
    Arc(92.5, 2.5, B, R_EXT, 188, 45, t1=AUX3), Mark(95.2, Q1, "1", (0, 24), aux=True, t1=AUX3),
    arc_to(95.5, 1.5, Q1, Q2, t1=AUX3), Mark(97.2, Q2, "2", (-18, -14), aux=True, t1=AUX3),
    arc_to(97.5, 1.5, Q2, Q3, t1=AUX3), Mark(99.2, Q3, "3", (20, -10), aux=True, t1=AUX3),
    arc_to(99.5, 1.5, Q2, Q4, t1=AUX3), arc_to(101.2, 1.5, Q3, Q4, t1=AUX3),
    Mark(103, Q4, "4", (22, 0), aux=True, t1=AUX3),
    Tape(103.5, 3, B, C, hold=1), Mark(106.7, C, "C", (30, -14)), Chalk(107.3, B, C), Chalk(108.4, D, C),
    RightAngle(107.5, 128, B, (-1, 0), (0, 1), s=0.3),
]
cap(92, 103, "Paso 3: repetimos en B. Arco de 1,50 metros con centro en B, y de ahí los puntos 1, 2, 3 y 4, igual que antes.",
    "Paso tres: repetimos en be. Arco de metro y medio con centro en be, y de ahí los puntos uno, dos, tres y cuatro, igual que antes.")
cap(103, 114, "Medimos 3,50 metros por la perpendicular: punto C. Con C y D marcados, trazamos BC y DC en blanco.",
    "Medimos tres metros y medio por la perpendicular: punto ce. Con ce y de marcados, trazamos be ce, y de ce, en blanco.")
panel(92, 114, "PASO 3 / 9", "Perpendicular en B y cierre",
      ["Mismo método de arcos en B", "Por B y 4: medimos 3,50 m → C", "Traza BC y DC en blanco"],
      pts=("B", "C", "D"), segs=(("B", "C"), ("C", "D")))

# --- Paso 4: comprobación (114-128)
EL += [Tape(114.5, 2, D, C, hold=2), Tape(117.5, 2.5, A, C, hold=5, lab_side=-1, lab_at=0.3),
       Tape(120.5, 2.5, B, D, hold=3, lab_at=0.3),
       FText(123.5, 127.8, (px(mid(D, C))[0], px(D)[1] - 60), "DC = 2,50 m · AC = BD = 4,30 m  ✔", 28, OK)]
cap(114, 120, "Paso 4: comprobamos. El lado DC tiene que medir 2,50 metros.",
    "Paso cuatro: comprobamos. El lado de ce tiene que medir dos metros y medio.")
cap(120, 128, "Y las dos diagonales, lo mismo: 4,30 metros. Si no coinciden, revisad las perpendiculares.",
    "Y las dos diagonales, lo mismo: cuatro metros y treinta centímetros. Si no coinciden, revisad las perpendiculares.")
panel(114, 128, "PASO 4 / 9", "Comprobar el rectángulo",
      ["DC = 2,50 m", "Diagonales iguales: 4,30 m", "Diferencia > 2 cm → repite las perpendiculares"],
      formula="d = √(2,5² + 3,5²) = 4,30 m", pts=("A", "B", "C", "D"), segs=(("A", "C"), ("B", "D")))

# --- Paso 5: puntos medios (128-142)
EL += [Tape(128.5, 1.5, A, M1, hold=0.3), Mark(130.2, M1, "M1", (-10, 28)),
       Tape(131, 1.5, D, M3, hold=0.3, lab_side=-1), Mark(132.7, M3, "M3", (-38, -22)),
       Tape(133.5, 1.5, A, M4, hold=0.3, lab_side=-1), Mark(135.2, M4, "M4", (40, 0)),
       Tape(136, 1.5, B, M2, hold=0.3), Mark(137.7, M2, "M2", (-42, 0))]
cap(128, 135, "Paso 5: los puntos medios. En los lados de 2,50 medimos 1,25 metros; en los de 3,50, 1,75.",
    "Paso cinco: los puntos medios. En los lados de dos y medio, medimos uno veinticinco; en los de tres y medio, uno setenta y cinco.")
cap(135, 142, "De cada punto medio sale un trazo perpendicular hacia fuera, como dice la nota del plano.")
panel(128, 142, "PASO 5 / 9", "Puntos medios",
      ["AB y DC: a 1,25 m → M1 y M3", "AD y BC: a 1,75 m → M4 y M2", "De cada uno sale un trazo perpendicular"],
      pts=("M1", "M2", "M3", "M4"))

# --- Paso 6: triángulo inferior, arcos iguales en detalle (142-170)
AUX6 = 170
EL += perp_equal(142.5, M1, EQ_INF, E, "E", (26, 20), AUX6, k=1.15)
EL += [Chalk(157.3, M1, E), Chalk(158.3, E, B),
       Tape(159.5, 1.2, M1, SEMI_INF[0], hold=0.5, lab_side=-1),
       Mark(161, SEMI_INF[0], "O", (22, 0), aux=True, t1=AUX6), semi_arc(162, 3.5, SEMI_INF)]
cap(142, 147, "Paso 6: triángulo de abajo. La perpendicular en M1 la hacemos con arcos iguales: dos puntos a 75 centímetros, uno a cada lado.",
    "Paso seis: triángulo de abajo. La perpendicular en eme uno la hacemos con arcos iguales: dos puntos a setenta y cinco centímetros, uno a cada lado.")
cap(147, 154, "Desde cada uno, un arco de 1,50 metros hacia fuera. Donde se cruzan, punto 3: está justo en la perpendicular.",
    "Desde cada uno, un arco de metro y medio hacia fuera. Donde se cruzan, punto tres: está justo en la perpendicular.")
cap(154, 161, "Desde M1, pasando por el punto 3, medimos 2 metros: es E. Trazamos M1E y EB en blanco.",
    "Desde eme uno, pasando por el punto tres, medimos dos metros: es el punto e. Trazamos eme uno e, y e be, en blanco.")
cap(161, 170, "El semicírculo tiene el centro en la mitad de M1E, a 1 metro. Con la cinta a 1 metro, giramos y lo marcamos.",
    "El semicírculo tiene el centro en la mitad de eme uno e, a un metro. Con la cinta a un metro, giramos y lo marcamos.")
panel(142, 170, "PASO 6 / 9", "Triángulo inferior: arcos iguales",
      ["Puntos 1 y 2 a 0,75 m de M1", "Arcos iguales de 1,50 m → punto 3", "Por M1 y 3: 2,00 m → E",
       "Semicírculo: centro a 1,00 m, R 1,00 m"], formula="Arcos iguales → cruce en la perpendicular",
      pts=("M1", "E"), segs=(("M1", "E"), ("E", "B")), semis=("inf",))

# --- Paso 7: triángulo derecho (170-194)
AUX7 = 194
EL += perp_equal(170.5, M2, EQ_DER, F, "F", (28, -18), AUX7, k=0.9)
EL += [Chalk(181.3, M2, F), Chalk(182.3, F, B),
       Tape(183.3, 1.5, F, SEMI_DER[0], hold=0.6), Mark(185, SEMI_DER[0], "O", (22, 10), aux=True, t1=AUX7),
       semi_arc(185.5, 3.5, SEMI_DER)]
cap(170, 178, "Paso 7: triángulo de la derecha. Mismo método en M2: dos puntos a 75 centímetros y arcos iguales de 1,50.",
    "Paso siete: triángulo de la derecha. Mismo método en eme dos: dos puntos a setenta y cinco centímetros, y arcos iguales de metro y medio.")
cap(178, 185, "Por el cruce, 2 metros hasta F. Trazamos M2F y FB en blanco.",
    "Por el cruce, dos metros hasta efe. Trazamos eme dos efe, y efe be, en blanco.")
cap(185, 194, "Aquí el semicírculo va sobre FB, que mide 2,66 metros: el centro está en su mitad y el radio es 1,33.",
    "Aquí el semicírculo va sobre efe be, que mide dos sesenta y seis: el centro está en su mitad, y el radio es uno treinta y tres.")
panel(170, 194, "PASO 7 / 9", "Triángulo derecho",
      ["Arcos iguales en M2 hacia fuera", "2,00 m → F", "Traza M2F y FB", "Semicírculo sobre FB: R 1,33 m"],
      formula="FB = √(2² + 1,75²) = 2,66 → R 1,33", pts=("M2", "F"), segs=(("M2", "F"), ("F", "B")),
      semis=("der",))

# --- Paso 8: triángulo izquierdo (194-216)
AUX8 = 216
EL += perp_equal(194.5, M4, EQ_IZQ, J, "J", (-28, -18), AUX8, k=0.9)
EL += [Chalk(205.3, M4, J), Chalk(206.3, J, D),
       Tape(207.3, 1.5, J, SEMI_IZQ[0], hold=0.6, lab_side=-1),
       Mark(209, SEMI_IZQ[0], "O", (22, 10), aux=True, t1=AUX8), semi_arc(209.5, 3.5, SEMI_IZQ)]
cap(194, 202, "Paso 8: triángulo de la izquierda. Igual: arcos iguales desde M4, hacia fuera.",
    "Paso ocho: triángulo de la izquierda. Igual: arcos iguales desde eme cuatro, hacia fuera.")
cap(202, 209, "A 2 metros, el punto J. Trazamos M4J y JD en blanco.",
    "A dos metros, el punto jota. Trazamos eme cuatro jota, y jota de, en blanco.")
cap(209, 216, "Centro en la mitad de JD, a 1,33 metros, y semicírculo de 1,33 de radio.",
    "Centro en la mitad de jota de, a uno treinta y tres, y semicírculo de uno treinta y tres de radio.")
panel(194, 216, "PASO 8 / 9", "Triángulo izquierdo",
      ["Arcos iguales en M4 hacia fuera", "2,00 m → J", "Traza M4J y JD", "Semicírculo sobre JD: R 1,33 m"],
      formula="JD = √(2² + 1,75²) = 2,66 → R 1,33", pts=("M4", "J"), segs=(("M4", "J"), ("J", "D")),
      semis=("izq",))

# --- Paso 9: triángulo superior (216-252)
AUX9 = 252
k1, k2, x = EQ_SUP
EL += [Tape(216.5, 1, M3, k1, hold=0.2), Mark(217.6, k1, "1", (18, -18), aux=True, t1=AUX9),
       Tape(218, 1, M3, k2, hold=0.2), Mark(219.1, k2, "2", (18, -18), aux=True, t1=AUX9),
       arc_to(219.5, 2, k1, x, t1=AUX9), arc_to(222, 2, k2, x, t1=AUX9), Mark(224.2, x, "3", (18, -18), aux=True, t1=AUX9),
       Tape(224.5, 2.5, M3, G, hold=0.8), Mark(227.2, G, "G", (-28, -16)), Chalk(227.7, M3, G),
       Tape(229, 1.2, M3, H_, hold=0.4, lab_side=-1), Mark(230.5, H_, "H", (-28, 0))]
k1, k2, x = EQ_H
EL += [Tape(231, 0.8, H_, k1, hold=0.2), Mark(231.9, k1, "1", (18, -18), aux=True, t1=AUX9),
       Tape(232.2, 0.8, H_, k2, hold=0.2), Mark(233.1, k2, "2", (18, -18), aux=True, t1=AUX9),
       arc_to(233.5, 2, k1, x, t1=AUX9), arc_to(235.8, 2, k2, x, t1=AUX9), Mark(238, x, "3", (18, -18), aux=True, t1=AUX9),
       Tape(238.3, 2, H_, I_, hold=0.8), Mark(240.5, I_, "I", (28, 0)),
       Chalk(241, H_, I_), Chalk(241.8, G, I_), Chalk(242.6, I_, M3),
       Tape(243.8, 1.5, G, SEMI_SUP[0], hold=0.5), Mark(245.5, SEMI_SUP[0], "O", (0, 24), aux=True, t1=AUX9),
       semi_arc(246, 3.5, SEMI_SUP)]
cap(216, 224, "Paso 9: triángulo de arriba. Arcos iguales en M3, esta vez hacia arriba.",
    "Paso nueve: triángulo de arriba. Arcos iguales en eme tres, esta vez hacia arriba.")
cap(224, 231, "Este trazo es más largo: 2,50 metros hasta G. Su punto medio, a 1,25, es H.",
    "Este trazo es más largo: dos metros y medio hasta ge. Su punto medio, a uno veinticinco, es hache.")
cap(231, 241, "Desde H, otra perpendicular con arcos iguales, ahora hacia la derecha. A 2 metros, el punto I.",
    "Desde hache, otra perpendicular con arcos iguales, ahora hacia la derecha. A dos metros, el punto i.")
cap(241, 252, "Trazamos GI e I-M3 en blanco. El semicírculo va sobre GI, de 2,36 metros: radio 1,18.",
    "Trazamos ge i, e i eme tres, en blanco. El semicírculo va sobre ge i, de dos treinta y seis: radio uno dieciocho.")
panel(216, 252, "PASO 9 / 9", "Triángulo superior",
      ["Arcos iguales en M3 → 2,50 m → G", "H = mitad de M3G (1,25 m)", "Arcos iguales en H → 2,00 m → I",
       "Semicírculo sobre GI: R 1,18 m"], formula="GI = √(2² + 1,25²) = 2,36 → R 1,18",
      pts=("M3", "G", "H", "I"), segs=(("M3", "G"), ("H", "I"), ("G", "I"), ("I", "M3")), semis=("sup",))

# --- Plano terminado (252-262), resumen (262-280) y cierre (280-288)
FILL = [Poly(252.5, [A, B, C, D], (91, 134, 214), 0.45, t1=END_T + 1),
        Poly(253, [M1, E, B], (252, 213, 180), 0.4, t1=END_T + 1), Poly(253, [M2, F, B], (252, 213, 180), 0.4, t1=END_T + 1),
        Poly(253, [M4, J, D], (252, 213, 180), 0.4, t1=END_T + 1), Poly(253, [M3, G, I_], (252, 213, 180), 0.4, t1=END_T + 1),
        Poly(253.5, [G, H_, I_], (196, 120, 84), 0.45, t1=END_T + 1)]
for s in (SEMI_INF, SEMI_DER, SEMI_IZQ, SEMI_SUP):
    FILL.append(Semi(254, s, (253, 245, 120), 0.4, t1=END_T + 1, fade=1.0))
EL += FILL
cap(252, 262, "¡Plano terminado! Rectángulo, cuatro triángulos y cuatro semicírculos, todo a tamaño real sobre el asfalto.")
cap(262, 271, "Recordad: en una esquina, perpendicular con arcos desde el extremo; en un punto medio, con arcos iguales.")
cap(271, 280, "Cinta tensa, el cero en el centro de la cruz, y cada línea en blanco en cuanto tenga sus dos extremos.")
panel(252, END_T, "RESUMEN", "Claves del plano 1",
      ["✔ Esquinas: arcos desde el extremo (60°)", "✔ Puntos medios: arcos iguales", "✔ Diagonales: 4,30 m",
       "✔ Centro del semicírculo = mitad del lado", "✔ Línea en blanco al tener sus 2 extremos"],
      formula="Tolerancia: ±2 cm")
EL += [FText(280.3, END_T + 1, (620, 430), "¡Ahora os toca a vosotros!", 52, TAPE),
       FText(281, END_T + 1, (620, 520), "Replantead el plano 1 · Tolerancia ±2 cm", 30, CHALK)]
cap(280, 287, "¡Ahora os toca a vosotros! Replantead el plano 1 en el patio.",
    "¡Ahora os toca a vosotros! Replantead el plano uno en el patio.")

TOOLS = sorted([e for e in EL if getattr(e, "tool", False)], key=lambda e: e.t0)

# ---------------------------------------------------------------- equipo (alumnos 1, 2 y 3)
CREW_HOME = [(-0.6, -0.4), (0.2, -0.5), (-0.2, 0.5)]
CREW_T0, CREW_T1 = 40.0, 252.0


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
MINI_S, MINI_OX, MINI_OY = 26, 1547.5, 284
PT = {"A": A, "B": B, "C": C, "D": D, "M1": M1, "M2": M2, "M3": M3, "M4": M4,
      "E": E, "F": F, "G": G, "J": J, "H": H_, "I": I_}
PLAN_SEGS = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"), ("M1", "E"), ("E", "B"), ("M2", "F"), ("F", "B"),
             ("M4", "J"), ("J", "D"), ("M3", "G"), ("G", "I"), ("I", "M3"), ("H", "I")]
SEMIS = {"inf": SEMI_INF, "der": SEMI_DER, "izq": SEMI_IZQ, "sup": SEMI_SUP}


def mini(p):
    return (MINI_OX + p[0] * MINI_S, MINI_OY - p[1] * MINI_S)


def mini_semi(d, semi, col, width):
    c, r, a0, a1 = semi
    d.line([mini(polar(c, r, a0 + (a1 - a0) * i / 40)) for i in range(41)], fill=col, width=width, joint="curve")


def draw_panel(d, T):
    d.rectangle((1240, 70, W, 930), fill=PANEL)
    cur = next((p for p in PANELS if p["t0"] <= T < p["t1"]), None)
    d.rounded_rectangle((1270, 90, 1890, 360), 14, fill=(24, 29, 41))
    d.text((1290, 104), "PLANO 1", font=font(18, True), fill=MUTED)
    for a, b in PLAN_SEGS:
        d.line((*mini(PT[a]), *mini(PT[b])), fill=(90, 100, 120), width=3)
    for s in SEMIS.values():
        mini_semi(d, s, (90, 100, 120), 3)
    if cur:
        for a, b in cur["segs"]:
            d.line((*mini(PT[a]), *mini(PT[b])), fill=ACCENT, width=5)
        for k in cur["semis"]:
            mini_semi(d, SEMIS[k], ACCENT, 5)
        for k in cur["pts"]:
            x, y = mini(PT[k])
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=ACCENT)
    for k, off in [("A", (-12, 10)), ("B", (12, 10)), ("C", (12, -8)), ("D", (-12, -8)), ("E", (12, 6)),
                   ("F", (12, -8)), ("G", (-12, -4)), ("J", (-10, -10)), ("I", (12, 6))]:
        x, y = mini(PT[k])
        d.text((x + off[0], y + off[1]), k, font=font(16, True), fill=CHALK, anchor="mm")
    if not cur:
        return
    a = clamp01((T - cur["t0"]) / 0.5)
    d.text((1275, 385), cur["tag"], font=font(24, True), fill=rgba(ACCENT, a))
    y = 420
    for line in wrap(cur["title"], font(38, True), 600):
        d.text((1275, y), line, font=font(38, True), fill=rgba(CHALK, a))
        y += 48
    y += 14
    fnt = font(26)
    for i, b in enumerate(cur["bullets"]):
        ab = a * clamp01((T - cur["t0"] - 0.4 - 0.35 * i) / 0.4)
        lines = wrap(b, fnt, 570)
        if not b.startswith("✔"):
            d.ellipse((1278, y + 12, 1288, y + 22), fill=rgba(TAPE, ab))
        for line in lines:
            d.text((1300 if not b.startswith("✔") else 1275, y), line, font=fnt, fill=rgba((226, 232, 240), ab))
            y += 34
        y += 8
    if cur["formula"]:
        af = a * clamp01((T - cur["t0"] - 1.5) / 0.5)
        lines = wrap(cur["formula"], font(26, True), 570)
        h = 30 + 38 * len(lines)
        y = max(y + 10, 905 - h)
        d.rounded_rectangle((1270, y, 1890, y + h), 12, fill=rgba((15, 23, 42), af), outline=rgba(TAPE, af), width=2)
        for j, line in enumerate(lines):
            d.text((1580, y + 34 + 38 * j), line, font=font(26, True), fill=rgba(TAPE, af), anchor="mm")


def draw_header(d, T):
    d.rectangle((0, 0, W, 70), fill=(15, 20, 30))
    d.text((30, 35), "Replanteo sobre asfalto", font=font(30, True), fill=CHALK, anchor="lm")
    d.text((455, 35), "· Plano 1", font=font(26), fill=MUTED, anchor="lm")
    cur = next((p for p in PANELS if p["t0"] <= T < p["t1"]), None)
    n = int(cur["tag"].split()[1]) if cur and cur["tag"].startswith("PASO") else (99 if cur and cur["tag"] == "RESUMEN" else 0)
    x = 1110
    for i in range(STEPS):
        col = ACCENT if n == i + 1 else (OK if n > i + 1 else (70, 80, 100))
        d.rounded_rectangle((x + i * 88, 20, x + i * 88 + 78, 50), 15, fill=col)
        d.text((x + i * 88 + 39, 35), str(i + 1), font=font(20, True), fill=(15, 20, 30), anchor="mm")


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
    x, y = 40, 902
    d.rounded_rectangle((x - 22, y - 22, x + 470, y + 22), 12, fill=(0, 0, 0, 150))
    for i, ((col, num), role) in enumerate(zip(CREW, ["cero", "tensa/lee", "marca"])):
        draw_person(d, (x + i * 160, y), col, num, r=13)
        d.text((x + i * 160 + 20, y), role, font=font(20), fill=CHALK, anchor="lm")


def title_frame(T):
    im = Image.new("RGB", (W, H), BG_DARK)
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(H):
        d.line((0, i, W, i), fill=(30 + i // 60, 40 + i // 50, 60 + i // 40))
    a = min(clamp01(T / 0.8), clamp01((TITLE_END - T) / 0.6))
    d.text((W / 2, 250), "Replanteo sobre asfalto · Plano 1", font=font(80, True), fill=rgba(CHALK, a), anchor="mm")
    d.text((W / 2, 345), "Perpendiculares con arcos: desde un extremo y con arcos iguales",
           font=font(40), fill=rgba((203, 213, 225), a), anchor="mm")
    d.text((W / 2, 412), "Cinta métrica · tiza · cordel · cada línea en blanco",
           font=font(30, True), fill=rgba(TAPE, a), anchor="mm")
    s, ox, oy = 34, W / 2 - 1.25 * 34, 790
    for i, (p, q) in enumerate(PLAN_SEGS):
        k = ease((T - 1 - 0.25 * i) / 0.3)
        if k <= 0:
            continue
        pa = (ox + PT[p][0] * s, oy - PT[p][1] * s)
        pq = (ox + (PT[p][0] + (PT[q][0] - PT[p][0]) * k) * s, oy - (PT[p][1] + (PT[q][1] - PT[p][1]) * k) * s)
        d.line((*pa, *pq), fill=rgba(CHALK, a), width=4)
    if T > 4.5:
        k = ease((T - 4.5) / 1)
        for sm in SEMIS.values():
            c, r, a0, a1 = sm
            d.line([(ox + polar(c, r, a0 + (a1 - a0) * k * i / 40)[0] * s, oy - polar(c, r, a0 + (a1 - a0) * k * i / 40)[1] * s)
                    for i in range(41)], fill=rgba(CHALK, a), width=4)
    draw_caption(d, T)
    return im


ASPHALT_IMG, PAPER_IMG = None, None
CLOSE_T = 280.0


def render(T):
    if T < TITLE_END:
        return title_frame(T)
    im = Image.new("RGB", (W, H), BG_DARK)
    im.paste(PAPER_IMG if T < ASPHALT else ASPHALT_IMG, (FIELD[0], FIELD[1]))
    d = ImageDraw.Draw(im, "RGBA")
    for el in EL[:-2]:
        if el.active(T) and (el.t0 >= ASPHALT) == (T >= ASPHALT):
            el.draw(d, T)
    if CREW_T0 <= T < CREW_T1:
        ca = min(clamp01((T - CREW_T0) / 0.6), clamp01((CREW_T1 - T) / 0.6))
        for (col, num), p in zip(CREW, crew_positions(T)):
            draw_person(d, px(p), col, num, ca)
        draw_legend(d)
    if CLOSE_T <= T:
        d.rectangle(FIELD, fill=(0, 0, 0, int(140 * clamp01((T - CLOSE_T) / 0.8))))
        for el in EL[-2:]:
            if el.active(T):
                el.draw(d, T)
    draw_panel(d, T)
    draw_header(d, T)
    draw_caption(d, T)
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
        for i, (t0, t1, text, _) in enumerate(CAPS, 1):
            f.write(f"{i}\n{srt_time(to_video(t0))} --> {srt_time(to_video(t1))}\n{text}\n\n")


# ---------------------------------------------------------------- locución (Piper TTS, sin conexión)
VOICE_URL = "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz"
VOICE_DIR = os.path.join(HERE, ".voz")
VOICE_MODEL = os.path.join(VOICE_DIR, "es-carlfm-x-low.onnx")
LEAD, TAIL = 0.3, 0.5  # silencio antes y después de cada frase (s)

# Tiempo del guion -> tiempo del vídeo. Si una frase dura más que su escena,
# la escena se alarga (la animación va algo más lenta) para que la voz quepa.
_warp = ([0.0], [0.0])


def to_video(t):
    return float(np.interp(t, *_warp))


def to_script(t):
    return float(np.interp(t, _warp[1], _warp[0]))


def ensure_voice():
    if os.path.exists(VOICE_MODEL):
        return
    os.makedirs(VOICE_DIR, exist_ok=True)
    tgz = os.path.join(VOICE_DIR, "voz.tar.gz")
    urllib.request.urlretrieve(VOICE_URL, tgz)
    with tarfile.open(tgz) as tf:
        tf.extractall(VOICE_DIR)
    os.remove(tgz)


def synth(text, idx):
    path = os.path.join(VOICE_DIR, f"frase_{idx:02d}.wav")
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE_MODEL, "-f", path, "--sentence-silence", "0.35"],
                   input=text.encode("utf-8"), check=True, capture_output=True)
    with wave.open(path) as w:
        sr = w.getframerate()
        audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return audio, sr


def build_narration():
    """Sintetiza cada frase, ajusta la línea de tiempo y devuelve la ruta del .wav completo."""
    global _warp
    ensure_voice()
    CAPS.sort(key=lambda c: c[0])
    clips = [synth(c[3], i) for i, c in enumerate(CAPS)]
    sr = clips[0][1]
    ks, kv = [0.0], [0.0]
    for (t0, t1, _, _), (audio, _) in zip(CAPS, clips):
        ks.append(t0)
        kv.append(kv[-1] + t0 - ks[-2])
        ks.append(t1)
        kv.append(kv[-1] + max(t1 - t0, LEAD + len(audio) / sr + TAIL))
    ks.append(END_T)
    kv.append(kv[-1] + END_T - ks[-2])
    _warp = (ks, kv)
    track = np.zeros(int((kv[-1] + 1) * sr), dtype=np.float32)
    for (t0, *_), (audio, _) in zip(CAPS, clips):
        i = int((to_video(t0) + LEAD) * sr)
        track[i:i + len(audio)] += audio
    track *= 0.9 / max(1e-6, np.abs(track).max())
    path = os.path.join(VOICE_DIR, "narracion.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((track * 32767).astype(np.int16).tobytes())
    return path


def main():
    global ASPHALT_IMG, PAPER_IMG
    ASPHALT_IMG, PAPER_IMG = make_asphalt(), make_paper()
    if "--preview" in sys.argv:
        out = os.path.join(HERE, "preview")
        os.makedirs(out, exist_ok=True)
        for t in [3, 20, 30, 50, 66, 72, 88, 106, 125, 137, 152, 166, 188, 212, 236, 249, 258, 284]:
            render(t).save(os.path.join(out, f"f_{t:03d}.png"))
        return
    narr = build_narration()
    total = to_video(END_T)
    print(f"Duración con locución: {total:.1f} s")
    mp4 = os.path.join(HERE, "replanteo_plano1.mp4")
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", narr,
           "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-shortest", "-movflags", "+faststart", mp4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n = int(total * FPS)
    for i in range(n):
        proc.stdin.write(render(to_script(i / FPS)).tobytes())
        if i % 500 == 0:
            print(f"{i}/{n}", flush=True)
    proc.stdin.close()
    proc.wait()
    write_srt(os.path.join(HERE, "replanteo_plano1.srt"))
    print("OK", mp4)


if __name__ == "__main__":
    main()
