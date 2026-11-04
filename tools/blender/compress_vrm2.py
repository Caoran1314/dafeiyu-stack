"""压缩 VRM：减面 + 缩图，目标 8~12MB"""
import bpy, sys, os, addon_utils

args = sys.argv[sys.argv.index("--") + 1:]
src = args[args.index("--in") + 1]
dst = args[args.index("--out") + 1]
ratio = float(args[args.index("--ratio") + 1]) if "--ratio" in args else 0.45
MAX = int(args[args.index("--max") + 1]) if "--max" in args else 512

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=src)

# 减面
tri_before = tri_after = 0
for o in list(bpy.data.objects):
    if o.type != "MESH":
        continue
    me = o.data
    tri_before += sum(len(p.vertices) - 2 for p in me.polygons)
    if len(me.polygons) < 200:
        tri_after += sum(len(p.vertices) - 2 for p in me.polygons)
        continue
    md = o.modifiers.new("Dec", "DECIMATE")
    md.ratio = ratio
    bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.modifier_apply(modifier=md.name)
    except Exception:
        o.modifiers.remove(md)
    tri_after += sum(len(p.vertices) - 2 for p in o.data.polygons)
print("三角面:", tri_before, "→", tri_after)

# 缩图
n = 0
for img in list(bpy.data.images):
    if not img.size or img.size[0] == 0:
        continue
    w, h = img.size
    if max(w, h) > MAX:
        s = MAX / max(w, h)
        img.scale(int(w * s), int(h * s))
        n += 1
    img.pack()
print("缩小贴图:", n)

try:
    bpy.ops.export_scene.vrm(filepath=dst, export_invisibles=False, export_only_selections=False)
except TypeError:
    bpy.ops.export_scene.vrm(filepath=dst)
print("EXPORTED:", dst)
