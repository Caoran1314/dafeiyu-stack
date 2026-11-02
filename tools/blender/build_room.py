"""用 Blender 生成房子骨架 → room.glb

用法（Windows）：
  "D:\\软件\\blender\\blender-4.5.9-windows-x64\\blender.exe" --background --python build_room.py -- --out "输出路径.glb"

房型（米，Z 向上，导出时自动转 glTF 的 Y 向上）：
  总尺寸 14 × 5.6，层高 2.7
  主卧   x -7.0..-3.6
  客厅   x -3.6..3.4, z 0.0..3.0
  猫房   x -3.6..3.4, z -2.6..0.0
  电竞房 x  3.4..7.0
  门洞   3 处（宽 1.0，高 2.1）
"""
import bpy
import sys
import math
import os

# ---------------------------------------------------------------- 参数
argv = sys.argv
out_path = None
if "--" in argv:
    args = argv[argv.index("--") + 1:]
    if "--out" in args:
        out_path = args[args.index("--out") + 1]
if not out_path:
    out_path = os.path.join(os.path.dirname(__file__), "room.glb")

WALL_H = 2.7
TH = 0.14
X1, X2 = -7.0, 7.0
Z1, Z2 = -2.6, 3.0
DOOR_W, DOOR_H = 1.0, 2.1


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_material(name, color, rough=0.65, metal=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat


def box(name, sx, sy, sz, x, y, z, mat):
    """sx/sy/sz 是尺寸，x/y/z 是中心点（Z 向上）。"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def build():
    reset_scene()
    mat_floor = make_material("Floor", (0.62, 0.55, 0.46, 1), rough=0.42)
    mat_wall = make_material("Wall", (0.88, 0.86, 0.83, 1), rough=0.85)
    mat_trim = make_material("Trim", (0.78, 0.75, 0.71, 1), rough=0.7)

    # 地板（略厚，避免 z-fighting）
    box("Floor", X2 - X1, Z2 - Z1, 0.08, (X1 + X2) / 2, (Z1 + Z2) / 2, -0.04, mat_floor)

    # 外墙：前后 + 左右
    box("Wall_Back", X2 - X1, TH, WALL_H, 0, Z1 - TH / 2, WALL_H / 2, mat_wall)
    box("Wall_Front", X2 - X1, TH, WALL_H, 0, Z2 + TH / 2, WALL_H / 2, mat_wall)
    box("Wall_Left", TH, Z2 - Z1, WALL_H, X1 - TH / 2, 0, WALL_H / 2, mat_wall)
    box("Wall_Right", TH, Z2 - Z1, WALL_H, X2 + TH / 2, 0, WALL_H / 2, mat_wall)

    # 隔墙 1：主卧 | 其余（x = -3.6），门在 z = 1.4
    door_z = 1.4
    seg_back = (door_z - DOOR_W / 2) - Z1
    seg_front = Z2 - (door_z + DOOR_W / 2)
    box("Part_Bed_Back", TH, seg_back, WALL_H, -3.6, Z1 + seg_back / 2, WALL_H / 2, mat_wall)
    box("Part_Bed_Front", TH, seg_front, WALL_H, -3.6, Z2 - seg_front / 2, WALL_H / 2, mat_wall)
    box("Part_Bed_Lintel", TH, DOOR_W, WALL_H - DOOR_H, -3.6, door_z, DOOR_H + (WALL_H - DOOR_H) / 2, mat_wall)

    # 隔墙 2：客厅/猫房 | 电竞房（x = 3.4），门在 z = 1.15
    door_z2 = 1.15
    seg_back2 = (door_z2 - DOOR_W / 2) - Z1
    seg_front2 = Z2 - (door_z2 + DOOR_W / 2)
    box("Part_Living_Back", TH, seg_back2, WALL_H, 3.4, Z1 + seg_back2 / 2, WALL_H / 2, mat_wall)
    box("Part_Living_Front", TH, seg_front2, WALL_H, 3.4, Z2 - seg_front2 / 2, WALL_H / 2, mat_wall)
    box("Part_Living_Lintel", TH, DOOR_W, WALL_H - DOOR_H, 3.4, door_z2, DOOR_H + (WALL_H - DOOR_H) / 2, mat_wall)

    # 隔墙 3：猫房 | 客厅（z = 0.0），门在 x = -1.3
    door_x = -1.3
    seg_left = (door_x - DOOR_W / 2) - (-3.6)
    seg_right = 3.4 - (door_x + DOOR_W / 2)
    box("Part_Cat_Left", seg_left, TH, WALL_H, -3.6 + seg_left / 2, 0, WALL_H / 2, mat_wall)
    box("Part_Cat_Right", seg_right, TH, WALL_H, 3.4 - seg_right / 2, 0, WALL_H / 2, mat_wall)
    box("Part_Cat_Lintel", DOOR_W, TH, WALL_H - DOOR_H, door_x, 0, DOOR_H + (WALL_H - DOOR_H) / 2, mat_wall)

    # 踢脚线（观感提升明显）
    for name, sx, sy, x, y in [
        ("Trim_Back", X2 - X1, 0.05, 0, Z1 + 0.05),
        ("Trim_Front", X2 - X1, 0.05, 0, Z2 - 0.05),
        ("Trim_Left", 0.05, Z2 - Z1, X1 + 0.05, 0),
        ("Trim_Right", 0.05, Z2 - Z1, X2 - 0.05, 0),
    ]:
        box(name, sx, sy, 0.1, x, y, 0.05, mat_trim)

    # 天花板（单独物件，页面按需隐藏）
    box("Ceiling", X2 - X1, Z2 - Z1, 0.06, 0, 0, WALL_H + 0.03, mat_wall)

    # 收纳到一个集合，方便导出/管理
    for obj in bpy.data.objects:
        obj.select_set(True)

    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_yup=True,
        export_cameras=False,
        export_lights=False,
    )
    print("EXPORTED:", out_path)


build()
