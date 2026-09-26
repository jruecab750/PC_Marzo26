"""Importa el robot de Claude Design (GLB) y lo renderiza: original y versión PCia naranja."""
import bpy, math, os, sys
from mathutils import Vector, Euler
HERE = os.path.dirname(os.path.abspath(__file__))
mode = sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, "design", "repla-robot-replanteo.glb"))
names = sorted(o.name for o in s.objects)
print("OBJETOS", len(names), names[:80])
if mode == "pcia":
    for m in bpy.data.materials:
        if m.name.startswith("carcasa_blanca") and m.use_nodes:
            b = m.node_tree.nodes.get("Principled BSDF")
            b.inputs["Base Color"].default_value = (1.0, 0.16, 0.0, 1)
        if m.name.startswith("placa_nombre") and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type == "TEX_IMAGE":
                    n.image = bpy.data.images.load(os.path.join(HERE, "design", "placa_pcia.png"))
bpy.ops.object.light_add(type="SUN", location=(3, 4, 6)); sun = bpy.context.object
sun.data.energy = 3; sun.data.angle = math.radians(8); sun.rotation_euler = Euler((math.radians(45), 0, math.radians(150)))
bpy.ops.object.light_add(type="AREA", location=(1.5, -2.0, 1.5)); a = bpy.context.object; a.data.energy = 80; a.data.size = 2
a.rotation_euler = (Vector((0.5, 0.3, 0.4)) - a.location).to_track_quat("-Z", "Y").to_euler()
w = bpy.data.worlds.new("w"); s.world = w; w.use_nodes = True
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
bpy.ops.object.camera_add(location=(1.05, -2.2, 0.95)); cam = bpy.context.object; s.camera = cam; cam.data.lens = 35
# glTF: Y arriba -> Blender Z arriba; el robot está en (0.55, -0.35, 0.09) aprox.
cam.rotation_euler = (Vector((0.55, -0.35, 0.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()
s.render.engine = "BLENDER_EEVEE_NEXT"; s.eevee.taa_render_samples = 16
s.render.resolution_x, s.render.resolution_y = 1280, 720
s.render.filepath = os.path.join(HERE, "design", f"glb_{mode}.png")
bpy.ops.render.render(write_still=True)
print("HECHO")
