import bpy, sys, addon_utils, mathutils, re
vrm = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=vrm)
print("--- 名称含关键词的物体 ---")
for o in bpy.data.objects:
    if re.search(r"text|plate|credit|board|plane|sign|bill|atlas|emote|hat|cap|bowl|dome", o.name, re.I):
        mats = [s.material.name if s.material else None for s in o.material_slots] if o.type=="MESH" else []
        print(" ", o.type, o.name, mats)
print("--- 材质名含关键词 ---")
for m in bpy.data.materials:
    if re.search(r"text|plate|credit|board|sign|hat|cap", m.name, re.I):
        print("  MAT", m.name)
