"""VRM 极限压缩：减面 + 贴图转 JPEG（带透明的保留 PNG）"""
import bpy, sys, os, addon_utils

args = sys.argv[sys.argv.index("--") + 1:]
src = args[args.index("--in") + 1]
dst = args[args.index("--out") + 1]
ratio = float(args[args.index("--ratio") + 1]) if "--ratio" in args else 0.45
MAX = int(args[args.index("--max") + 1]) if "--max" in args else 512
TMP = r"D:/软件/_tmp/vrmtex"
os.makedirs(TMP, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=src)

for o in list(bpy.data.objects):
    if o.type != "MESH":
        continue
    if len(o.data.polygons) < 200:
        continue
    md = o.modifiers.new("Dec", "DECIMATE")
    md.ratio = ratio
    bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.modifier_apply(modifier=md.name)
    except Exception:
        o.modifiers.remove(md)

bpy.context.scene.render.image_settings.quality = 82
converted = 0
for idx, img in enumerate(list(bpy.data.images)):
    if not img.size or img.size[0] == 0:
        continue
    w, h = img.size
    if max(w, h) > MAX:
        s = MAX / max(w, h)
        img.scale(int(w * s), int(h * s))
    has_alpha = img.depth == 32 or img.channels == 4
    if has_alpha:
        img.pack()
        continue
    try:
        path = os.path.join(TMP, f"t{idx}.jpg")
        img.file_format = "JPEG"
        img.filepath_raw = path
        img.save()
        new = bpy.data.images.load(path, check_existing=False)
        new.pack()
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            for n in mat.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image == img:
                    n.image = new
        converted += 1
    except Exception as exc:
        print("跳过", img.name, exc)
        img.pack()

print("JPEG 转换:", converted, "张")
try:
    bpy.ops.export_scene.vrm(filepath=dst, export_invisibles=False, export_only_selections=False)
except TypeError:
    bpy.ops.export_scene.vrm(filepath=dst)
print("EXPORTED:", dst)
