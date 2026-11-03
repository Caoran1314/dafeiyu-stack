import bpy, sys, mathutils
glb = sys.argv[sys.argv.index("--")+1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rows=[]
for o in bpy.data.objects:
    if o.type!="MESH": continue
    pts=[o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
    xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
    w=max(xs)-min(xs); d=max(ys)-min(ys); h=max(zs)-min(zs); cz=(max(zs)+min(zs))/2
    imgs=[]
    for s in o.material_slots:
        m=s.material
        if m and m.use_nodes:
            for n in m.node_tree.nodes:
                if n.type=="TEX_IMAGE" and n.image: imgs.append(n.image.name)
    rows.append((w*d, w, d, h, cz, o.name, imgs[:2]))
rows.sort(reverse=True)
print("--- 面积最大的 8 个 ---")
for a,w,d,h,cz,name,imgs in rows[:8]:
    print(f"  area={a:.2f} w={w:.2f} d={d:.2f} h={h:.2f} cz={cz:.2f} {name} {imgs}")
print("--- 位置高于 1.4 的 ---")
for a,w,d,h,cz,name,imgs in rows:
    if cz>1.4: print(f"  w={w:.2f} d={d:.2f} h={h:.2f} cz={cz:.2f} {name} {imgs}")
