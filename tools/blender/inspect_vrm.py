import bpy, sys, os
glb = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
import addon_utils
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=glb)
objs = [o for o in bpy.data.objects]
print("OBJECTS:", len(objs))
for o in objs[:8]:
    print("  ", o.type, o.name, "parent=", o.parent.name if o.parent else None)
mats = list(bpy.data.materials)
print("MATERIALS:", len(mats))
for m in mats[:12]:
    nodes = [n.type for n in m.node_tree.nodes] if m.use_nodes else []
    print("  ", m.name, "| blend:", m.blend_method, "| nodes:", nodes[:6])
