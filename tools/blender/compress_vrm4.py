"""VRM 压缩：减面 + 贴图调色板量化（保留透明）"""
import bpy, sys, os, addon_utils
from PIL import Image as PILImage

args = sys.argv[sys.argv.index("--") + 1:]
src = args[args.index("--in") + 1]
dst = args[args.index("--out") + 1]
ratio = float(args[args.index("--ratio") + 1]) if "--ratio" in args else 0.35
MAX = int(args[args.index("--max") + 1]) if "--max" in args else 512
COLORS = int(args[args.index("--colors") + 1]) if "--colors" in args else 64
TMP = r"D:/软件/_tmp/vrmq"
os.makedirs(TMP, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=src)

for o in list(bpy.data.objects):
    if o.type != "MESH" or len(o.data.polygons) < 200:
        continue
    md = o.modifiers.new("Dec", "DECIMATE")
    md.ratio = ratio
    bpy.context.view_layer.objects.active = o
    try:
        bpy.ops.object.modifier_apply(modifier=md.name)
    except Exception:
        o.modifiers.remove(md)

bpy.context.scene.render.image_settings.file_format = "PNG"
ok = 0
for idx, img in enumerate(list(bpy.data.images)):
    if not img.size or img.size[0] == 0:
        continue
    w, h = img.size
    if max(w, h) > MAX:
        s = MAX / max(w, h)
        img.scale(int(w * s), int(h * s))
    try:
        raw = os.path.join(TMP, f"{idx}_raw.png")
        img.file_format = "PNG"
        img.filepath_raw = raw
        img.save()
        pil = PILImage.open(raw).convert("RGBA")
        q = pil.quantize(colors=COLORS, method=PILImage.FASTOCTREE, dither=PILImage.Dither.NONE)
        out = os.path.join(TMP, f"{idx}_q.png")
        q.save(out, optimize=True)
        new = bpy.data.images.load(out, check_existing=False)
        new.pack()
        for mat in bpy.data.materials:
            if not mat.use_nodes:
                continue
            for n in mat.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image == img:
                    n.image = new
        ok += 1
    except Exception as exc:
        print("跳过", img.name, str(exc)[:60])
        img.pack()

print("量化贴图:", ok)
try:
    bpy.ops.export_scene.vrm(filepath=dst, export_invisibles=False, export_only_selections=False)
except TypeError:
    bpy.ops.export_scene.vrm(filepath=dst)
print("EXPORTED:", dst)
