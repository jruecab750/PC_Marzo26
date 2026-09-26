"""Escena 3D (Blender 4.x, Eevee): Robi, robot de Protección Civil, enseña el compás de cordel.

    blender -b -P escena_blender.py -- [--preview] [--start N] [--step K]

Lee warp.json (generado por «python3 intro.py voz») para ajustar la animación a la locución y
guarda los fotogramas en frames/00000.png ...
Mano izquierda: fija en el centro del arco, sujetando el cordel contra el suelo.
Mano derecha: tensa el cordel y sujeta la tiza cilíndrica anudada a su extremo.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Euler, Quaternion, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREVIEW = "--preview" in ARGS


def arg(name, default):
    return type(default)(ARGS[ARGS.index(name) + 1]) if name in ARGS else default


# ---------------------------------------------------------------- utilidades
def clamp01(x):
    return max(0.0, min(1.0, x))


def ease(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


def lerp(a, b, t):
    return a + (b - a) * t


def vlerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def d2(deg):
    a = math.radians(deg)
    return Vector((math.cos(a), math.sin(a), 0))


# ---------------------------------------------------------------- geometría de las construcciones
R1 = 0.6  # radio de la perpendicular en la esquina
A = Vector((0, 0, 0))
P1, P2, P3 = A + R1 * d2(0), A + R1 * d2(60), A + R1 * d2(120)
P4 = P2 + P3 - A
M = Vector((2.6, 0, 0))
K1, K2 = M + Vector((-0.4, 0, 0)), M + Vector((0.4, 0, 0))
R2 = 0.7
X = M + Vector((0, math.sqrt(R2 ** 2 - 0.4 ** 2), 0))
C0, R0 = Vector((-1.6, -1.75, 0)), 0.8  # arco de demostración
P_PRES = Vector((-1.6, -1.2, 0))  # donde Robi se presenta
P_FIN = Vector((2.6, -0.85, 0))


def ang(c, p):
    return math.degrees(math.atan2(p.y - c.y, p.x - c.x))


# Acciones de dibujo: (t0, t1, tipo, centro, radio o (r0, r1), ángulo(s))
ACTIONS = [
    (18.0, 25.0, "arc", C0, R0, (130, 230)),
    (34.0, 39.0, "arc", A, R1, (-10, 135)),
    (41.0, 43.5, "arc", P1, R1, (ang(P1, P2) - 15, ang(P1, P2) + 15)),
    (45.5, 48.0, "arc", P2, R1, (ang(P2, P3) - 15, ang(P2, P3) + 15)),
    (50.0, 52.5, "arc", P2, R1, (ang(P2, P4) - 15, ang(P2, P4) + 15)),
    (54.0, 56.5, "arc", P3, R1, (ang(P3, P4) - 15, ang(P3, P4) + 15)),
    (59.0, 63.0, "line", A, (0.12, 1.3), 90),
    (76.0, 79.0, "arc", K1, R2, (ang(K1, X) - 15, ang(K1, X) + 15)),
    (81.0, 84.0, "arc", K2, R2, (ang(K2, X) - 15, ang(K2, X) + 15)),
    (87.0, 90.5, "line", M, (0.1, 1.0), 90),
]


def action_state(a, t):
    """Centro, ángulo (grados) y radio del compás en el instante t de la acción a."""
    t0, t1, kind, c, r, th = a
    p = ease((t - t0) / (t1 - t0))
    if kind == "arc":
        return c, lerp(th[0], th[1], p), r
    return c, th, lerp(r[0], r[1], p)


# ---------------------------------------------------------------- poses de Robi
BODY_BACK = 0.36  # distancia del cuerpo por detrás de la línea entre las manos


def pose_compas(c, th, r, lift=0.0):
    u = d2(th)
    f = Vector((-math.sin(math.radians(th)), math.cos(math.radians(th)), 0))
    tip = c + r * u
    m = c + 0.5 * r * u
    return dict(body=m - BODY_BACK * f, yaw=math.radians(th),
                lh=Vector((c.x, c.y, 0.045 + lift)), rh=Vector((tip.x, tip.y, 0.055 + lift)),
                anchor=Vector((c.x, c.y, 0.012 + lift)), cord=True)


def pose_pres(body, t, kind):
    yaw = math.pi  # mirando a -Y (hacia la cámara)
    u, f = Vector((-1, 0, 0)), Vector((0, -1, 0))  # derecha y frente de Robi
    if kind == "saludo":
        rh = body + u * 0.3 + f * 0.08 + Vector((0, 0, 0.78)) + u * 0.07 * math.sin(t * 7)
        lh = body - u * 0.2 + f * 0.22 + Vector((0, 0, 0.35))
    elif kind == "tiza":
        rh = body + u * 0.07 + f * 0.36 + Vector((0, 0, 0.6))
        lh = body - u * 0.12 + f * 0.33 + Vector((0, 0, 0.48))
    elif kind == "reposo":
        rh = body + u * 0.24 + f * 0.1 + Vector((0, 0, 0.3))
        lh = body - u * 0.24 + f * 0.1 + Vector((0, 0, 0.3))
    else:  # pulgar arriba
        rh = body + u * 0.27 + f * 0.18 + Vector((0, 0, 0.72))
        lh = body - u * 0.2 + f * 0.22 + Vector((0, 0, 0.35))
    return dict(body=body, yaw=yaw, lh=lh, rh=rh, anchor=lh + Vector((0, 0, -0.03)), cord=kind == "tiza")


# Tramos de pose: (t0, t1, función t -> pose)
KEYS = [(0.0, 6.3, lambda t: pose_pres(P_PRES, t, "saludo")),
        (7.2, 15.6, lambda t: pose_pres(P_PRES, t, "tiza"))]
for a in ACTIONS:
    KEYS.append((a[0], a[1], (lambda a: lambda t: pose_compas(*action_state(a, t)))(a)))
KEYS.append((64.6, 67.8, lambda t: pose_pres(Vector((1.45, 0.8, 0)), t, "reposo")))
KEYS.append((91.8, 94.6, lambda t: pose_pres(Vector((3.75, 0.55, 0)), t, "reposo")))
KEYS.append((95.6, 101.0, lambda t: pose_pres(P_FIN, t, "pulgar")))
KEYS.sort(key=lambda k: k[0])


def blend(p, q, s, bump):
    yaw_d = (q["yaw"] - p["yaw"] + math.pi) % (2 * math.pi) - math.pi
    up = Vector((0, 0, bump))
    return dict(body=vlerp(p["body"], q["body"], s), yaw=p["yaw"] + yaw_d * s,
                lh=vlerp(p["lh"], q["lh"], s) + up, rh=vlerp(p["rh"], q["rh"], s) + up,
                anchor=vlerp(p["anchor"], q["anchor"], s) + up, cord=p["cord"] or q["cord"])


def pose_at(t):
    for i, (t0, t1, fn) in enumerate(KEYS):
        if t0 <= t <= t1:
            return fn(t)
        if t < t0:  # hueco entre tramos: espera y transición al final
            prev = KEYS[i - 1] if i else KEYS[0]
            pe, ne = prev[2](prev[1]), fn(t0)
            win = min(1.6, t0 - prev[1])
            s = ease((t - (t0 - win)) / win) if win > 0 else 1
            return blend(pe, ne, s, 0.1 * math.sin(math.pi * s))
    return KEYS[-1][2](KEYS[-1][1])


# ---------------------------------------------------------------- cámara: (t0, t1, posición, objetivo)
CAMS = [(0, 6.5, (-1.6, -2.95, 0.85), (-1.6, -1.2, 0.45)),
        (7.6, 16, (-1.52, -2.15, 0.72), (-1.6, -1.45, 0.52)),
        (17.2, 30.5, (-1.95, -4.0, 1.75), (-1.9, -1.55, 0.3)),
        (32.2, 67.5, (0.3, -1.35, 2.6), (0.25, 0.45, 0.0)),
        (69.2, 94.5, (2.65, -1.35, 2.6), (2.6, 0.35, 0.0)),
        (96.2, 101, (2.6, -2.55, 0.85), (2.6, -0.85, 0.45))]


def cam_at(t):
    for i, (t0, t1, p, g) in enumerate(CAMS):
        if t0 <= t <= t1:
            return Vector(p), Vector(g)
        if t < t0:
            _, pt1, pp, pg = CAMS[i - 1]
            s = ease((t - pt1) / (t0 - pt1))
            return vlerp(pp, p, s), vlerp(pg, g, s)
    return Vector(CAMS[-1][2]), Vector(CAMS[-1][3])


# ---------------------------------------------------------------- escena
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def mat(name, color, rough=0.5, metal=0.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


M_METAL = mat("metal", (0.55, 0.58, 0.62), 0.35, 0.8)
M_DARK = mat("oscuro", (0.05, 0.05, 0.06), 0.6)
M_WHITE = mat("blanco", (0.9, 0.9, 0.88), 0.4)
M_VEST = mat("chaleco", (1.0, 0.33, 0.02), 0.55)
M_REFL = mat("reflectante", (0.85, 0.87, 0.9), 0.15, 1.0)
M_EYE = mat("ojo", (0.2, 0.9, 1.0), 0.2, 0, 6)
M_CHALK = mat("tiza", (0.97, 0.97, 0.94), 0.9, 0, 0.15)
M_CORD = mat("cordel", (0.85, 0.12, 0.08), 0.8)
M_LINE = mat("linea", (0.95, 0.95, 0.92), 0.9, 0, 0.35)
M_TXT = mat("texto", (1.0, 1.0, 1.0), 0.5, 0, 2.5)
M_TXT_Y = mat("texto_amarillo", (1.0, 0.82, 0.1), 0.5, 0, 2.5)
M_OK = mat("ok", (0.3, 0.9, 0.5), 0.5, 0, 2.5)
M_HAND = mat("mano", (0.22, 0.24, 0.28), 0.45, 0.6)


def asphalt_material():
    m = bpy.data.materials.new("asfalto")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 60
    n1.inputs["Detail"].default_value = 8
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.035, 0.035, 0.038, 1)
    ramp.color_ramp.elements[1].color = (0.16, 0.16, 0.165, 1)
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 400
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = 0.92
    return m


def add(obj, material, parent=None):
    if material:
        obj.data.materials.append(material)
    if parent:
        obj.parent = parent
    for p in obj.data.polygons if hasattr(obj.data, "polygons") else []:
        p.use_smooth = True
    return obj


def box(size, loc, material, parent=None, bevel=0.02, name="caja"):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        mod = o.modifiers.new("bisel", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    return add(o, material, parent)


def cyl(r, h, loc, material, parent=None, rot=(0, 0, 0), name="cil", verts=24):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, rotation=rot, vertices=verts)
    o = bpy.context.object
    o.name = name
    return add(o, material, parent)


def sph(r, loc, material, parent=None, name="esf", scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=24, ring_count=12)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    return add(o, material, parent)


def empty(name):
    o = bpy.data.objects.new(name, None)
    scene.collection.objects.link(o)
    return o


FONT = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

# Suelo
bpy.ops.mesh.primitive_plane_add(size=30, location=(0.5, 0, 0))
add(bpy.context.object, asphalt_material())

# Luz y mundo
bpy.ops.object.light_add(type="SUN", location=(3, -4, 6))
sun = bpy.context.object
sun.data.energy = 3.2
sun.data.angle = math.radians(6)
sun.rotation_euler = Euler((math.radians(50), math.radians(12), math.radians(35)))
world = bpy.data.worlds.new("mundo")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9

# ---------------------------------------------------------------- Robi (robot con orugas y chaleco EPC)
robot = empty("robot")
for sx in (-1, 1):
    box((0.1, 0.44, 0.14), (sx * 0.15, 0, 0.07), M_DARK, robot, 0.04, "oruga")
    for yy in (-0.15, 0, 0.15):
        cyl(0.045, 0.105, (sx * 0.15, yy, 0.07), M_METAL, robot, (0, math.radians(90), 0), "rueda")
box((0.32, 0.32, 0.05), (0, 0, 0.165), M_METAL, robot, 0.01, "base")
box((0.3, 0.2, 0.3), (0, 0, 0.34), M_METAL, robot, 0.05, "torso")
box((0.33, 0.23, 0.22), (0, 0, 0.34), M_VEST, robot, 0.04, "chaleco")
for zz in (0.3, 0.38):
    box((0.335, 0.235, 0.022), (0, 0, zz), M_REFL, robot, 0.005, "banda")
bpy.ops.object.text_add(location=(0, 0.118, 0.3))
t = bpy.context.object
t.data.body = "EPC"
t.data.size = 0.055
t.data.align_x = "CENTER"
t.parent = robot
t.data.materials.append(M_REFL)
t.data.font = FONT
t.location = (0, 0.119, 0.325)  # el frente de Robi es +Y local
t.rotation_euler = (math.radians(90), 0, math.radians(180))
cyl(0.035, 0.06, (0, 0, 0.51), M_METAL, robot, name="cuello")
box((0.2, 0.17, 0.15), (0, 0, 0.6), M_WHITE, robot, 0.05, "cabeza")
box((0.16, 0.02, 0.07), (0, 0.086, 0.61), M_DARK, robot, 0.015, "visor")
for sx in (-1, 1):
    sph(0.016, (sx * 0.04, 0.097, 0.615), M_EYE, robot, "ojo")
cyl(0.006, 0.08, (0.05, 0, 0.71), M_METAL, robot, name="antena")
sph(0.018, (0.05, 0, 0.755), M_VEST, robot, "antena_bola")
for sx in (-1, 1):
    sph(0.045, (sx * 0.19, 0, 0.45), M_METAL, robot, "hombro")

# Brazos (se colocan en cada fotograma)
L1, L2 = 0.34, 0.36
ARMS = {}
for side in ("izq", "der"):
    up = cyl(0.028, 1, (0, 0, 0), M_METAL, None, name=f"brazo_{side}")
    fo = cyl(0.024, 1, (0, 0, 0), M_METAL, None, name=f"antebrazo_{side}")
    el = sph(0.034, (0, 0, 0), M_DARK, None, f"codo_{side}")
    ARMS[side] = (up, fo, el)


def make_hand(side):
    """Mano articulada de 3 dedos + pulgar. Origen = centro de la palma. Local +Y = dedos, -Z = palma."""
    h = empty(f"mano_{side}")
    box((0.075, 0.07, 0.032), (0, 0, 0), M_HAND, h, 0.012, "palma")
    if side == "izq":  # mano abierta que aprieta el cordel contra el suelo
        for i, x in enumerate((-0.025, 0, 0.025)):
            f1 = cyl(0.009, 0.045, (x, 0.055, -0.006), M_HAND, h, (math.radians(100), 0, 0), "dedo")
            f2 = cyl(0.008, 0.035, (x, 0.083, -0.025), M_HAND, h, (math.radians(130), 0, 0), "dedo")
            sph(0.009, (x, 0.093, -0.038), M_HAND, h, "yema")
        cyl(0.01, 0.045, (-0.05, 0.02, -0.01), M_HAND, h, (math.radians(90), 0, math.radians(40)), "pulgar")
    else:  # puño que rodea la tiza vertical
        for i, z in enumerate((-0.018, 0, 0.018)):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.024, minor_radius=0.009, location=(0, 0.045, z))
            o = bpy.context.object
            o.name = "dedo_curvado"
            add(o, M_HAND, h)
        cyl(0.01, 0.045, (0.03, 0.035, 0.03), M_HAND, h, (math.radians(-60), 0, 0), "pulgar")
    return h


HAND_L, HAND_R = make_hand("izq"), make_hand("der")

# Tiza cilíndrica, nudo y cordel
CHALK = cyl(0.012, 0.1, (0, 0, 0), M_CHALK, None, name="tiza")
bpy.ops.mesh.primitive_torus_add(major_radius=0.016, minor_radius=0.004)
KNOT = add(bpy.context.object, M_CORD)
CORD = cyl(0.0035, 1, (0, 0, 0), M_CORD, None, name="cordel", verts=10)
bpy.ops.mesh.primitive_torus_add(major_radius=0.014, minor_radius=0.0035)
LOOP = add(bpy.context.object, M_CORD)  # lazada del extremo que sujeta la mano izquierda

# ---------------------------------------------------------------- trazos de tiza en el suelo
TRAILS = []  # (curva, t0, t1)


def trail(points, t0, t1, width=0.0065):
    cu = bpy.data.curves.new("trazo", "CURVE")
    cu.dimensions = "3D"
    sp = cu.splines.new("POLY")
    sp.points.add(len(points) - 1)
    for p, q in zip(sp.points, points):
        p.co = (q.x, q.y, 0.004, 1)
    cu.bevel_depth = width
    cu.bevel_resolution = 2
    cu.bevel_factor_mapping_end = "SPLINE"
    o = bpy.data.objects.new("trazo", cu)
    scene.collection.objects.link(o)
    o.data.materials.append(M_LINE)
    o.scale = (1, 1, 0.25)
    TRAILS.append((o, t0, t1))
    return o


for a in ACTIONS:
    t0, t1, kind, c, r, th = a
    n = 80
    pts = []
    for i in range(n + 1):
        if kind == "arc":
            pts.append(c + r * d2(lerp(th[0], th[1], i / n)))
        else:
            pts.append(c + lerp(r[0], r[1], i / n) * d2(th))
    trail(pts, t0, t1)
# líneas base (ya trazadas antes de empezar cada ejemplo)
trail([Vector((-0.3, 0, 0)), Vector((1.3, 0, 0))], 31.0, 32.0)
trail([Vector((1.75, 0, 0)), Vector((3.45, 0, 0))], 68.0, 69.0)

# ---------------------------------------------------------------- marcas y rótulos
APPEAR = []  # (objeto, t)


def cross(p, t, s=0.09):
    g = empty("cruz")
    g.location = (p.x, p.y, 0.005)
    for a_ in (45, -45):
        o = box((s, 0.012, 0.003), (0, 0, 0), M_LINE, g, 0)
        o.rotation_euler = (0, 0, math.radians(a_))
    APPEAR.append((g, t))


def label(text, p, t, material=M_TXT, size=0.1, off=(0.07, -0.07)):
    bpy.ops.object.text_add(location=(p.x + off[0], p.y + off[1], 0.12))
    o = bpy.context.object
    o.data.body = text
    o.data.size = size
    o.data.align_x = "CENTER"
    o.data.align_y = "CENTER"
    o.data.font = FONT
    o.data.extrude = 0.004
    o.data.materials.append(material)
    APPEAR.append((o, t))
    return o


cross(C0, 16.8)
label("centro", C0, 16.8, M_TXT_Y, 0.07, (0.05, -0.14))
cross(A, 31.5)
label("A", A, 31.5, M_TXT, 0.12, (-0.13, -0.15))
for p, nm, tt, off in [(P1, "1", 39.3, (0.1, -0.16)), (P2, "2", 43.8, (0.14, 0.06)), (P3, "3", 48.3, (-0.14, 0.06)),
                       (P4, "4", 56.8, (0.14, 0.06))]:
    cross(p, tt, 0.07)
    label(nm, p, tt, M_TXT_Y, 0.09, off)
label("90°", A, 64.0, M_OK, 0.1, (0.2, 0.18))
cross(M, 69.5)
label("M", M, 69.5, M_TXT, 0.12, (0.0, -0.2))
for p, nm, tt in [(K1, "1", 71.0), (K2, "2", 72.0)]:
    cross(p, tt, 0.07)
    label(nm, p, tt, M_TXT_Y, 0.09, (0.0, -0.2))
cross(X, 84.3, 0.07)
label("3", X, 84.3, M_TXT_Y, 0.09, (0.15, 0.06))

# ---------------------------------------------------------------- cámara y render
bpy.ops.object.camera_add()
CAM = bpy.context.object
CAM.data.lens = 32
scene.camera = CAM
TXT_OBJS = [o for o, _ in APPEAR if o.type == "FONT"]

scene.render.engine = "BLENDER_EEVEE"
ee = scene.eevee
ee.taa_render_samples = arg("--samples", 16)
ee.use_gtao = True
ee.use_soft_shadows = True
ee.shadow_cascade_size = "2048"
scene.render.resolution_x = arg("--width", 1920)
scene.render.resolution_y = arg("--height", 1080)
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Filmic" if "Filmic" in [
    v.identifier for v in type(scene.view_settings).bl_rna.properties["view_transform"].enum_items] else "AgX"


def look(obj_from, target):
    d = Vector(target) - Vector(obj_from)
    return d.to_track_quat("-Z", "Y")


def place_segment(obj, a, b):
    """Cilindro de altura 1 entre los puntos a y b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    obj.location = (a + b) / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("Z", "Y")
    obj.scale = (1, 1, max(d.length, 1e-4))


def ik(shoulder, target, pole):
    s, t = Vector(shoulder), Vector(target)
    d = t - s
    dist = min(d.length, L1 + L2 - 1e-3)
    d.normalize()
    a = (L1 ** 2 - L2 ** 2 + dist ** 2) / (2 * dist)
    h = math.sqrt(max(L1 ** 2 - a ** 2, 0))
    pv = Vector(pole) - s
    pv = (pv - pv.dot(d) * d)
    pv = pv.normalized() if pv.length > 1e-6 else Vector((0, 0, -1))
    elbow = s + d * a + pv * h
    wrist = s + d * dist
    return elbow, wrist


def apply_state(t):
    st = pose_at(t)
    body, yaw = st["body"], st["yaw"]
    robot.location = (body.x, body.y, 0)
    robot.rotation_euler = (0, 0, yaw - math.pi / 2 + math.pi / 2)  # local +Y = frente
    rot = Euler((0, 0, yaw)).to_matrix()
    right = rot @ Vector((1, 0, 0))
    fwd = rot @ Vector((0, 1, 0))
    hands = {"izq": (st["lh"], -1), "der": (st["rh"], 1)}
    for side, (hand_pos, sx) in hands.items():
        sh = Vector((body.x, body.y, 0)) + rot @ Vector((sx * 0.19, 0, 0.45))
        back = (hand_pos - sh).normalized()
        wrist_target = hand_pos - back * 0.045
        elbow, wrist = ik(sh, wrist_target, sh + right * sx * 0.3 + Vector((0, 0, -0.25)) - fwd * 0.1)
        up, fo, el = ARMS[side]
        place_segment(up, sh, elbow)
        place_segment(fo, elbow, wrist)
        el.location = elbow
        hobj = HAND_L if side == "izq" else HAND_R
        hobj.location = hand_pos
        fdir = (hand_pos - elbow)
        if side == "izq":  # palma hacia abajo, dedos hacia delante-abajo
            fdir.z = min(fdir.z, -0.25 * Vector((fdir.x, fdir.y)).length)
            q = fdir.to_track_quat("Y", "Z")
        else:  # puño con la tiza vertical: solo gira alrededor de Z
            fdir.z = 0
            q = fdir.to_track_quat("Y", "Z") if fdir.length > 1e-6 else Quaternion()
        hobj.rotation_mode = "QUATERNION"
        hobj.rotation_quaternion = q
    # tiza en el puño derecho, nudo en su extremo superior y cordel tenso hasta la lazada
    rh = st["rh"]
    CHALK.location = rh
    top = rh + Vector((0, 0, 0.042))
    KNOT.location = top
    anchor = st["anchor"]
    LOOP.location = anchor
    CORD.hide_render = not st["cord"]
    KNOT.hide_render = LOOP.hide_render = not st["cord"]
    place_segment(CORD, anchor, top)
    # cámara
    pos, tgt = cam_at(t)
    CAM.location = pos
    CAM.rotation_mode = "QUATERNION"
    CAM.rotation_quaternion = look(pos, tgt)
    # trazos y marcas
    for o, t0, t1 in TRAILS:
        o.data.bevel_factor_end = ease((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)
        o.hide_render = t < t0
    for o, ta in APPEAR:
        k = clamp01((t - ta) / 0.3)
        o.hide_render = k <= 0
        s = 0.001 + k
        o.scale = (s, s, s)
    for o in TXT_OBJS:  # rótulos siempre de cara a la cámara
        o.rotation_mode = "QUATERNION"
        d = (pos - o.location)
        o.rotation_quaternion = d.to_track_quat("Z", "Y")


def main():
    warp = json.load(open(os.path.join(HERE, "warp.json")))
    frames = warp["frames"]
    out = os.path.join(HERE, "preview" if PREVIEW else "frames")
    os.makedirs(out, exist_ok=True)
    if PREVIEW:
        times = [float(x) for x in arg("--times", "3,11,20,27,36,42,53,57.5,62,66,70,78,85,89,93,98").split(",")]
        todo = [(int(s * 25), s) for s in times]
    else:
        start, step = arg("--start", 0), arg("--step", 1)
        todo = [(i, frames[i]) for i in range(start, len(frames), step)]
    for i, t in todo:
        path = os.path.join(out, f"{i:05d}.png" if not PREVIEW else f"t_{t:05.1f}.png")
        if not PREVIEW and os.path.exists(path):
            continue
        apply_state(t)
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        print("FRAME", i, f"{t:.2f}", flush=True)


main()
