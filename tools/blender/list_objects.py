import bpy, sys, addon_utils, mathutils
vrm = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
addon_utils.enable("bl_ext.user_default.vrm", default_set=True, persistent=True)
bpy.ops.import_scene.vrm(filepath=vrm)
rows = []
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    pts = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    zs = [p.z for p in pts]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    rows.append((max(zs), max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs), o.name,
                 [s.material.name if s.material else None for s in o.material_slots][:2]))
rows.sort(reverse=True)
print("MESH 数:", len(rows))
print("--- 最高的 12 个 ---")
for z, w, d, h, name, mats in rows[:12]:
    print(f"  z={z:.2f} w={w:.2f} d={d:.2f} h={h:.2f} {name} | {mats}")
