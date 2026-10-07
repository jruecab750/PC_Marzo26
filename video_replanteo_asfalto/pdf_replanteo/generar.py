"""Genera las páginas HTML de los PDF del replanteo (después: node pdf.mjs las imprime en A4).

    python3 generar.py   -> plano1_A4_escala_1-100.html, plano_practicas_A4_escala_1-100.html, guia_replanteo_plano1.html

- Hojas A4 a escala 1:100 (1 cm de papel = 1 m) con las cotas al doble del plano del patio: se mide en centímetros
  el mismo número que pone la cota, siempre en centímetros enteros o medios.
  El SVG está en milímetros, así que al imprimir al 100 % la escala es exacta (barra de control de 10 cm).
- Guía del replanteo a tamaño real del plano 1: métodos y pasos 0 a 9 con dibujos técnicos 2D.
"""
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ geometría (metros)
def P(x, y): return (x, y)
def add(a, b): return (a[0] + b[0], a[1] + b[1])
def sub(a, b): return (a[0] - b[0], a[1] - b[1])
def mul(a, k): return (a[0] * k, a[1] * k)
def ln(a): return math.hypot(*a)
def mid(a, b): return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
def nrm(a): l = ln(a) or 1; return (a[0] / l, a[1] / l)
def dirv(d): return (math.cos(math.radians(d)), math.sin(math.radians(d)))
def polar(c, r, d): return add(c, mul(dirv(d), r))
def ang(c, p): return math.degrees(math.atan2(p[1] - c[1], p[0] - c[0]))


def semicircle(p, q, inner):
    c, r, a0 = mid(p, q), ln(sub(p, q)) / 2, ang(mid(p, q), p)
    plus, minus = polar(c, r, a0 + 90), polar(c, r, a0 - 90)
    return dict(c=c, r=r, a0=a0, a1=a0 - 180 if ln(sub(plus, inner)) < ln(sub(minus, inner)) else a0 + 180)


def mid_info(p, q, r):
    m, u = mid(p, q), nrm(sub(q, p))
    n, h = (-u[1], u[0]), math.sqrt(r * r - (ln(sub(q, p)) / 2) ** 2)
    return dict(m=m, x1=add(m, mul(n, h)), x2=sub(m, mul(n, h)))


# Plano 1
A, B, C, D = P(0, 0), P(2.5, 0), P(2.5, 3.5), P(0, 3.5)
M1, M2, M3, M4 = P(1.25, 0), P(2.5, 1.75), P(1.25, 3.5), P(0, 1.75)
E, F, G, J, H, I = P(1.25, -2), P(4.5, 1.75), P(1.25, 6), P(-2, 1.75), P(1.25, 4.75), P(3.25, 4.75)
S_INF, S_DER, S_IZQ, S_SUP = semicircle(E, M1, B), semicircle(F, B, M2), semicircle(J, D, M4), semicircle(G, I, H)
RX, DQ, RQ = 1.5, 0.75, 1.5
HQ = math.sqrt(RQ * RQ - DQ * DQ)


def eq(m, u, n): return dict(m=m, k1=sub(m, mul(u, DQ)), k2=add(m, mul(u, DQ)), x=add(m, mul(n, HQ)))


EQ_INF, EQ_DER, EQ_IZQ, EQ_SUP = eq(M1, (1, 0), (0, -1)), eq(M2, (0, 1), (1, 0)), eq(M4, (0, 1), (-1, 0)), eq(M3, (1, 0), (0, 1))


def equal_radii(o, base, sg, r=RX):
    p1, p2, p3 = polar(o, r, base), polar(o, r, base + 60 * sg), polar(o, r, base + 120 * sg)
    return dict(o=o, p1=p1, p2=p2, p3=p3, p4=sub(add(p2, p3), o), r=r)


EQ_A, EQ_B = equal_radii(A, 0, 1), equal_radii(B, 180, -1)

# ------------------------------------------------------------------ dibujo SVG
INK, GREY, ORANGE, YELLOW = "#1d2329", "#b5bcc3", "#ff6b1a", "#f2c230"
RED, DIM = "#d4161b", "#c4501a"   # nombres de los vértices y cotas
AUX = ["#1f8fe0", "#e0457b", "#1fa463", "#8a4fd8", "#d98c00"]


class Fig:
    """Figura en metros -> SVG. s = mm de papel por metro; si fit, se encaja en w × h mm."""

    def __init__(self, s=20.0, ox=0.0, oy=0.0, w=210, h=297, unit="mm"):
        self.s, self.ox, self.oy, self.w, self.h, self.items, self.k = s, ox, oy, w, h, [], 1.0

    @classmethod
    def fit(cls, pts, w, h, pad=8, max_s=None):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        s = min((w - 2 * pad) / (max(xs) - min(xs)), (h - 2 * pad) / (max(ys) - min(ys)))
        if max_s: s = min(s, max_s)
        f = cls(s, w / 2 - s * (min(xs) + max(xs)) / 2, h / 2 + s * (min(ys) + max(ys)) / 2, w, h)
        f.k = 0.8
        return f

    def X(self, p): return (self.ox + self.s * p[0], self.oy - self.s * p[1])

    def line(self, a, b, color=INK, w=0.6, dash=None):
        (x1, y1), (x2, y2) = self.X(a), self.X(b)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="{color}" stroke-width="{w * self.k:.2f}" stroke-linecap="round"{d}/>')

    def poly(self, pts, color=INK, w=0.6, fill="none", close=False, dash=None):
        d = "M" + " L".join(f"{x:.2f} {y:.2f}" for x, y in map(self.X, pts)) + (" Z" if close else "")
        ds = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<path d="{d}" stroke="{color}" stroke-width="{w * self.k:.2f}" fill="{fill}" stroke-linejoin="round" stroke-linecap="round"{ds}/>')

    def arc(self, c, r, a0, a1, color=INK, w=0.6, dash=None):
        n = max(8, int(abs(a1 - a0) / 3))
        self.poly([polar(c, r, a0 + (a1 - a0) * i / n) for i in range(n + 1)], color, w, dash=dash)

    def arc_to(self, c, target, span=16, color=AUX[0], w=0.45):
        a = ang(c, target)
        self.arc(c, ln(sub(target, c)), a - span, a + span, color, w)

    def semi(self, sm, color=INK, w=0.6, dash=None): self.arc(sm["c"], sm["r"], sm["a0"], sm["a1"], color, w, dash)

    def cross(self, p, color=INK, size=1.6, w=0.45):
        x, y = self.X(p); s = size * self.k
        self.items.append(f'<path d="M{x - s:.2f} {y - s:.2f} L{x + s:.2f} {y + s:.2f} M{x - s:.2f} {y + s:.2f} L{x + s:.2f} {y - s:.2f}" stroke="{color}" stroke-width="{w * self.k:.2f}"/>')

    def dot(self, p, color=INK, r=0.7):
        x, y = self.X(p)
        self.items.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r * self.k:.2f}" fill="{color}"/>')

    def text(self, p, t, dx=0, dy=0, size=3.6, color=INK, weight=700, anchor="middle", rot=0, bg=False):
        x, y = self.X(p); x += dx * self.k; y += dy * self.k; size *= self.k
        tr = f' transform="rotate({rot:.1f} {x:.2f} {y:.2f})"' if rot else ""
        halo = ' paint-order="stroke" stroke="#fff" stroke-width="%.2f" stroke-linejoin="round"' % (size * 0.32) if bg else ""
        self.items.append(f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size:.2f}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}" dominant-baseline="middle"{tr}{halo}>{t}</text>')

    lab = 1.0   # cotas: valor rotulado = longitud × lab (2 en las hojas a escala 1:100 con las cotas al doble)

    def fmt(self, v): return f"{v * self.lab:.2f}".replace(".", ",")

    def dim(self, a, b, t=None, off=-0.35, color=DIM, size=3.0, tpos=0.5):
        """Cota: líneas de referencia desde el objeto, línea de cota paralela a ab desplazada off metros
        (a la izquierda de a→b) y topes inclinados a 45°. t = texto (por defecto, la longitud)."""
        t = t or self.fmt(ln(sub(b, a)))
        u = nrm(sub(b, a)); n = (-u[1], u[0]); sg = 1 if off > 0 else -1
        pa, pb = add(a, mul(n, off)), add(b, mul(n, off))
        gap, over = 0.6 / self.s, 1.2 / self.s   # hueco junto al objeto y prolongación tras la cota (en metros)
        for p, q in ((a, pa), (b, pb)):
            self.line(add(p, mul(n, sg * gap)), add(q, mul(n, sg * over)), color, 0.22)
        self.line(pa, pb, color, 0.3)
        tk = mul(nrm(add(u, n)), 1.3 / self.s)   # tope: trazo corto a 45°
        for q in (pa, pb): self.line(sub(q, tk), add(q, tk), color, 0.45)
        rot = -math.degrees(math.atan2(u[1], u[0]))
        if rot > 90: rot -= 180
        if rot <= -90: rot += 180
        m = add(pa, mul(sub(pb, pa), tpos))
        self.text(m, t, size=size, color=color, rot=rot, bg=True)

    def seglabel(self, a, b, t=None, off=0.2, color=DIM, size=3.0, frac=0.5):
        """Medida escrita junto a un tramo (sin línea de cota), desplazada off metros a la izquierda de a→b."""
        t = t or self.fmt(ln(sub(b, a)))
        u = nrm(sub(b, a)); n = (-u[1], u[0])
        rot = -math.degrees(math.atan2(u[1], u[0]))
        if rot > 90: rot -= 180
        if rot <= -90: rot += 180
        self.text(add(add(a, mul(sub(b, a), frac)), mul(n, off)), t, size=size, color=color, rot=rot, bg=True)

    def labels(self, named, segs, semis, color=None, size=3.4, dist=3.6, force=None):
        """Nombres de los puntos en rojo, colocados en la dirección más libre de líneas (y con halo blanco)."""
        color = color or RED
        for p, t in named:
            dirs = []
            for a, b in segs:
                if ln(sub(a, p)) < 1e-6: dirs.append(sub(b, a))
                elif ln(sub(b, p)) < 1e-6: dirs.append(sub(a, b))
                else:
                    ab, ap = sub(b, a), sub(p, a); k = (ab[0] * ap[0] + ab[1] * ap[1]) / (ln(ab) ** 2)
                    if 0 < k < 1 and ln(sub(ap, mul(ab, k))) < 1e-6: dirs += [sub(a, p), sub(b, p)]
            for sm in semis:
                for a0, a1 in ((sm["a0"], sm["a1"]), (sm["a1"], sm["a0"])):
                    if ln(sub(polar(sm["c"], sm["r"], a0), p)) < 1e-6: dirs.append(sub(polar(sm["c"], sm["r"], a0 + (a1 - a0) * 0.08), p))
            angs = [math.degrees(math.atan2(d[1], d[0])) for d in dirs]
            def free(a): return min([abs((a - b + 180) % 360 - 180) for b in angs] or [180])
            best = (force or {}).get(t) if (force or {}).get(t) is not None else max(range(0, 360, 10), key=lambda a: (free(a), -abs(((a - 225) + 180) % 360 - 180)))  # empate: abajo a la izquierda
            w = 0.35 * size * len(t)   # media anchura aproximada del rótulo (mm)
            dx, dy = math.cos(math.radians(best)), -math.sin(math.radians(best))
            r = dist + abs(dx) * w * 0.8
            self.dot(p, INK, 0.55)
            self.text(p, t, dx * r, dy * r, size, color, bg=True)

    def svg(self, cls=""):
        return (f'<svg class="{cls}" xmlns="http://www.w3.org/2000/svg" width="{self.w}mm" height="{self.h}mm" viewBox="0 0 {self.w} {self.h}" '
                f'font-family="Atkinson Hyperlegible, DejaVu Sans, sans-serif">' + "".join(self.items) + "</svg>")


# ------------------------------------------------------------------ plano 1: dibujo completo
SEGS1 = [(A, B), (B, C), (C, D), (D, A), (M1, E), (E, B), (M2, F), (F, B), (M4, J), (J, D), (M3, G), (G, I), (I, M3), (H, I)]
SEMIS1 = [S_INF, S_DER, S_IZQ, S_SUP]
NAMES1 = [(A, "A"), (B, "B"), (C, "C"), (D, "D"), (E, "E"), (F, "F"), (G, "G"), (J, "J"), (H, "H"), (I, "I"),
          (M1, "M1"), (M2, "M2"), (M3, "M3"), (M4, "M4")]


def draw_plan1(f, color=INK, w=0.7, labels=True, dims=True):
    for a, b in SEGS1: f.line(a, b, color, w)
    for sm in SEMIS1: f.semi(sm, color, w)
    if labels: f.labels(NAMES1, SEGS1, SEMIS1, None if color == INK else color, force={"M2": 235, "M4": 315})
    if dims:
        f.dim(D, C, off=0.38, tpos=0.27)       # lado de arriba, por fuera (texto a un lado del trazo M3G)
        f.dim(B, C, off=0.6, tpos=0.3)          # lado derecho, por dentro
        f.dim(A, M1, off=0.45)                 # M1, por dentro
        f.dim(M4, D, off=-0.3)                 # M4, por dentro
        f.seglabel(M1, E, off=-0.22); f.seglabel(M2, F, off=0.2); f.seglabel(M4, J, off=-0.2)
        f.seglabel(M3, G, off=0.22, frac=0.27); f.seglabel(H, I, off=0.2)


# ------------------------------------------------------------------ plano de prácticas (nuevo)
PA, PB, PC, PD = P(0, 0), P(4, 0), P(4, 3), P(0, 3)
PM1, PE = P(2, 0), P(2, -2)                 # abajo: mediatriz de AB, E a 2 m
PM2, PG = P(4, 1.5), P(5.5, 1.5)            # derecha: mediatriz de BC, G a 1,5 m
PP, PQ = P(0, 1), P(-2, 1)                  # izquierda: P a 1 m de A, dos radios, Q a 2 m
PM3 = P(2, 3)                               # arriba: semicírculo sobre DC, centro por mediatriz
PSEMI = semicircle(PD, PC, PM1)
PSEGS = [(PA, PB), (PB, PC), (PC, PD), (PD, PA), (PA, PE), (PE, PB), (PB, PG), (PG, PC), (PP, PQ), (PQ, PD)]
PNAMES = [(PA, "A"), (PB, "B"), (PC, "C"), (PD, "D"), (PE, "E"), (PG, "G"), (PP, "P"), (PQ, "Q"), (PM1, "M1"), (PM2, "M2"), (PM3, "M3")]


def draw_practice(f, color=INK, w=0.7, labels=True, dims=True):
    for a, b in PSEGS: f.line(a, b, color, w)
    f.semi(PSEMI, color, w)
    f.line(PM1, PE, color, 0.3, "1.2 1"); f.line(PM2, PG, color, 0.3, "1.2 1")
    if labels: f.labels(PNAMES, PSEGS + [(PM1, PE), (PM2, PG)], [PSEMI], force={"P": 320, "A": 250})
    if dims:
        f.dim(PA, PB, off=0.4)                 # base, por dentro
        f.dim(PP, PD, off=-0.6)                # P-D, por dentro
        f.dim(PA, PP, off=0.35)                # A-P, por fuera
        f.seglabel(PP, PQ, off=-0.2); f.seglabel(PM1, PE, off=-0.22); f.seglabel(PM2, PG, off=0.2)
        f.text(add(PM3, P(0, 1.0)), "R = " + f.fmt(PSEMI["r"]), 0, 0, 3.0, DIM, bg=True)


# ------------------------------------------------------------------ hojas A4 a escala 1:100 (cotas al doble del plano del patio)
S50 = 20.0  # mm de papel por metro del plano del patio (= 1 cm por metro rotulado, con las cotas al doble)


def ruler10(f, x, y):
    """Barra de control de 10 cm en coordenadas de papel (mm)."""
    it = [f'<rect x="{x}" y="{y}" width="100" height="3" fill="none" stroke="{INK}" stroke-width="0.3"/>']
    for i in range(11):
        it.append(f'<line x1="{x + 10 * i}" y1="{y}" x2="{x + 10 * i}" y2="{y + (4.5 if i % 5 == 0 else 3)}" stroke="{INK}" stroke-width="0.3"/>')
        if i % 2 == 0: it.append(f'<rect x="{x + 10 * i}" y="{y}" width="10" height="3" fill="{INK}"/>' if i < 10 else "")
    it.append(f'<text x="{x + 50}" y="{y + 8.5}" font-size="3" text-anchor="middle" fill="{INK}">Control de escala: esta barra debe medir 10 cm (imprime al 100 %, sin «ajustar a la página»)</text>')
    f.items += it


def sheet_plan(title, subtitle, draw, box, table, steps, checks=None):
    """Tres páginas: plano acotado, pasos en el folio, hoja para dibujar."""
    (x0, y0), (x1, y1) = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    pages = []
    # 1) plano acotado
    f = Fig(S50, 105 - S50 * cx, 150 + S50 * cy); f.lab = 2
    draw(f)
    ruler10(f, 55, 252)
    pages.append(f"""<section class="page">
  <header><div class="tag">Intervención Operativa · Replanteo a escala</div><h1>{title}</h1><p>{subtitle}</p></header>
  <div class="sheet">{f.svg()}</div>
  <div class="foot"><b>Escala 1:100</b> · cada centímetro del papel es un metro · cotas en metros</div>
</section>""")
    # 2) tabla y pasos
    rows = "".join(f"<tr><td>{a}</td><td>{b}</td><td><b>{c}</b></td></tr>" for a, b, c in table)
    li = "".join(f"<li>{s}</li>" for s in steps)
    pages.append(f"""<section class="page text">
  <header><div class="tag">Intervención Operativa · Replanteo a escala</div><h1>{title}: del suelo al folio</h1>
  <p>Material: compás, regla graduada, escuadra solo para comprobar al final, lápiz duro y goma. Los arcos auxiliares, finos; las líneas definitivas, marcadas.</p></header>
  <h2>Medidas a escala 1:100</h2>
  <p class="note"><b>Cada centímetro del papel es un metro</b>: la cota en metros es lo que mides en centímetros en el folio. Por ejemplo, 5,00 m → 5 cm.</p>
  <table><thead><tr><th>Elemento</th><th>Cota</th><th>En el folio</th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Orden de trabajo</h2>
  <ol class="steps">{li}</ol>
  <p class="note">Tolerancia en el folio: ±1 mm. Si las diagonales del rectángulo no coinciden, revisa las perpendiculares antes de seguir.</p>
</section>""")
    # 3) hoja para dibujar: solo la línea base y el punto A
    g = Fig(S50, 105 - S50 * cx, 150 + S50 * cy)
    g.line(P(x0 - 0.2, 0), P(x1 + 0.2, 0), INK, 0.35)
    g.cross(P(0, 0), INK, 1.8, 0.5); g.text(P(0, 0), "A", -3.5, 4, 3.6)
    g.text(P(x1 + 0.2, 0), "línea base", -1, -3, 3, "#6b747c", 400, "end")
    ruler10(g, 55, 252)
    pages.append(f"""<section class="page">
  <header><div class="tag">Hoja de trabajo · Escala 1:100</div><h1>{title}: dibújalo con compás</h1>
  <p class="who">Nombre: ______________________________ &nbsp; Grupo: ________ &nbsp; Fecha: ____________</p></header>
  <div class="sheet">{g.svg()}</div>
  <div class="foot">Empieza en A, sobre la línea base. Deja los arcos auxiliares a la vista: el profesor los revisará.</div>
</section>""")
    if checks:
        pages.append(check_page(title, draw, checks, 2, "m → cm en el folio",
                                "Escala 1:100: el valor en metros es lo que debe medir en centímetros en el folio. Si una medida se aleja más de 1 mm, "
                                "o las dos de una pareja no coinciden, revisa las perpendiculares y los puntos de esa parte antes de seguir.",
                                ((box[0][0] - 0.2, box[0][1] - 0.2), (box[1][0] + 0.2, box[1][1] + 0.2))))
    return pages


TABLE1 = [("Lado AB (y DC)", "5,00 m", "5 cm"), ("Lado AD (y BC)", "7,00 m", "7 cm"), ("Puntos medios M1 y M3", "2,50 m", "2,5 cm"),
          ("Puntos medios M2 y M4", "3,50 m", "3,5 cm"), ("Trazos M1E, M2F, M4J", "4,00 m", "4 cm"), ("Trazo M3G", "5,00 m", "5 cm"),
          ("H, en la mitad de M3G", "técnica del punto medio", "sin medir"), ("Cateto HI", "4,00 m", "4 cm"), ("Radios iguales en A y B", "3,00 m", "3 cm"),
          ("Dos radios: marcas / arcos", "1,50 m / 3,00 m", "1,5 cm / 3 cm"), ("Diagonales AC = BD (comprobación)", "8,60 m", "8,6 cm"),
          ("Radios de los semicírculos (salen solos)", "2,00 · 2,66 · 2,66 · 2,36 m", "no se miden")]
STEPS1 = ["<b>Línea base:</b> desde A mide 5 cm y marca B.",
          "<b>Perpendicular en A</b> (radios iguales, abertura 3 cm): arco desde A → 1; desde 1 → 2; desde 2 → 3; desde 2 y 3 → 4. La recta A-4 es la perpendicular. Mide 7 cm: D.",
          "<b>Perpendicular en B</b> igual (o con la terna 3-4-5 cm). Mide 7 cm: C. Une D y C.",
          "<b>Comprueba:</b> DC = 5 cm y diagonales iguales, 8,6 cm.",
          "<b>Puntos medios:</b> M1 y M3 a 2,5 cm de las esquinas; M2 y M4 a 3,5 cm.",
          "<b>Triángulo de abajo:</b> en M1, dos radios (marcas a 1,5 cm, arcos de 3 cm) hacia fuera; a 4 cm, E. Une M1E y EB. Centro del semicírculo: punto medio de M1E con la técnica del punto medio. Pincha en el centro y abre el compás hasta E: el radio sale solo.",
          "<b>Triángulo de la derecha:</b> igual en M2; F a 4 cm. Une M2F y FB. Semicírculo sobre FB con centro en su punto medio (técnica del punto medio).",
          "<b>Triángulo de la izquierda:</b> igual en M4; J a 4 cm. Une M4J y JD. Semicírculo sobre JD.",
          "<b>Triángulo de arriba:</b> en M3, dos radios hacia arriba; G a 5 cm. Punto medio de M3G con la técnica del punto medio: es H, y la recta de los cruces ya es la perpendicular. Sobre ella, I a 4 cm de H. Une HI, GI e I-M3. Semicírculo sobre GI."]
TABLEP = [("Lado AB (y DC)", "8,00 m", "8 cm"), ("Lado AD (y BC)", "6,00 m", "6 cm"), ("Radios iguales en A", "3,00 m", "3 cm"),
          ("Terna 3-4-5 en B", "3,00 · 4,00 · 5,00 m", "3 · 4 · 5 cm"), ("Mediatrices (técnica del punto medio)", "radio > mitad del lado", "5 cm en AB y DC · 4 cm en BC"),
          ("M1E (abajo, sobre la mediatriz)", "4,00 m", "4 cm"), ("M2G (derecha, sobre la mediatriz)", "3,00 m", "3 cm"),
          ("AP (izquierda)", "2,00 m", "2 cm"), ("Dos radios en P: marcas / arcos", "1,50 m / 3,00 m", "1,5 cm / 3 cm"), ("PQ", "4,00 m", "4 cm"),
          ("Radio del semicírculo de arriba (sale solo)", "4,00 m", "no se mide"), ("Diagonales AC = BD (comprobación)", "10,00 m", "10 cm")]
STEPSP = ["<b>Línea base:</b> desde A mide 8 cm y marca B.",
          "<b>Perpendicular en A</b> con radios iguales (abertura 3 cm). Mide 6 cm: D.",
          "<b>Perpendicular en B</b> con la terna 3-4-5: marca 3 cm sobre la base hacia A; arco de 4 cm con centro en B y de 5 cm con centro en la marca. Por el cruce, 6 cm: C. Une D y C.",
          "<b>Comprueba:</b> DC = 8 cm y diagonales iguales, 10 cm (otra terna 3-4-5).",
          "<b>Abajo, mediatriz de AB</b> sin medir: con una abertura de 5 cm (más de la mitad de AB), arcos desde A y desde B por arriba y por abajo. La recta de los cruces corta AB en M1 y ya es la perpendicular. Sobre ella, 4 cm hacia abajo: E. Une EA y EB.",
          "<b>Derecha, mediatriz de BC:</b> igual, con 4 cm de abertura, arcos desde B y desde C. Corta BC en M2. Sobre la recta, 3 cm hacia fuera: G. Une GB y GC.",
          "<b>Izquierda, dos radios en P:</b> P a 2 cm de A sobre AD. Marcas a 1,5 cm a cada lado y arcos de 3 cm hacia fuera. Por el cruce, 4 cm: Q. Une PQ y QD.",
          "<b>Arriba, semicírculo sobre DC:</b> busca el punto medio de DC con la técnica del punto medio, con 5 cm de abertura (M3). Pincha en M3, abre hasta D y traza el semicírculo hacia fuera hasta C."]


# ------------------------------------------------------------------ guía del replanteo a tamaño real (plano 1)
def fig_plan_state(done_steps, current, w=170, h=125):
    """Dibujo del plano con lo ya hecho en gris, lo del paso en negro y los auxiliares en color."""
    f = Fig.fit(FOCUS.get(current, [P(-2.6, -2.4), P(5.1, 6.9)]), w, h, 4)
    STEP = step_drawings()
    for k in done_steps: STEP[k](f, GREY, False)
    STEP[current](f, INK, True)
    return f.svg("fig")


# zona del plano que se amplía en la figura de cada paso
FOCUS = {1: [P(-0.7, -1.0), P(3.2, 1.0)], 2: [P(-1.0, -0.6), P(3.0, 4.0)], 3: [P(-0.5, -0.6), P(3.6, 4.0)], 4: [P(-0.6, -0.6), P(3.1, 4.0)],
         5: [P(-0.8, -0.6), P(3.3, 4.0)], 6: [P(-0.6, -2.4), P(2.9, 0.8)], 7: [P(1.5, -1.3), P(5.3, 3.6)], 8: [P(-2.8, -0.1), P(1.3, 4.7)],
         9: [P(-0.4, 3.0), P(4.4, 6.8)]}


def step_drawings():
    def lbl(f, p, t, dx, dy, col): f.dot(p, col, 0.6); f.text(p, t, dx, dy, 3.4, col)

    def s1(f, col, aux):
        f.line(A, B, col, 0.8); lbl(f, A, "A", -3, 3, col); lbl(f, B, "B", 3, 3, col)
        if aux: f.dim(A, B, "2,50 m", -0.45)

    def perp(f, q, col, aux, end, name, other, nend):
        if aux:
            c = AUX[0]
            f.arc(q["o"], q["r"], ang(q["o"], q["p1"]) - 8 * (1 if q is EQ_A else -1), ang(q["o"], q["p3"]) + 10 * (1 if q is EQ_A else -1), c, 0.45)
            for a, b in ((q["p1"], q["p2"]), (q["p2"], q["p3"]), (q["p2"], q["p4"]), (q["p3"], q["p4"])): f.arc_to(a, b, 16, c)
            for k, t in (("p1", "1"), ("p2", "2"), ("p3", "3"), ("p4", "4")): f.cross(q[k], c); f.text(q[k], t, 3, -2.5, 3, c)
        f.line(q["o"], end, col, 0.8); lbl(f, end, name, nend[0], nend[1], col)
        if aux: f.dim(q["o"], end, "3,50 m", other)

    def s2(f, col, aux): perp(f, EQ_A, col, aux, D, "D", 0.45, (-3, -3))

    def s3(f, col, aux):
        perp(f, EQ_B, col, aux, C, "C", -0.45, (3, -3)); f.line(D, C, col, 0.8)

    def s4(f, col, aux):
        if aux:
            f.line(A, C, AUX[1], 0.4, "1.5 1"); f.line(B, D, AUX[1], 0.4, "1.5 1")
            f.text(mid(A, C), "AC = BD = 4,30 m", 0, -4, 3.2, AUX[1], bg=True); f.dim(D, C, "2,50 m", 0.4)

    def s5(f, col, aux):
        for p, t, dx, dy in ((M1, "M1", 0, 4), (M2, "M2", 5, 0), (M3, "M3", 0, -4), (M4, "M4", -5, 0)):
            f.cross(p, col, 1.6, 0.6 if aux else 0.45); f.text(p, t, dx, dy, 3.2, col)
        if aux: f.dim(A, M1, "1,25", 0.35); f.dim(B, M2, "1,75", 0.35)

    def tri(f, col, aux, q, end, name, nd, lines, mids, semi, rad, extra=None):
        if aux:
            c = AUX[0]
            f.arc_to(q["m"], q["k1"], 20, c); f.arc_to(q["m"], q["k2"], 20, c)
            f.arc_to(q["k1"], q["x"], 16, c); f.arc_to(q["k2"], q["x"], 16, c)
            f.cross(q["k1"], c); f.cross(q["k2"], c); f.cross(q["x"], c); f.text(q["x"], "3", 3, -2.5, 3, c)
        f.line(q["m"], end, col, 0.8); lbl(f, end, name, nd[0], nd[1], col)
        for a, b in lines: f.line(a, b, col, 0.8)
        if extra: extra(f, col, aux)
        if aux:
            for (p, qq, r), c in zip(mids, AUX[1:]):
                g = mid_info(p, qq, r)
                for cen, tgt in ((p, g["x1"]), (p, g["x2"]), (qq, g["x1"]), (qq, g["x2"])): f.arc_to(cen, tgt, 12, c)
                f.line(g["x1"], g["x2"], c, 0.35, "1.2 0.9")
        f.semi(semi, col, 0.8)
        if aux:
            f.dot(semi["c"], AUX[3], 0.7); f.text(semi["c"], "O", -3, -3, 3.2, AUX[3])
            f.text(polar(semi["c"], semi["r"] * 0.55, (semi["a0"] + semi["a1"]) / 2), rad, 0, 0, 2.8, AUX[3], bg=True)

    def s6(f, col, aux):
        tri(f, col, aux, EQ_INF, E, "E", (3.2, 2), [(E, B)], [(M1, E, 1.3)], S_INF, "R 1,00")
        if aux: f.dim(M1, E, "2,00 m", -0.35)

    def s7(f, col, aux):
        tri(f, col, aux, EQ_DER, F, "F", (3.5, -1.5), [(F, B)], [(F, B, 1.7)], S_DER, "R 1,33")
        if aux: f.dim(M2, F, "2,00 m", 0.3)

    def s8(f, col, aux):
        tri(f, col, aux, EQ_IZQ, J, "J", (-3, -2.5), [(J, D)], [(J, D, 1.7)], S_IZQ, "R 1,33")
        if aux: f.dim(M4, J, "2,00 m", -0.3)

    def s9(f, col, aux):
        def extra(f, col, aux):
            f.line(H, I, col, 0.8); lbl(f, H, "H", -3.5, 0, col); lbl(f, I, "I", 3.3, 1.5, col)
            if aux: f.dim(M3, G, "2,50 m", -0.3); f.dim(H, I, "2,00 m", 0.3)
        tri(f, col, aux, EQ_SUP, G, "G", (-3, -2.5), [(G, I), (I, M3)], [(M3, G, 1.6), (G, I, 1.5)], S_SUP, "R 1,18", extra)

    return {1: s1, 2: s2, 3: s3, 4: s4, 5: s5, 6: s6, 7: s7, 8: s8, 9: s9}


def fig_method(kind, w=80, h=54):
    c, c2, c3 = AUX[0], AUX[1], AUX[2]
    if kind == "radios":
        o, q = P(0, 0), equal_radii(P(0, 0), 0, 1, 1.0)
        f = Fig.fit([P(-0.3, -0.25), P(1.5, 1.95)], w, h, 4)
        f.line(P(-0.3, 0), P(1.5, 0), INK, 0.6)
        f.arc(o, 1.0, -8, 130, c, 0.45)
        for a, b in ((q["p1"], q["p2"]), (q["p2"], q["p3"]), (q["p2"], q["p4"]), (q["p3"], q["p4"])): f.arc_to(a, b, 16, c)
        for k, t in (("p1", "1"), ("p2", "2"), ("p3", "3"), ("p4", "4")): f.cross(q[k], c); f.text(q[k], t, 3, -2.5, 3, c)
        f.line(o, P(0, 1.85), ORANGE, 0.8); f.dot(o); f.text(o, "A", -3, 3, 3.4)
    elif kind == "dos":
        m = P(0, 0); k1, k2, x = P(-0.5, 0), P(0.5, 0), P(0, math.sqrt(1 - 0.25))
        f = Fig.fit([P(-1.1, -0.25), P(1.1, 1.15)], w, h, 4)
        f.line(P(-1.1, 0), P(1.1, 0), INK, 0.6)
        f.arc_to(m, k1, 20, c); f.arc_to(m, k2, 20, c); f.arc_to(k1, x, 16, c2); f.arc_to(k2, x, 16, c2)
        for p, t in ((k1, "1"), (k2, "2"), (x, "3")): f.cross(p, c if t != "3" else c2); f.text(p, t, 3, -2.5, 3, c if t != "3" else c2)
        f.line(m, P(0, 1.1), ORANGE, 0.8); f.dot(m); f.text(m, "M", 0, 3.5, 3.4)
        f.text(P(-0.25, 0), "r", 0, -2.5, 2.8, c); f.text(P(-0.25, 0.43), "R", -2.5, 0, 2.8, c2)
    elif kind == "345":
        a, k, x = P(0, 0), P(1.5, 0), P(0, 2)
        f = Fig.fit([P(-0.4, -0.3), P(1.9, 2.3)], w, h, 4)
        f.line(P(-0.4, 0), P(1.9, 0), INK, 0.6)
        f.arc(a, 2.0, 78, 102, c, 0.45); f.arc(k, 2.5, 117, 135, c2, 0.45)
        f.line(k, x, c2, 0.35, "1.2 0.9"); f.cross(k, INK)
        f.line(a, P(0, 2.2), ORANGE, 0.8); f.dot(a); f.text(a, "A", -3, 3, 3.4); f.text(k, "1,5 m", 0, 3.5, 3)
        f.text(P(0, 1.0), "2 m", -5, 0, 3, c); f.text(mid(k, x), "2,5 m", 6, -1, 3, c2)
    else:  # punto medio
        a, b = P(0, 0), P(1.6, 0); g = mid_info(a, b, 1.1)
        f = Fig.fit([P(-0.2, -1.0), P(1.8, 1.0)], w, h, 4)
        f.line(a, b, INK, 0.6)
        for cen, col in ((a, c), (b, c2)):
            for t in (g["x1"], g["x2"]): f.arc_to(cen, t, 13, col)
        f.line(g["x1"], g["x2"], ORANGE, 0.7); f.dot(a); f.dot(b); f.text(a, "A", -3, 3, 3.4); f.text(b, "B", 3, 3, 3.4)
        f.cross(g["m"], INK); f.text(g["m"], "M", 3.5, 3.5, 3.4)
    return f.svg("mfig")


def fig_zone(w=80, h=86):
    f = Fig.fit([P(-3.6, -3.6), P(6.3, 8.1)], w, h, 3)
    f.poly([P(-3.25, -2.98), P(5.75, -2.98), P(5.75, 7.52), P(-3.25, 7.52)], "#6b747c", 0.5, close=True, dash="2 1.2")
    f.poly([P(-2.329, -2.0), P(4.829, -2.0), P(4.829, 6.554), P(-2.329, 6.554)], AUX[0], 0.35, close=True, dash="1 1")
    draw_plan1(f, GREY, 0.5, labels=False, dims=False)
    f.dot(A, ORANGE, 0.9); f.text(A, "A", 3, 3.5, 3.4, ORANGE)
    f.line(P(-3.25, 0), A, ORANGE, 0.4, "1 0.8"); f.line(P(0, -2.98), A, ORANGE, 0.4, "1 0.8")
    f.text(P(-1.6, 0), "3,25 m", 0, -2.5, 2.8, ORANGE, bg=True); f.text(P(0, -1.5), "2,98 m", 7, 0, 2.8, ORANGE, bg=True)
    f.text(P(1.25, -2.98), "zona 9,00 m", 0, 3.2, 2.8, "#6b747c"); f.text(P(5.75, 2.27), "10,50 m", 3, 0, 2.8, "#6b747c", rot=-90)
    f.text(P(1.25, 6.554), "dibujo 7,16 × 8,55 m", 0, -2.5, 2.8, AUX[0], bg=True)
    return f.svg("mfig")


def final_fig():
    f = Fig.fit([P(-2.6, -2.4), P(5.1, 6.9)], 170, 150, 4)
    draw_plan1(f, INK, 0.8, labels=True, dims=False)
    return f.svg("fig")


def guide_html():
    plan = Fig.fit([P(-2.7, -2.6), P(5.2, 7.0)], 170, 190, 4)
    draw_plan1(plan)
    methods = [
        ("radios", "Radios iguales", "Para una <b>esquina o el extremo</b> de una línea, sin prolongarla.",
         ["Centro en A y un radio cualquiera (1,50 m en el plano): arco que corta la base en 1.",
          "Sin cambiar el radio: centro en 1 → corta el arco en 2; centro en 2 → en 3.",
          "Desde 2 y desde 3, dos arcos más: se cruzan en 4.", "La recta A-4 es perpendicular a la base."]),
        ("dos", "Dos radios", "Para un <b>punto intermedio</b> M de la línea (por ejemplo, un punto medio).",
         ["Radio corto r (0,75 m) con centro en M: dos marcas en la línea, 1 y 2.",
          "Radio mayor R (1,50 m): un arco desde 1 y otro desde 2, hacia fuera. Se cruzan en 3.", "La recta M-3 es la perpendicular."]),
        ("345", "Terna 3-4-5", "Pitágoras: 3² + 4² = 5². Valen 30-40-50 cm, 1,5-2-2,5 m o 3-4-5 m (triángulos semejantes).",
         ["Sobre la base, desde A, mide 1,5 m y marca.", "Arco de 2 m con centro en A y arco de 2,5 m con centro en la marca.",
          "Donde se cruzan pasa la perpendicular por A. Comprobación: 1,5² + 2² = 6,25 = 2,5²."]),
        ("medio", "Técnica del punto medio", "Cuando <b>no conocemos el punto medio</b> de un segmento AB.",
         ["Radio mayor que la mitad de AB: arcos desde A por los dos lados.", "Con el mismo radio, arcos desde B: se cruzan en dos puntos.",
          "La recta de los cruces es perpendicular a AB y lo corta en su punto medio M."]),
    ]
    mhtml = "".join(f"""<div class="method">{fig_method(k)}<div><h3>{t}</h3><p>{d}</p><ol>{''.join(f'<li>{s}</li>' for s in st)}</ol></div></div>""" for k, t, d, st in methods)
    steps = [
        (1, "Paso 1 · Línea base AB", ["GALía2 sujeta el cero de la cinta en A; GALía3 marca B a 2,50 m.", "Con los dos extremos marcados, GALía2 y GALía3 tensan el cordel y GALía traza AB."]),
        (2, "Paso 2 · Perpendicular en A", ["Radios iguales con 1,50 m: arco desde A → 1; desde 1 → 2; desde 2 → 3.", "Desde 2 y desde 3, dos arcos de 1,50 m: se cruzan en 4.", "Por la recta A-4 se miden 3,50 m: D. Se traza AD."]),
        (3, "Paso 3 · Perpendicular en B y cierre", ["Radios iguales en B, hacia el mismo lado: puntos 1, 2, 3 y 4.", "Por la recta B-4, 3,50 m: C. Se trazan BC y DC."]),
        (4, "Paso 4 · Comprobación", ["DC debe medir 2,50 m.", "Diagonales iguales: AC = BD = 4,30 m. Si difieren más de 2 cm, repite las perpendiculares."]),
        (5, "Paso 5 · Puntos medios", ["En los lados de 2,50 m, a 1,25 m: M1 abajo y M3 arriba.", "En los de 3,50 m, a 1,75 m: M2 a la derecha y M4 a la izquierda."]),
        (6, "Paso 6 · Triángulo inferior", ["Dos radios en M1 (marcas a 0,75 m, arcos de 1,50 m) hacia abajo: punto 3.", "Desde M1, pasando por 3, se miden 2,00 m: E. Se trazan M1E y EB.",
                                             "Centro del semicírculo: punto medio de M1E (técnica del punto medio, radio 1,30 m) → O.", "El radio no se mide: tiza en E y cordel en O; con el cordel tenso se gira hasta M1."]),
        (7, "Paso 7 · Triángulo derecho", ["Dos radios en M2 hacia fuera; F a 2,00 m. Se trazan M2F y FB.", "Semicírculo sobre FB (2,66 m): centro O en su punto medio (técnica del punto medio, radio 1,70 m).", "Tiza en F, cordel en O y se gira hasta B."]),
        (8, "Paso 8 · Triángulo izquierdo", ["Dos radios en M4 hacia fuera; J a 2,00 m. Se trazan M4J y JD.", "Semicírculo sobre JD: centro O en su punto medio (técnica del punto medio).", "Tiza en J, cordel en O y se gira hasta D."]),
        (9, "Paso 9 · Triángulo superior", ["Dos radios en M3 hacia arriba; G a 2,50 m. Se traza M3G.", "Técnica del punto medio en M3G (radio 1,60 m): la recta de los cruces corta M3G en H y ya es perpendicular.",
                                             "Sobre esa recta, desde H, 2,00 m hacia la derecha: I. Se trazan HI, GI e I-M3.", "Semicírculo sobre GI: centro O por la técnica del punto medio; tiza en G, cordel en O, se gira hasta I (radio 1,18 m)."]),
    ]
    blocks = [f"""<section class="step"><h2>{t}</h2><div class="stepfig">{fig_plan_state(range(1, k), k, 170, 86)}</div><ol>{''.join(f'<li>{x}</li>' for x in st)}</ol></section>""" for k, t, st in steps]
    first = blocks[0]   # el paso 1 va en la página del paso 0
    shtml = "".join(f'<section class="page text">{"".join(blocks[i:i + 2])}</section>' for i in range(1, len(blocks), 2))
    legend = f"""<p class="legend"><span style="color:{INK}">━</span> trazos de este paso &nbsp; <span style="color:{GREY}">━</span> ya trazado &nbsp;
      <span style="color:{AUX[0]}">━</span> <span style="color:{AUX[1]}">━</span> <span style="color:{AUX[2]}">━</span> arcos y rectas auxiliares (cada construcción, un color) &nbsp; <span style="color:{AUX[3]}">●</span> centro O del semicírculo</p>"""
    return f"""<section class="page text">
  <header><div class="tag">Intervención Operativa · Profesor Joaquín Rueda</div><h1>Replanteo del plano 1 a tamaño real</h1>
  <p>Guía del proceso completo en el asfalto con cordel, tiza y cinta métrica, paso a paso, como en las escenas de GALía.</p></header>
  <h2>¿Para qué sirve replantear?</h2>
  <p>En una emergencia hay que montar campamentos, hospitales de campaña y puestos de mando. Todo parte de una <b>línea base</b>: las filas y las calles salen perpendiculares a ella, las distancias de seguridad son iguales y cada anclaje de las carpas va en su punto exacto. Un error de 5° al principio se convierte en casi 80 cm de desvío a 9 m.</p>
  <h2>Material y equipo</h2>
  <ul><li>Cinta métrica, cordel con una tiza cilíndrica atada (el compás), tiza y calculadora.</li>
  <li>Zona limpia, señalizada y sin tráfico.</li>
  <li>Tres papeles fijos: <b>GALía2</b> sujeta el centro de los arcos y el cero de la cinta; <b>GALía3</b> lleva la tiza en los arcos y el extremo de la cinta; <b>GALía</b> dirige y traza las rectas mientras las otras dos tensan el cordel.</li>
  <li>Compás de cordel: una mano fija el cordel en el centro, pegado al suelo; la otra lo tensa y gira marcando con la tiza.</li>
  <li>Rectas: con el cordel atirantado entre las dos marcas, se pasa la tiza por su borde, sin moverlo. Una línea se traza en definitivo cuando tiene sus dos extremos marcados.</li></ul>
  <h2>El plano 1</h2>
  <p>Rectángulo de 2,50 × 3,50 m con un triángulo rectángulo en cada lado. Cada triángulo sale de un trazo perpendicular desde el punto medio del lado y lleva un semicírculo con el centro en la mitad de uno de sus lados. Cotas en metros.</p>
</section>
<section class="page text"><div class="planfig">{plan.svg("fig")}</div>
  <p class="note">Regla: en una esquina, radios iguales o 3-4-5; en un punto medio, dos radios; si no conocéis el punto medio, la técnica del punto medio. Los semicírculos no se miden: tiza en un extremo del diámetro y cordel en el centro.</p>
</section>
<section class="page text"><h1 class="h1s">Métodos para trazar perpendiculares</h1>{mhtml}</section>
<section class="page text"><h2>Paso 0 · Centrar el replanteo en la zona</h2>
  <div class="method">{fig_zone()}<div><ol>
  <li>Antes de dibujar, se centra el replanteo en la zona asignada para que no molesten paredes u obstáculos.</li>
  <li>Zona: 9,00 × 10,50 m. Dibujo completo con los semicírculos: 7,16 × 8,55 m. Cabe.</li>
  <li>Lo que sobra se reparte a partes iguales: unos 92 cm a cada lado y unos 98 cm arriba y abajo.</li>
  <li>Así A queda a <b>3,25 m</b> del borde izquierdo y a <b>2,98 m</b> del de abajo. Desde ahí empieza todo.</li></ol></div></div>
  {legend}
  {first}
</section>
{shtml}
{check_page("Plano 1", draw_plan1, CHECKS1, 1, "m",
    "Tolerancia en el patio: <b>2 cm</b>. Si una medida se aleja más de 2 cm del valor de la tabla, o las dos de una pareja difieren más de 2 cm, "
    "esa parte está mal: revisa la perpendicular o el punto de donde sale y rehazla antes de seguir. Las diagonales AC y BD se miden al terminar el paso 3; "
    "las demás, al cerrar cada triángulo.", ((-2.6, -2.4), (5.1, 6.9)))}
<section class="page text"><h2>Plano terminado</h2><div class="stepfig">{final_fig()}</div>
  <ol><li>Rectángulo, cuatro triángulos y cuatro semicírculos a tamaño real.</li><li>Tolerancia: ±2 cm. Comprobad lados y diagonales antes de dar el replanteo por bueno.</li>
  <li>Si no habéis podido hacerlo en el patio, practicadlo en el folio a escala 1:100 (hoja «Plano 1 · escala 1:100», con las medidas al doble).</li></ol></section>"""


CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: "Atkinson Hyperlegible", "DejaVu Sans", sans-serif; color: #1d2329; font-size: 10.5pt; line-height: 1.4; }
.page { width: 210mm; height: 297mm; position: relative; overflow: hidden; page-break-after: always; break-after: page; }
.page:last-child { page-break-after: auto; break-after: auto; }
.page header { position: absolute; top: 12mm; left: 15mm; right: 15mm; z-index: 1; }
.text { padding: 14mm 15mm 20mm; }
.text header { position: static; margin-bottom: 4mm; }
.tag { font-family: "Barlow Condensed", "DejaVu Sans Condensed", sans-serif; font-weight: 700; letter-spacing: .14em; text-transform: uppercase; color: #ff6b1a; font-size: 9pt; }
h1 { font-family: "Barlow Condensed", "DejaVu Sans Condensed", sans-serif; font-weight: 700; font-size: 22pt; line-height: 1.05; margin: 1mm 0 1.5mm; }
.h1s { margin-bottom: 4mm; }
h2 { font-family: "Barlow Condensed", "DejaVu Sans Condensed", sans-serif; font-weight: 700; font-size: 15pt; margin: 4mm 0 1.5mm; color: #1d2329; border-bottom: 0.6mm solid #ff6b1a; padding-bottom: .6mm; }
h3 { font-family: "Barlow Condensed", "DejaVu Sans Condensed", sans-serif; font-size: 13pt; margin: 0 0 1mm; }
header p { margin: 0; color: #4a535b; }
p { margin: 1mm 0 2mm; }
.who { margin-top: 3mm; color: #1d2329 !important; }
.sheet { position: absolute; inset: 0; }
.sheet svg { display: block; }
.foot { position: absolute; left: 15mm; right: 15mm; bottom: 19mm; font-size: 9pt; color: #4a535b; text-align: center; }
table { border-collapse: collapse; width: 100%; margin: 1.5mm 0 2.5mm; font-size: 9.5pt; }
th, td { border: 0.25mm solid #c9cfd4; padding: 1mm 2.5mm; text-align: left; }
th { background: #fff1e8; }
td:last-child { color: #c4501a; }
ol, ul { margin: 1mm 0 2mm; padding-left: 6mm; }
li { margin: 0.8mm 0; }
li::marker { color: #ff6b1a; font-weight: 700; }
.note { background: #f4f6f7; border-left: 1mm solid #f2c230; padding: 2mm 3mm; font-size: 9.5pt; }
.steps li { margin: 0.9mm 0; font-size: 10pt; }
.method { display: grid; grid-template-columns: 82mm 1fr; gap: 5mm; align-items: center; margin: 1.5mm 0 3mm; break-inside: avoid; font-size: 10pt; }
.method svg, .stepfig svg, .planfig svg { display: block; margin: 0 auto; }
.method svg { border: 0.25mm solid #e1e5e8; border-radius: 2mm; }
.step { break-inside: avoid; margin-bottom: 4mm; }
.stepfig svg { border: 0.25mm solid #e1e5e8; border-radius: 2mm; }
.legend { font-size: 8.5pt; color: #4a535b; margin: 1mm 0 3mm; }
.pfoot { position: absolute; left: 15mm; right: 15mm; bottom: 6mm; display: flex; justify-content: space-between; align-items: flex-end;
  border-top: 0.35mm solid #ff6b1a; padding-top: 1.5mm; font-size: 7.5pt; line-height: 1.35; color: #4a535b; }
.pfoot b { color: #1d2329; }
.pfoot .pn { font-weight: 700; color: #1d2329; white-space: nowrap; }
.checks td.blank { width: 22mm; }
.checks td, .checks th { padding: 1.8mm 2.5mm; }
.sw { display: inline-block; width: 3mm; height: 3mm; border-radius: 0.6mm; margin-right: 2mm; vertical-align: -0.3mm; }
"""


# ------------------------------------------------------------------ comprobación con diagonales
# Parejas de distancias que deben salir iguales (simetría) o un valor conocido: se miden con la cinta
# entre dos puntos ya marcados.
CHECKS1 = [[("A", A, "C", C), ("B", B, "D", D)], [("A", A, "E", E), ("B", B, "E", E)], [("B", B, "F", F), ("C", C, "F", F)],
           [("A", A, "J", J), ("D", D, "J", J)], [("C", C, "G", G), ("D", D, "G", G)]]
PT = P(2, 5)   # punto más alto del semicírculo del plano de prácticas
CHECKSP = [[("A", PA, "C", PC), ("B", PB, "D", PD)], [("A", PA, "E", PE), ("B", PB, "E", PE)], [("B", PB, "G", PG), ("C", PC, "G", PG)],
           [("D", PD, "T", PT), ("C", PC, "T", PT)], [("A", PA, "Q", PQ)]]


def check_page(title, draw, checks, lab, unit, tol, box):
    """Figura con las diagonales de comprobación (cada pareja de un color) y tabla para anotar lo medido."""
    f = Fig.fit([P(box[0][0], box[0][1]), P(box[1][0], box[1][1])], 180, 118, 4); f.lab = lab
    draw(f, GREY, 0.5, labels=False, dims=False)
    for k, grp in enumerate(checks):
        c = AUX[k % len(AUX)]
        for i, (na, a, nb, b) in enumerate(grp):
            f.line(a, b, c, 0.45, "1.6 1.1")
            f.seglabel(a, b, na + nb, off=0.18 if i == 0 else -0.18, color=c, size=2.8)
    named = {}
    for grp in checks:
        for na, a, nb, b in grp: named[na] = a; named[nb] = b
    f.labels([(p, t) for t, p in named.items()], [], [], size=3.2)
    rows = ""
    for k, grp in enumerate(checks):
        c = AUX[k % len(AUX)]
        v = f.fmt(ln(sub(grp[0][3], grp[0][1])))
        names = " = ".join(na + nb for na, _, nb, _ in grp)
        cm = v.rstrip("0").rstrip(",")
        shown = f"{v} m → {cm} cm" if lab != 1 else f"{v} {unit}"
        rows += (f'<tr><td><span class="sw" style="background:{c}"></span><b>{names}</b></td><td><b>{shown}</b></td>'
                 + '<td class="blank"></td><td class="blank"></td><td class="blank"></td></tr>')
    return f"""<section class="page text">
  <header><div class="tag">Comprobación con diagonales</div><h1>{title}: ¿va bien el replanteo?</h1>
  <p>Con la cinta, mide entre los puntos ya marcados. Cada pareja del mismo color debe salir igual y con el valor de la tabla.</p></header>
  <div class="planfig">{f.svg("fig")}</div>
  <table class="checks"><thead><tr><th>Diagonal</th><th>Debe medir</th><th>Medida 1</th><th>Medida 2</th><th>¿Bien?</th></tr></thead><tbody>{rows}</tbody></table>
  <p class="note">{tol}</p>
</section>"""


def add_footers(html, doc_title):
    """Pie en cada página: módulo, profesor y centro, título del documento y «Página X de N»."""
    pat = re.compile(r'<section class="page(?: text)?">')
    total = len(pat.findall(html)); n = [0]

    def foot(m):
        n[0] += 1
        return (m.group(0) + f'<div class="pfoot"><div><b>Módulo: Intervención Operativa</b> · {doc_title}<br>'
                f'Profesor Joaquín Rueda · IES Galileo Galilei · Córdoba</div><div class="pn">Página {n[0]} de {total}</div></div>')
    return pat.sub(foot, html)


def page(title, body):
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Barlow+Condensed:wght@600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>{body}</body></html>"""


def main():
    out = {
        "plano1_A4_escala_1-100.html": page("Plano 1 a escala 1:100", "".join(sheet_plan(
            "Plano 1 · escala 1:100", "Rectángulo de 5,00 × 7,00 m con cuatro triángulos y cuatro semicírculos (el plano 1 del patio con todas las medidas al doble). Practica en el folio con compás lo que se hace en el patio con cordel.",
            draw_plan1, (P(-2.329, -2.0), P(4.829, 6.554)), TABLE1, STEPS1, CHECKS1))),
        "plano_practicas_A4_escala_1-100.html": page("Plano de prácticas a escala 1:100", "".join(sheet_plan(
            "Plano de prácticas · escala 1:100", "Rectángulo de 8,00 × 6,00 m para practicar radios iguales y 3-4-5 en las esquinas, dos radios en un punto intermedio y la técnica del punto medio (mediatriz).",
            draw_practice, (P(-2.0, -2.0), P(5.5, 5.0)), TABLEP, STEPSP, CHECKSP))),
        "guia_replanteo_plano1.html": page("Guía del replanteo del plano 1", guide_html()),
    }
    titles = {"plano1_A4_escala_1-100.html": "Plano 1 · escala 1:100", "plano_practicas_A4_escala_1-100.html": "Plano de prácticas · escala 1:100",
              "guia_replanteo_plano1.html": "Guía del replanteo del plano 1 a tamaño real"}
    for name, html in out.items():
        html = add_footers(html, titles[name])
        open(os.path.join(HERE, name), "w", encoding="utf-8").write(html)
        print(name)


if __name__ == "__main__":
    main()
