"""压缩 VRM：缩小贴图，重新导出，体积可降到原来的 1/4"""
import bpy, sys, os, addon_utils

args = sys.argv[sys.argv.index("--") + 1:]
src = args[args.index("--in") + 1]
dst = args[args.index("--out") + 1]
MAX = int(args[args.index("--max") + 1]) if "--max" in args else 1024

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=src)

n = 0
for img in list(bpy.data.images):
    if not img.size[0] or img.size[0] == 0:
        continue
    w, h = img.size
    if max(w, h) > MAX:
        s = MAX / max(w, h)
        img.scale(int(w * s), int(h * s))
        n += 1
    img.pack()
print("缩小贴图:", n, "张")

try:
    bpy.ops.export_scene.vrm(filepath=dst, export_invisibles=False, export_only_selections=False)
except TypeError:
    bpy.ops.export_scene.vrm(filepath=dst)
print("EXPORTED:", dst)
