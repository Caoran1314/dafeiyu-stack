import bpy, sys, os, addon_utils, mathutils
vrm = r"D:/软件/02-项目/dafeiyu-bot/release/dafeiyu-stack/plugins/dafeiyu_room/pages/room/model/character.vrm"
out = r"D:/软件/_tmp/face_test"
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=vrm)

# 统计名字
import re
names = [o.name for o in bpy.data.objects if o.type=="MESH"]
print("FACE 相关:", [n for n in names if re.search(r"face|eye|mouth|brow|atlas|emote", n, re.I)][:12])

# 隐藏脸部叠加层与说明牌
hidden = []
for o in bpy.data.objects:
    if o.type != "MESH": continue
    if re.search(r"facebaked|ve_emote|emoteatlas", o.name, re.I):
        o.hide_render = True; hidden.append(o.name)
print("隐藏:", hidden[:10])

# 相机灯光
bpy.ops.object.camera_add(location=(0, -2.2, 1.15))
cam = bpy.context.active_object; cam.data.lens = 85
bpy.context.scene.camera = cam
d = mathutils.Vector((0,0,1.05)) - cam.location
cam.rotation_euler = d.to_track_quat("-Z","Y").to_euler()
bpy.ops.object.light_add(type="AREA", location=(1.2,-1.6,2.2))
k = bpy.context.active_object; k.data.energy = 120; k.data.size = 2
bpy.ops.object.light_add(type="AREA", location=(-1.4,-1.2,1.6))
f = bpy.context.active_object; f.data.energy = 50; f.data.size = 2

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x = 700; sc.render.resolution_y = 800
sc.view_settings.view_transform = "Standard"
sc.world = bpy.data.worlds.new("W"); sc.world.use_nodes = True
nt = sc.world.node_tree
bg = nt.nodes.get("Background") or nt.nodes.new("ShaderNodeBackground")
bg.inputs[1].default_value = 0.5
sc.render.filepath = os.path.join(out, "face.png")
bpy.ops.render.render(write_still=True)
print("RENDERED", sc.render.filepath)
