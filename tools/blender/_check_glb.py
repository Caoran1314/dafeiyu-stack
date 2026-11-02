import bpy, sys
glb = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
mats = set()
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    names = [m.name if m else "None" for m in o.data.materials]
    for m in names: mats.add(m)
print("MESH 数:", len([o for o in bpy.data.objects if o.type=="MESH"]))
print("材质:", sorted(mats))
for m in bpy.data.materials:
    if m.use_nodes and m.node_tree.nodes.get("Principled BSDF"):
        c = m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value
        print(f"  {m.name}: {tuple(round(v,2) for v in c)}")
