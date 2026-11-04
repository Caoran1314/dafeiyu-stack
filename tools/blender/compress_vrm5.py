"""VRM 压缩：减面 → 贴图导出 → 调色板量化（外部 python）→ 回填 → 导出"""
import bpy, sys, os, addon_utils, subprocess, shutil

args = sys.argv[sys.argv.index("--") + 1:]
src = args[args.index("--in") + 1]
dst = args[args.index("--out") + 1]
ratio = float(args[args.index("--ratio") + 1]) if "--ratio" in args else 0.35
MAX = int(args[args.index("--max") + 1]) if "--max" in args else 512
COLORS = args[args.index("--colors") + 1] if "--colors" in args else "64"
TMP = r"D:/软件/_tmp/vrmq5"
shutil.rmtree(TMP, ignore_errors=True)
os.makedirs(TMP, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=src)

# 清掉形态键（表情用，占体积大）
for o in list(bpy.data.objects):
    if o.type == "MESH" and o.data.shape_keys:
        o.shape_key_clear()

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

pairs = []
for idx, img in enumerate(list(bpy.data.images)):
    if not img.size or img.size[0] == 0:
        continue
    w, h = img.size
    if max(w, h) > MAX:
        s = MAX / max(w, h)
        img.scale(int(w * s), int(h * s))
    raw = os.path.join(TMP, f"{idx}_raw.png")
    try:
        img.file_format = "PNG"
        img.filepath_raw = raw
        img.save()
        pairs.append((img, raw))
    except Exception as exc:
        print("保存失败", img.name, str(exc)[:50])

subprocess.run(["python", r"D:/软件/_tmp/quantize_png.py", TMP, COLORS], check=False)
print("准备回填", len(pairs), "张")

back = 0
for img, raw in pairs:
    q = raw.replace("_raw.png", "_q.png")
    if not os.path.exists(q):
        img.pack(); continue
    new = bpy.data.images.load(q, check_existing=False)
    new.pack()
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image == img:
                n.image = new
    back += 1
print("回填", back)

try:
    bpy.ops.export_scene.vrm(filepath=dst, export_invisibles=False, export_only_selections=False)
except TypeError:
    bpy.ops.export_scene.vrm(filepath=dst)
print("EXPORTED:", dst)
