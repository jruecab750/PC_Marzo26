"""Clips de prueba (≈5 s) del nuevo diseño de PCia: robot tipo EVA, naranja de Protección Civil,
que levita, con manos de pulgar y dos dedos.

    python3 propuestas_pcia.py -- --head naranja --out prop_A      # Blender 4.2 (módulo bpy, Eevee Next)
    blender -b -P propuestas_pcia.py -- --head naranja --out prop_C # Blender 4.0 (Eevee)
"""
import math
import os
import sys
import time

import bpy
import bmesh
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default):
    return type(default)(ARGS[ARGS.index(name) + 1]) if name in ARGS else default


HEAD = arg("--head", "naranja")
OUT = os.path.join(HERE, arg("--out", "prop"))
DUR, STEP, FPS = arg("--dur", 5.0), arg("--step", 2), 25

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
FONT = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")


def mat(name, color, rough=0.5, metal=0.0, emit=0.0, coat=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.08
    if emit:
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


M_ORANGE = mat("naranja_pc", (1.0, 0.16, 0.0), 0.28, 0, 0, 0.8)
M_WHITE = mat("blanco", (0.92, 0.92, 0.9), 0.25, 0, 0, 0.8)
M_VISOR = mat("visor", (0.01, 0.01, 0.012), 0.08, 0, 0, 1.0)
M_EYE = mat("ojo", (0.25, 0.85, 1.0), 0.2, 0, 8)
M_REFL = mat("reflectante", (0.85, 0.87, 0.9), 0.15, 1.0)
M_HAND = mat("mano", (0.78, 0.8, 0.83), 0.3, 0.3)
M_TXT = mat("texto", (1, 1, 1), 0.4, 0, 1.5)
M_LINE = mat("linea", (0.95, 0.95, 0.92), 0.9, 0, 0.3)
M_CHALK = mat("tiza", (0.97, 0.97, 0.94), 0.9, 0, 0.15)
M_GLOW = mat("brillo", (0.3, 0.8, 1.0), 0.5, 0, 1.2)


def asphalt():
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


def smooth(o, level=2):
    for p in o.data.polygons:
        p.use_smooth = True
    mod = o.modifiers.new("suave", "SUBSURF")
    mod.levels = mod.render_levels = level
    return o


def ellipsoid(size, loc, material, parent=None, taper=0.0, name="elipsoide", seg=32):
    """Elipsoide; taper > 0 estrecha la mitad inferior (forma de huevo, como EVA)."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0), segments=seg, ring_count=seg // 2)
    o = bpy.context.object
    o.name = name
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for v in bm.verts:
        k = 1.0 - taper * max(0.0, -v.co.z) ** 1.5
        v.co.x *= size[0] * k
        v.co.y *= size[1] * k
        v.co.z *= size[2]
    bm.to_mesh(o.data)
    bm.free()
    o.location = loc
    o.data.materials.append(material)
    if parent:
        o.parent = parent
    for p in o.data.polygons:
        p.use_smooth = True
    return o


def capsule(r, loc, material, name="capsula"):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=loc, segments=24, ring_count=12)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(material)
    for p in o.data.polygons:
        p.use_smooth = True
    o["r"] = r
    return o


def empty(name, parent=None):
    o = bpy.data.objects.new(name, None)
    scene.collection.objects.link(o)
    if parent:
        o.parent = parent
    return o


# ---------------------------------------------------------------- escenario
bpy.ops.mesh.primitive_plane_add(size=30)
bpy.context.object.data.materials.append(asphalt())
# un arco y una línea de tiza de fondo
cu = bpy.data.curves.new("arco", "CURVE")
cu.dimensions = "3D"
sp = cu.splines.new("POLY")
pts = [(0.55 * math.cos(math.radians(a)) - 0.2, 0.55 * math.sin(math.radians(a)) + 0.25, 0.004) for a in range(200, 341, 4)]
sp.points.add(len(pts) - 1)
for p, q in zip(sp.points, pts):
    p.co = (*q, 1)
cu.bevel_depth = 0.0065
o = bpy.data.objects.new("arco", cu)
scene.collection.objects.link(o)
o.data.materials.append(M_LINE)
o.scale = (1, 1, 0.25)

bpy.ops.object.light_add(type="SUN", location=(3, -4, 6))
sun = bpy.context.object
sun.data.energy = 3.0
sun.data.angle = math.radians(8)
sun.rotation_euler = Euler((math.radians(48), math.radians(10), math.radians(30)))
bpy.ops.object.light_add(type="AREA", location=(-1.2, -1.4, 1.4))
fill = bpy.context.object
fill.data.energy = 60
fill.data.size = 1.5
fill.rotation_euler = Euler((math.radians(55), 0, math.radians(-40)))
world = bpy.data.worlds.new("mundo")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.9

# ---------------------------------------------------------------- PCia
robot = empty("PCia")
BODY_Z = 0.1  # altura de levitación del punto más bajo
body = smooth(ellipsoid((0.15, 0.13, 0.22), (0, 0, 0.22), M_ORANGE, robot, taper=0.55, name="cuerpo"), 1)
band = ellipsoid((0.152, 0.132, 0.02), (0, 0, 0.27), M_REFL, robot, name="banda")
bpy.ops.object.text_add(location=(0, 0.128, 0.33))
t = bpy.context.object
t.data.body = "EPC"
t.data.font = FONT
t.data.size = 0.05
t.data.align_x = t.data.align_y = "CENTER"
t.data.extrude = 0.002
t.rotation_euler = (math.radians(90), 0, math.radians(180))
t.parent = robot
t.data.materials.append(M_TXT)
head_mat = M_ORANGE if HEAD == "naranja" else M_WHITE
head = smooth(ellipsoid((0.13, 0.115, 0.09), (0, 0, 0.535), head_mat, robot, name="cabeza"), 1)
visor = ellipsoid((0.105, 0.05, 0.058), (0, 0.072, 0.53), M_VISOR, robot, name="visor")
for sx in (-1, 1):
    eye = ellipsoid((0.022, 0.006, 0.014), (sx * 0.042, 0.119, 0.535), M_EYE, robot, name="ojo")
    eye.rotation_euler = (0, sx * math.radians(12), 0)
# brillo de levitación bajo el cuerpo
bpy.ops.mesh.primitive_circle_add(radius=0.045, fill_type="NGON", location=(0, 0, 0.002))
glow = bpy.context.object
glow.data.materials.append(M_GLOW)

L1, L2 = 0.2, 0.19
ARMS = {s: (capsule(0.032, (0, 0, 0), M_ORANGE, f"brazo_{s}"), capsule(0.028, (0, 0, 0), M_ORANGE, f"antebrazo_{s}"))
        for s in ("izq", "der")}


def make_hand(side):
    """Mano de pulgar + dos dedos. Origen en la palma; local +Y = dedos."""
    h = empty(f"mano_{side}")
    ellipsoid((0.03, 0.035, 0.016), (0, 0, 0), M_HAND, h, name="palma", seg=24)
    for x in (-0.012, 0.014):
        f = ellipsoid((0.009, 0.026, 0.009), (x, 0.052, -0.004), M_HAND, h, name="dedo", seg=16)
        f.rotation_euler = (math.radians(-15), 0, 0)
    th = ellipsoid((0.009, 0.022, 0.009), (-0.033 if side == "der" else 0.033, 0.02, 0.0), M_HAND, h, name="pulgar", seg=16)
    th.rotation_euler = (0, 0, math.radians(35 if side == "der" else -35))
    return h


HANDS = {"izq": make_hand("izq"), "der": make_hand("der")}
CHALK = None
bpy.ops.mesh.primitive_cylinder_add(radius=0.011, depth=0.09)
CHALK = bpy.context.object
CHALK.data.materials.append(M_CHALK)


def place_capsule(o, a, b):
    a, b = Vector(a), Vector(b)
    d = b - a
    o.location = (a + b) / 2
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    r = o["r"]
    o.scale = (r, r, max(d.length / 2 + r * 0.6, r))


def ik(s, t, pole):
    s, t = Vector(s), Vector(t)
    d = t - s
    dist = min(d.length, L1 + L2 - 1e-3)
    d.normalize()
    a = (L1 ** 2 - L2 ** 2 + dist ** 2) / (2 * dist)
    h = math.sqrt(max(L1 ** 2 - a ** 2, 0))
    pv = Vector(pole) - s
    pv = pv - pv.dot(d) * d
    pv = pv.normalized() if pv.length > 1e-6 else Vector((0, 0, -1))
    return s + d * a + pv * h, s + d * dist


# ---------------------------------------------------------------- cámara y render
bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.lens = 40
scene.camera = cam
cam.location = (0.15, -1.85, 0.58)
cam.rotation_mode = "QUATERNION"
cam.rotation_quaternion = (Vector((0, 0, 0.4)) - cam.location).to_track_quat("-Z", "Y")

engines = [e.identifier for e in type(scene.render).bl_rna.properties["engine"].enum_items]
scene.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
ee = scene.eevee
ee.taa_render_samples = arg("--samples", 16)
RT = "--sin-rt" not in ARGS
for attr, val in (("use_gtao", True), ("use_soft_shadows", True), ("use_raytracing", RT), ("use_shadows", True)):
    if hasattr(ee, attr):
        setattr(ee, attr, val)
scene.render.resolution_x, scene.render.resolution_y = 1280, 720
vt = [v.identifier for v in type(scene.view_settings).bl_rna.properties["view_transform"].enum_items]
scene.view_settings.view_transform = "AgX" if "AgX" in vt else "Filmic"


def apply(t):
    z = BODY_Z + 0.015 * math.sin(2 * math.pi * t / 2.2)
    yaw = math.radians(8 * math.sin(2 * math.pi * t / 5))
    robot.location = (0, 0, z)
    glow.scale = (1 + 2 * (z - BODY_Z),) * 3
    robot.rotation_euler = (0, 0, math.pi + yaw)  # mirando a la cámara (-Y)
    rot = robot.rotation_euler.to_matrix()
    right, fwd, up = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0)), Vector((0, 0, 1))
    base = Vector((0, 0, z))
    wave = math.sin(2 * math.pi * t / 0.9) * 0.06 * min(1, t / 0.6) * (1 if t < 3.2 else max(0, (4 - t) / 0.8))
    targets = {"der": base + right * 0.24 + fwd * 0.08 + up * (0.55 if t < 4 else 0.3 + 0.25 * max(0, (4.6 - t) / 0.6)) + right * wave,
               "izq": base - right * 0.2 + fwd * 0.12 + up * 0.22}
    for side, sx in (("izq", -1), ("der", 1)):
        sh = base + rot @ Vector((sx * 0.13, 0, 0.36))
        tgt = targets[side]
        el, wr = ik(sh, tgt - (tgt - sh).normalized() * 0.035, sh + right * sx * 0.3 + up * -0.2 - fwd * 0.1)
        ua, fa = ARMS[side]
        place_capsule(ua, sh, el)
        place_capsule(fa, el, wr)
        h = HANDS[side]
        h.location = tgt
        d = tgt - el
        h.rotation_mode = "QUATERNION"
        h.rotation_quaternion = d.to_track_quat("Y", "Z")
    rh = targets["izq"]
    CHALK.location = rh + Vector((0, 0, 0.0))


os.makedirs(OUT, exist_ok=True)
n = int(DUR * FPS)
t_start = time.time()
count = 0
for i in range(0, n, STEP):
    apply(i / FPS)
    scene.render.filepath = os.path.join(OUT, f"{i:05d}.png")
    bpy.ops.render.render(write_still=True)
    count += 1
per = (time.time() - t_start) / max(count, 1)
open(os.path.join(OUT, "tiempo.txt"), "w").write(f"{scene.render.engine} {bpy.app.version_string} {per:.2f} s/fotograma\n")
print("HECHO", OUT, f"{per:.2f} s/fotograma")
