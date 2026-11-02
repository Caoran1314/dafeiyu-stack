"""把 VRM 转成「网页友好」的 glb

做四件事：
  1. 材质从 MToon 转成 Principled BSDF（保留颜色贴图）
  2. 删掉模型自带的版权说明牌
  3. 朝向/原点统一（脚底中心、面向 -Y）
  4. 导出 character.glb

用法：
  blender --background --python convert_vrm_to_glb.py -- --vrm 输入.vrm --out 输出.glb
"""
import bpy
import sys
import os
import addon_utils

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
vrm = args[args.index("--vrm") + 1] if "--vrm" in args else None
out = args[args.index("--out") + 1] if "--out" in args else "character.glb"
if not vrm or not os.path.exists(vrm):
    raise SystemExit("缺少 --vrm 输入文件")

bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=vrm)

print("导入完成：对象", len(bpy.data.objects), "材质", len(bpy.data.materials))

# ---------------------------------------------------------------- 1) 删版权牌
removed = []
for o in list(bpy.data.objects):
    if o.type != "MESH":
        continue
    # 蒙皮网格保留
    if any(m.type == "ARMATURE" for m in o.modifiers):
        continue
    bb = [o.matrix_world @ __import__("mathutils").Vector(c) for c in o.bound_box]
    ys = [v.z for v in bb]
    h = max(ys) - min(ys)
    cz = sum(ys) / len(ys)
    if h > 0.5 and cz > 1.3:          # 头顶上方的大板子
        removed.append(o.name)
        bpy.data.objects.remove(o, do_unlink=True)
print("删除说明牌：", removed or "无")


def find_image(mat):
    """在材质节点里找第一张图片贴图。"""
    if not mat or not mat.use_nodes:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            return n.image
    return None


# ---------------------------------------------------------------- 2) 材质转换
converted = 0
cache = {}
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    for slot in o.material_slots:
        m = slot.material
        if not m:
            continue
        if m.name in cache:
            slot.material = cache[m.name]
            continue
        img = find_image(m)
        new = bpy.data.materials.new(name=m.name + "_pbr")
        new.use_nodes = True
        nt = new.node_tree
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if bsdf is None:
            bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
            out_node = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
            if out_node:
                nt.links.new(bsdf.outputs["BSDF"], out_node.inputs["Surface"])
        bsdf.inputs["Roughness"].default_value = 0.62
        bsdf.inputs["Metallic"].default_value = 0.0
        if img:
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            tex.location = (-420, 260)
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            if img.depth == 32 or "alpha" in img.name.lower() or m.blend_method in ("HASHED", "BLEND"):
                nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        # 透明度设置（脸部贴图、头发边缘）
        if m.blend_method in ("HASHED", "BLEND"):
            new.blend_method = "BLEND" if m.blend_method == "BLEND" else "HASHED"
            new.use_backface_culling = False
        else:
            new.blend_method = "OPAQUE"
        cache[m.name] = new
        slot.material = new
        converted += 1
print("材质转换：", converted, "个")

# ---------------------------------------------------------------- 3) 方向与落地
arm = next((o for o in bpy.data.objects if o.type == "ARMATURE"), None)
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
if arm:
    # VRM 导入后通常面向 +Y；网页需要面向 -Y（导出后 +Z）
    arm.rotation_euler[2] = 0.0
# 让最低点落到 z=0
import mathutils
minz = min((o.matrix_world @ mathutils.Vector(c)).z
           for o in meshes for c in o.bound_box)
for o in bpy.data.objects:
    if o.parent is None:
        o.location.z -= minz
print("落地偏移：", round(-minz, 3))

# ---------------------------------------------------------------- 4) 导出
bpy.ops.object.select_all(action="SELECT")
bpy.ops.export_scene.gltf(
    filepath=out,
    export_format="GLB",
    use_selection=False,
    export_apply=False,
    export_yup=True,
    export_animations=True,
    export_cameras=False,
    export_lights=False,
)
print("EXPORTED:", out)
