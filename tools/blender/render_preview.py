"""把 character.glb 渲染成预览图（正面 / 侧面 / 四分之三）"""
import bpy
import sys
import os
import math
from mathutils import Vector

argv = sys.argv
glb = None
outdir = None
if "--" in argv:
    args = argv[argv.index("--") + 1:]
    if "--glb" in args:
        glb = args[args.index("--glb") + 1]
    if "--outdir" in args:
        outdir = args[args.index("--outdir") + 1]
if not glb:
    glb = os.path.join(os.path.dirname(__file__), "..", "..",
                       "plugins", "dafeiyu_room", "pages", "room", "model", "character.glb")
if not outdir:
    outdir = os.path.join(os.path.dirname(__file__), "_preview")
os.makedirs(outdir, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)

# 相机与灯
bpy.ops.object.camera_add(location=(0, -2.6, 1.1))
cam = bpy.context.active_object
cam.data.lens = 52
bpy.context.scene.camera = cam

bpy.ops.object.light_add(type="AREA", location=(1.6, -2.0, 2.4))
key = bpy.context.active_object
key.data.energy = 70
key.data.size = 2.2

bpy.ops.object.light_add(type="AREA", location=(-1.8, -1.2, 1.6))
fill = bpy.context.active_object
fill.data.energy = 25
fill.data.size = 2.0

bpy.ops.object.light_add(type="AREA", location=(0, 1.8, 2.0))
rim = bpy.context.active_object
rim.data.energy = 40
rim.data.size = 1.6

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 720
scene.render.resolution_y = 1000
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0.0
if scene.world is None:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
nt = scene.world.node_tree
bg = nt.nodes.get("Background") or nt.nodes.new("ShaderNodeBackground")
out = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
try:
    nt.links.new(bg.outputs[0], out.inputs[0])
except Exception:
    pass
bg.inputs[0].default_value = (0.72, 0.78, 0.84, 1)
bg.inputs[1].default_value = 0.45


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


shots = {
    "front": ((0.0, -3.0, 0.95), (0, 0, 0.80)),
    "side": ((2.6, -1.9, 1.0), (0, 0, 0.80)),
    "back": ((0.0, 3.0, 1.05), (0, 0, 0.85)),
}
for name, (pos, target) in shots.items():
    cam.location = pos
    aim(cam, target)
    scene.render.filepath = os.path.join(outdir, f"{name}.png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", scene.render.filepath)
