"""用 Blender 建整个房间（12×12 正方形，四区 + 家具）

坐标约定：
  Blender  X = 网页 x
  Blender  Y = -网页 z
  Blender  Z = 高度
导出时 +Y 向上，网页里就是 (x, z, -y) → 与页面锚点坐标一致。

用法：
  blender --background --python build_apartment.py -- --out room.glb
"""
import bpy
import bmesh
import math
import sys
import os

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
out = args[args.index("--out") + 1] if "--out" in args else "room.glb"

R = 6.0        # 半边长（12×12）
H = 2.8        # 层高
WALL = 0.14    # 墙厚

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"


# ---------------------------------------------------------------- 材质
def mat(name, color, rough=0.6, metal=0.0, alpha=1.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m


M_WALL = mat("Wall", (0.93, 0.93, 0.92), 0.85)
M_FLOOR = mat("Floor", (0.86, 0.87, 0.88), 0.35)
M_CEIL = mat("Ceil", (0.95, 0.95, 0.94), 0.9)
M_WOOD = mat("Wood", (0.28, 0.20, 0.14), 0.55)
M_WOOD_L = mat("WoodLight", (0.55, 0.42, 0.30), 0.55)
M_FABRIC = mat("Fabric", (0.92, 0.91, 0.88), 0.9)
M_LINEN = mat("Linen", (0.80, 0.86, 0.90), 0.9)
M_DARK = mat("Dark", (0.10, 0.10, 0.11), 0.5)
M_METAL = mat("Metal", (0.45, 0.47, 0.50), 0.3, 0.8)
M_SCREEN = mat("Screen", (0.06, 0.09, 0.12), 0.15)
M_GREEN = mat("Plant", (0.18, 0.45, 0.26), 0.7)
M_CAT = mat("CatFur", (0.85, 0.82, 0.76), 0.85)
M_RUG = mat("Rug", (0.88, 0.92, 0.95), 0.95)
M_GLASS = mat("Glass", (0.35, 0.62, 0.80), 0.1, 0.0, 0.35)
M_CITY = mat("City", (0.10, 0.24, 0.38), 0.8)


# ---------------------------------------------------------------- 工具
def box(name, sx, sy, sz, x, y, z, rz=0.0, m=None, bevel=0.015):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    o.rotation_euler[2] = rz
    if m:
        o.data.materials.append(m)
    if bevel:
        md = o.modifiers.new(name="Bevel", type="BEVEL")
        md.width = bevel
        md.segments = 2
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=md.name)
    return o


def cyl(name, r, h, x, y, z, rz=0.0, m=None, seg=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=h, location=(x, y, z))
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler[2] = rz
    if m:
        o.data.materials.append(m)
    return o


def sph(name, r, x, y, z, m=None, sy=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=r, location=(x, y, z))
    o = bpy.context.active_object
    o.name = name
    if sy:
        o.scale = (1, sy, 1)
    if m:
        o.data.materials.append(m)
    return o


def J(x, z):
    """网页坐标 (x,z) → Blender (x,y)"""
    return x, -z


# ---------------------------------------------------------------- 地板 / 天花
box("Floor", R * 2, R * 2, 0.1, 0, 0, -0.05, m=M_FLOOR, bevel=0)
# 天花板不导出（俯视看不到室内）

# 外墙
box("WallN", R * 2, WALL, H, 0, R, H / 2, m=M_WALL, bevel=0)      # z=+6 → y=-6 不对，见下
# 注意：网页 z=+6 对应 Blender y=-6；这里逐个写清楚
bpy.data.objects.remove(bpy.data.objects["WallN"], do_unlink=True)


def wall_x(name, x, z0, z1, door=None, door_w=1.0):
    """沿 z 方向的墙（Blender y 方向），带门洞和过梁"""
    y0, y1 = -z1, -z0
    segs = [(y0, y1)] if door is None else [
        (y0, -door - door_w / 2), (-door + door_w / 2, y1)]
    i = 0
    for a, b in segs:
        if b - a < 0.05:
            continue
        box(f"{name}_{i}", WALL, b - a, H, x, (a + b) / 2, H / 2, m=M_WALL, bevel=0)
        i += 1
    if door is not None:
        box(f"{name}_lintel", WALL, door_w, H - 2.1, x, -door, (H + 2.1) / 2, m=M_WALL, bevel=0)


def wall_z(name, z, x0, x1, door=None, door_w=1.0):
    """沿 x 方向的墙"""
    y = -z
    segs = [(x0, x1)] if door is None else [
        (x0, door - door_w / 2), (door + door_w / 2, x1)]
    i = 0
    for a, b in segs:
        if b - a < 0.05:
            continue
        box(f"{name}_{i}", b - a, WALL, H, (a + b) / 2, y, H / 2, m=M_WALL, bevel=0)
        i += 1
    if door is not None:
        box(f"{name}_lintel", door_w, WALL, H - 2.1, door, y, (H + 2.1) / 2, m=M_WALL, bevel=0)


# 外墙
wall_z("OuterS", -R, -R, R)
wall_z("OuterN", R, -R, R)
wall_x("OuterW", -R, -R, R)
wall_x("OuterE", R, -R, R)

# 隔断（与网页一致）
wall_z("BedLiving", 1, -R, -1, door=-3.5)      # 主卧 ↔ 客厅
wall_x("LeftHall", -1, -5, 1, door=-3)          # 电竞房 ↔ 玄关
wall_x("CatHall", 1, -R, -1, door=-3.5)         # 猫房 ↔ 玄关
wall_z("CatLiving", -1, 1, R, door=3.5)         # 猫房 ↔ 客厅

# 踢脚线
for (x, z, w, d) in [(0, -R + 0.07, R * 2, 0.02), (0, R - 0.07, R * 2, 0.02),
                     (-R + 0.07, 0, 0.02, R * 2), (R - 0.07, 0, 0.02, R * 2)]:
    box("Baseboard", w, d, 0.1, x, -z, 0.05, m=M_WALL, bevel=0)

# 主卧窗户（西墙 x=-6，z=4.6）
win_x, win_z = -R + 0.02, 4.6
box("WinFrame", 0.06, 2.2, 1.6, win_x, -win_z, 1.62, m=M_WALL, bevel=0)
box("WinGlass", 0.03, 2.0, 1.4, win_x + 0.04, -win_z, 1.62, m=M_CITY, bevel=0)
box("WinGlow", 0.02, 1.9, 1.3, win_x + 0.06, -win_z, 1.62, m=M_GLASS, bevel=0)


# ---------------------------------------------------------------- 家具
def rug(name, x, z, r, m=M_RUG):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=r, depth=0.012, location=(x, -z, 0.008))
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(m)
    return o


# ===== 客厅 =====
# 沙发 (2.4, 3.6) 面向 +z（北）
sx, sy = J(2.4, 3.6)
box("SofaBase", 1.9, 0.95, 0.34, sx, sy, 0.2, m=M_FABRIC)
box("SofaBack", 1.9, 0.22, 0.66, sx, sy - 0.4, 0.55, m=M_FABRIC)
box("SofaArmL", 0.22, 0.95, 0.5, sx - 0.95, sy, 0.4, m=M_FABRIC)
box("SofaArmR", 0.22, 0.95, 0.5, sx + 0.95, sy, 0.4, m=M_FABRIC)
box("SofaCushion", 1.7, 0.8, 0.14, sx, sy + 0.02, 0.42, m=M_LINEN)
for dx in (-0.45, 0.45):
    box("SofaPillow", 0.42, 0.16, 0.34, sx + dx, sy - 0.28, 0.58, rz=0.1, m=M_LINEN)

# 地毯 + 茶几
rug("LivingRug", 2.4, 4.35, 1.55)
box("CoffeeTop", 1.1, 0.6, 0.06, 2.4, -4.3, 0.42, m=M_WOOD)
for dx, dy in [(-0.5, -0.25), (0.5, -0.25), (-0.5, 0.25), (0.5, 0.25)]:
    box("CoffeeLeg", 0.06, 0.06, 0.4, 2.4 + dx, -4.3 + dy, 0.2, m=M_DARK, bevel=0)

# 电视柜 + 电视（北墙 z=5.68）
box("TvUnit", 1.8, 0.42, 0.42, 2.4, -5.68, 0.21, m=M_WOOD)
box("TvBody", 1.6, 0.06, 0.9, 2.4, -5.9, 1.2, m=M_DARK)
box("TvScreen", 1.5, 0.02, 0.8, 2.4, -5.86, 1.2, m=M_SCREEN, bevel=0)

# 餐桌 + 4 椅
box("DiningTop", 1.5, 0.9, 0.06, 4.7, -1.3, 0.74, m=M_WOOD)
for dx, dy in [(-0.65, -0.35), (0.65, -0.35), (-0.65, 0.35), (0.65, 0.35)]:
    box("DiningLeg", 0.07, 0.07, 0.72, 4.7 + dx, -1.3 + dy, 0.36, m=M_DARK, bevel=0)
for i, (dx, dy, rz) in enumerate([(-0.95, 0, 0), (0.95, 0, math.pi), (0, -0.75, math.pi / 2), (0, 0.75, -math.pi / 2)]):
    box(f"ChairSeat{i}", 0.42, 0.42, 0.06, 4.7 + dx, -1.3 + dy, 0.45, rz=rz, m=M_WOOD_L)
    box(f"ChairBack{i}", 0.42, 0.06, 0.45, 4.7 + dx, -1.3 + dy - 0.18, 0.68, rz=rz, m=M_WOOD_L)

# 开放厨房（东墙 x=5.6，z 0.9~3.5）
box("KitchenCounter", 0.62, 2.6, 0.88, 5.6, -2.2, 0.44, m=M_WOOD)
box("KitchenTop", 0.68, 2.66, 0.05, 5.6, -2.2, 0.9, m=M_WOOD_L, bevel=0)
box("KitchenSink", 0.5, 0.5, 0.04, 5.55, -1.7, 0.92, m=M_METAL, bevel=0)
box("KitchenCabinet", 0.6, 2.6, 0.7, 5.62, -2.2, 1.75, m=M_FABRIC)

# 书架（东墙）
box("ShelfBody", 0.34, 1.5, 1.9, 5.6, -3.6, 0.95, m=M_WOOD)
for i in range(4):
    box(f"ShelfBoard{i}", 0.3, 1.44, 0.04, 5.58, -3.6, 0.35 + i * 0.42, m=M_WOOD_L, bevel=0)
    for j in range(2):
        box(f"Book{i}{j}", 0.22, 0.12, 0.26, 5.56, -4.1 + j * 0.35 + i * 0.1, 0.52 + i * 0.42, m=M_LINEN, bevel=0)

# 落地灯（客厅北侧）
cyl("LampBase", 0.2, 0.04, 0.15, -5.15, 0.02, m=M_DARK)
cyl("LampPole", 0.025, 1.6, 0.15, -5.15, 0.82, m=M_METAL)
cyl("LampShade", 0.24, 0.3, 0.15, -5.15, 1.66, m=M_FABRIC, seg=20)

# 绿植（客厅东北角）
cyl("Pot", 0.18, 0.34, 5.2, -5.3, 0.17, m=M_WOOD_L)
for i in range(5):
    a = i * math.pi * 0.4
    sph("Leaf", 0.22, 5.2 + math.cos(a) * 0.12, -5.3 + math.sin(a) * 0.12, 0.55 + i * 0.08, m=M_GREEN, sy=0.8)

# ===== 主卧 =====
bx, by = J(-4.0, 4.55)
box("BedFrame", 2.1, 1.6, 0.3, bx, by, 0.15, m=M_DARK)
box("BedMattress", 2.0, 1.5, 0.24, bx, by, 0.42, m=M_FABRIC)
box("BedSheet", 1.95, 1.45, 0.1, bx, by, 0.56, m=M_LINEN)
box("BedHead", 2.12, 0.12, 0.9, bx, by + 0.8, 0.62, m=M_WOOD)
box("BedPillow1", 0.6, 0.34, 0.14, bx - 0.5, by + 0.5, 0.64, rz=0.05, m=M_FABRIC)
box("BedPillow2", 0.6, 0.34, 0.14, bx + 0.05, by + 0.5, 0.64, m=M_FABRIC)

for nx in (-5.55, -2.45):
    box("Nightstand", 0.45, 0.42, 0.5, nx, -4.55, 0.25, m=M_WOOD)
    box("NsTop", 0.48, 0.45, 0.04, nx, -4.55, 0.52, m=M_WOOD_L, bevel=0)

# 衣柜（西墙 x=-5.62，z=2.4）
box("Wardrobe", 0.6, 2.6, 2.3, -5.62, -2.4, 1.15, m=M_WOOD)
for i in range(3):
    box("WardrobeDoor", 0.02, 0.8, 2.2, -5.31, -3.2 + i * 0.85, 1.15, m=M_WOOD_L, bevel=0)

# 梳妆台（东墙 x=-1.62，z=3.2）+ 镜子
box("DresserBody", 0.5, 1.2, 0.78, -1.62, -3.2, 0.39, m=M_WOOD_L)
box("DresserTop", 0.54, 1.24, 0.05, -1.62, -3.2, 0.8, m=M_WOOD, bevel=0)
cyl("MirrorRing", 0.3, 0.03, -1.9, -3.2, 1.45, rz=math.pi / 2, m=M_DARK)
cyl("MirrorGlass", 0.27, 0.012, -1.88, -3.2, 1.45, rz=math.pi / 2, m=M_GLASS)

rug("BedRug", -4.0, 3.35, 1.05, M_RUG)

# ===== 电竞房 =====
dx_, dy_ = J(-3.5, -4.55)
box("DeskTop", 1.9, 0.8, 0.06, dx_, dy_, 0.76, m=M_WOOD)
for ddx, ddy in [(-0.85, -0.32), (0.85, -0.32), (-0.85, 0.32), (0.85, 0.32)]:
    box("DeskLeg", 0.07, 0.07, 0.74, dx_ + ddx, dy_ + ddy, 0.37, m=M_DARK, bevel=0)
box("MonitorStand", 0.2, 0.2, 0.06, dx_, dy_ + 0.1, 0.79, m=M_DARK, bevel=0)
box("MonitorBody", 0.9, 0.06, 0.52, dx_, dy_ + 0.16, 1.06, m=M_DARK)
box("MonitorScreen", 0.84, 0.02, 0.46, dx_, dy_ + 0.13, 1.06, m=M_SCREEN, bevel=0)
box("Monitor2", 0.52, 0.03, 0.3, dx_ + 0.72, dy_ + 0.1, 1.02, rz=-0.4, m=M_SCREEN, bevel=0)
box("Keyboard", 0.5, 0.16, 0.03, dx_, dy_ - 0.12, 0.8, m=M_DARK, bevel=0)

# 电竞椅
cx, cy = J(-3.5, -3.7)
box("ChairSeat", 0.5, 0.5, 0.08, cx, cy, 0.48, m=M_DARK)
box("ChairBack", 0.5, 0.1, 0.7, cx, cy - 0.22, 0.85, m=M_DARK)
cyl("ChairPole", 0.05, 0.4, cx, cy, 0.24, m=M_METAL)
cyl("ChairBase", 0.3, 0.04, cx, cy, 0.04, m=M_DARK)

# 机箱（RGB）
px, py = J(-5.1, -4.55)
box("PcCase", 0.25, 0.45, 0.5, px, py, 0.25, m=M_DARK)
box("PcGlass", 0.02, 0.4, 0.44, px + 0.13, py, 0.25, m=M_GLASS, bevel=0)

# 置物架（西墙）
box("GShelf", 0.3, 1.4, 1.4, -5.62, 2.2, 0.7, m=M_WOOD)
for i in range(3):
    box("GShelfBoard", 0.28, 1.36, 0.04, -5.6, 2.2, 0.25 + i * 0.45, m=M_WOOD_L, bevel=0)

# 海报（北墙 z=-5）
box("Poster", 1.1, 0.03, 0.78, -3.5, 4.95, 1.7, m=M_LINEN, bevel=0)

# 落地灯（电竞房）
cyl("GLampBase", 0.18, 0.04, -1.8, 4.55, 0.02, m=M_DARK)
cyl("GLampPole", 0.022, 1.55, -1.8, 4.55, 0.8, m=M_METAL)
cyl("GLampShade", 0.2, 0.26, -1.8, 4.55, 1.6, m=M_FABRIC, seg=18)

# ===== 猫房 =====
def cat_tree(name, x, z, h=1.6):
    cx, cy = J(x, z)
    box(f"{name}_base", 0.5, 0.5, 0.06, cx, cy, 0.03, m=M_WOOD_L)
    cyl(f"{name}_post", 0.06, h, cx, cy, h / 2, m=M_WOOD_L)
    for i, hz in enumerate((0.5, 1.0, 1.45)):
        box(f"{name}_plat{i}", 0.5, 0.5, 0.05, cx, cy, hz, m=M_WOOD_L)
    box(f"{name}_house", 0.42, 0.42, 0.34, cx + 0.1, cy, 1.2, m=M_CAT)


cat_tree("CatTree1", 1.9, -5.0)
cat_tree("CatTree2", 5.1, -5.2, 1.7)

for name, x, z in [("CatBed1", 2.4, -2.4), ("CatBed2", 4.6, -2.6)]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.4, depth=0.16,
                                        location=(x, -z, 0.08))
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(M_CAT)

x_, y_ = J(5.4, -3.4)
box("LitterBox", 0.6, 0.5, 0.3, x_, y_, 0.15, m=M_LINEN)
box("BowlStand", 0.6, 0.28, 0.04, 3.6, 5.3, 0.02, m=M_WOOD_L, bevel=0)
for dx in (-0.15, 0.15):
    cyl("Bowl", 0.1, 0.06, 3.6 + dx, 5.3, 0.06, m=M_LINEN, seg=18)

x_, y_ = J(1.5, -3.4)
box("ScratchPad", 0.5, 0.3, 0.06, x_, y_, 0.03, m=M_WOOD_L, bevel=0)
box("ScratchPole", 0.05, 0.05, 0.7, x_, y_, 0.35, m=M_WOOD_L, bevel=0)

# ===== 玄关 =====
box("ShoeCabinet", 1.2, 0.36, 0.9, 0, 5.62, 0.45, m=M_WOOD)
box("ShoeTop", 1.2, 0.38, 0.04, 0, 5.62, 0.92, m=M_WOOD_L, bevel=0)

# 基础照明（面光）
bpy.ops.object.light_add(type="AREA", location=(2.4, -3.0, 2.6))
k = bpy.context.active_object
k.data.energy = 300
k.data.size = 6

bpy.ops.object.light_add(type="AREA", location=(-3.5, -3.5, 2.6))
k2 = bpy.context.active_object
k2.data.energy = 200
k2.data.size = 5

bpy.ops.export_scene.gltf(
    filepath=out,
    export_format="GLB",
    use_selection=False,
    export_apply=True,
    export_yup=True,
    export_cameras=False,
    export_lights=False,
)
print("EXPORTED:", out)
