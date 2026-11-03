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
keep_mtoon = "--keep-mtoon" in args
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

# 删掉可选配件与描边壳（草帽/猫耳/狐狸尾/Outline），这些在网页里只会变成金属块
# ve_emote/atlas/facebaked 是“脸部+版权牌”的叠加面片，必须删
drop_keys = ("strawhat", "cat_ear", "catear", "foxtail", "fox_tail", "outline",
             "ve_emote", "emoteatlas", "facebaked")
dropped = []
for o in list(bpy.data.objects):
    if o.type != "MESH":
        continue
    names = [s.material.name.lower() for s in o.material_slots if s.material]
    objname = o.name.lower()
    if any(any(k in n for k in drop_keys) for n in names) or any(k in objname for k in drop_keys):
        dropped.append(o.name)
        bpy.data.objects.remove(o, do_unlink=True)
print("清理配件：", len(dropped), "个", dropped[:6])


def find_image(mat):
    """在材质节点里找第一张图片贴图。"""
    if not mat or not mat.use_nodes:
        return None
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            return n.image
    return None


# ---------------------------------------------------------------- 2) 材质转换
def convert_material(m):
    """MToon/自定义 → Principled BSDF，保留贴图与透明度。"""
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
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        new.blend_method = "CLIP" if m.blend_method in ("HASHED", "CLIP") else (
            "BLEND" if m.blend_method == "BLEND" else "OPAQUE")
    else:
        # 没有贴图就用 MToon 的基础色，实在拿不到就白色
        col = None
        for n in (m.node_tree.nodes if m.use_nodes else []):
            if n.type == "RGB" and n.outputs:
                col = n.outputs[0].default_value
                break
        if col:
            bsdf.inputs["Base Color"].default_value = col
        new.blend_method = "OPAQUE"
    new.use_backface_culling = False
    return new


mapping = {}
for m in ([] if keep_mtoon else list(bpy.data.materials)):
    if m.name.endswith("_pbr"):
        continue
    try:
        mapping[m.name] = convert_material(m)
    except Exception as exc:
        print("材质转换失败:", m.name, exc)

replaced = 0
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    for slot in o.material_slots:
        if slot.material and slot.material.name in mapping:
            slot.material = mapping[slot.material.name]
            replaced += 1
print("材质转换：", len(mapping), "个，替换 slot", replaced, "次（keep_mtoon =", keep_mtoon, "）")

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
