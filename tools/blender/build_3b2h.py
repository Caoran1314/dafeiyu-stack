"""三室两厅（14 × 15 m ≈ 210㎡）

布局：
  左上 次卧A 3.25×3   右上 次卧B 3.25×3
  左侧 走廊 6.5×1.2
  左中 主卫 3×2.3     右中 衣帽间 3.5×2.3
  左下 主卧 6.5×6     右侧 厨房 4.5×2.5 / 玄关 3×2.5 / 餐厅 7.5×3 / 客厅 7.5×7
  底部 阳台 7.5×2.5

坐标：x 向右，z 向下（Blender y = -z）
"""
import bpy
import math
import sys
import os

argv = sys.argv
args = argv[argv.index("--") + 1:] if "--" in argv else []
out = args[args.index("--out") + 1] if "--out" in args else "room.glb"

WALL = 0.12
H = 2.85
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")

bpy.ops.wm.read_factory_settings(use_empty=True)


# ---------------------------------------------------------------- 材质
def tex_mat(name, file, scale=1.0, rough=0.6, metal=0.0, normal=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    p = os.path.join(TEX, file)
    if os.path.exists(p):
        img = bpy.data.images.load(p, check_existing=True)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = img
        co = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, scale)
        nt.links.new(co.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        if normal:
            np_ = os.path.join(TEX, normal)
            if os.path.exists(np_):
                ni = bpy.data.images.load(np_, check_existing=True)
                ntx = nt.nodes.new("ShaderNodeTexImage")
                ntx.image = ni
                ntx.image.colorspace_settings.name = "Non-Color"
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.inputs["Strength"].default_value = 0.7
                nt.links.new(ntx.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


def plain(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


M_WALL = tex_mat("Wall", "wall_warm.png", 2.4, 0.92, normal="wall_normal.png")
M_OAK = tex_mat("FloorOak", "floor_oak.png", 0.55, 0.55, normal="wood_normal.png")
M_STONE = tex_mat("FloorStone", "marble_warm.png", 0.6, 0.3, normal="marble_normal.png")
M_TILE = tex_mat("Tile", "marble_warm.png", 2.0, 0.35)
M_WOOD = tex_mat("Walnut", "wood_walnut.png", 1.1, 0.55, normal="wood_normal.png")
M_WOOD_L = tex_mat("WoodLight", "wood_light.png", 1.2, 0.55, normal="wood_normal.png")
M_LINEN = tex_mat("Linen", "fabric_linen.png", 2.2, 0.95, normal="fabric_normal.png")
M_MARBLE = tex_mat("Marble", "marble_warm.png", 0.7, 0.28)
M_DARK = plain("Dark", (0.09, 0.09, 0.10), 0.5)
M_METAL = plain("Metal", (0.42, 0.44, 0.47), 0.3, 0.85)
M_GLASS = plain("Glass", (0.55, 0.68, 0.75), 0.1)
M_SCREEN = plain("Screen", (0.05, 0.07, 0.10), 0.15)
M_WHITE = plain("White", (0.93, 0.93, 0.91), 0.6)
M_GREEN = plain("Plant", (0.22, 0.42, 0.26), 0.8)
M_SAGE = plain("SageFabric", (0.60, 0.66, 0.58), 0.9)
M_TERRA = plain("Terra", (0.70, 0.46, 0.38), 0.9)
M_GOLD = plain("Gold", (0.78, 0.64, 0.36), 0.3, 0.8)
M_TV = plain("TvGlass", (0.045, 0.055, 0.075), 0.12, 0.55)


def soft(name, w, d, h, x, z, y=0.0, m=None, r=0.06, rz=0.0):
    """软包家具：大倒角 + 3 段圆角"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -z, y + h / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (w, d, h)
    o.rotation_euler[2] = rz
    if m:
        o.data.materials.append(m)
    md = o.modifiers.new("Bevel", "BEVEL")
    md.width = r
    md.segments = 3
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.modifier_apply(modifier=md.name)
    return o


# ---------------------------------------------------------------- 基础几何
def box(name, sx, sy, sz, x, y, z, rz=0.0, m=None, bevel=0.012):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    o = bpy.context.active_object
    o.name = name
    o.scale = (sx, sy, sz)
    o.rotation_euler[2] = rz
    if m:
        o.data.materials.append(m)
    if bevel:
        md = o.modifiers.new("Bevel", "BEVEL")
        md.width = bevel
        md.segments = 2
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=md.name)
    return o


def B(name, w, d, h, x, z, y=0.0, m=None, rz=0.0):
    """w 沿 x，d 沿 z，h 高，x/z 平面位置，y 底面高度"""
    return box(name, w, d, h, x, -z, y + h / 2, rz=rz, m=m)


def cyl(name, r, h, x, z, y=0.0, m=None, seg=24, sz=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=h, location=(x, -z, y + h / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (1, 1, sz)
    if m:
        o.data.materials.append(m)
    return o


def sph(name, r, x, z, y, m=None, s=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=12, radius=r, location=(x, -z, y))
    o = bpy.context.active_object
    o.name = name
    if s:
        o.scale = s
    if m:
        o.data.materials.append(m)
    return o


def wall_z(z, x0, x1, door=None, dw=1.0, h=H):
    segs = [(x0, x1)] if door is None else [(x0, door - dw / 2), (door + dw / 2, x1)]
    for a, b in segs:
        if b - a > 0.05:
            box(f"Wz{int(z*100)}_{int(a*100)}", b - a, WALL, h, (a + b) / 2, -z, h / 2, m=M_WALL, bevel=0)
    if door is not None:
        box(f"Wzl{int(z*100)}_{int(door*100)}", dw, WALL, h - 2.1, door, -z, (h + 2.1) / 2, m=M_WALL, bevel=0)


def wall_x(x, z0, z1, door=None, dw=1.0, h=H):
    segs = [(z0, z1)] if door is None else [(z0, door - dw / 2), (door + dw / 2, z1)]
    for a, b in segs:
        if b - a > 0.05:
            box(f"Wx{int(x*100)}_{int(a*100)}", WALL, b - a, h, x, -(a + b) / 2, h / 2, m=M_WALL, bevel=0)
    if door is not None:
        box(f"Wxl{int(x*100)}_{int(door*100)}", WALL, dw, h - 2.1, x, -door, (h + 2.1) / 2, m=M_WALL, bevel=0)


# ---------------------------------------------------------------- 地面
floors = [
    ("F_hall", 0, 3.0, 0, 3.0, M_OAK),
    ("F_bed2", 3.2, 6.6, 0, 3.0, M_OAK),
    ("F_corridor", 0, 6.6, 3.0, 4.2, M_STONE),
    ("F_mbath", 0, 3.0, 4.2, 6.5, M_TILE),
    ("F_closet", 3.0, 6.6, 4.2, 6.5, M_OAK),
    ("F_master", 0, 6.6, 6.5, 12.5, M_OAK),
    ("F_entry", 6.6, 9.6, 0, 2.5, M_STONE),
    ("F_kitchen", 9.6, 14.0, 0, 2.5, M_TILE),
    ("F_dining", 6.6, 14.0, 2.5, 5.5, M_STONE),
    ("F_living", 6.6, 14.0, 5.5, 12.5, M_STONE),
    ("F_balcony", 6.6, 14.0, 12.5, 15.0, M_TILE),
]
for name, x0, x1, z0, z1, m in floors:
    box(name, x1 - x0, z1 - z0, 0.1, (x0 + x1) / 2, -(z0 + z1) / 2, -0.05, m=m, bevel=0)

# ---------------------------------------------------------------- 外墙
wall_z(0, 0, 14)                                   # 上外墙
wall_x(14, 0, 15)                                  # 右外墙
wall_z(15, 6.6, 14)                                # 阳台外沿
wall_x(6.6, 12.5, 15)
wall_x(14, 12.5, 15)
wall_z(12.5, 6.6, 14, door=10.0, dw=2.6)           # 客厅→阳台推拉门
wall_x(0, 0, 12.5)                                 # 左外墙
wall_z(12.5, 0, 6.6)                               # 主卧外墙
wall_z(2.5, 6.6, 14, door=8.0, dw=1.2)             # 餐厅/厨房之间（开放）
wall_z(0, 0, 14)                                   # 顶部

# ---------------------------------------------------------------- 内墙
# 两间次卧（上部）
wall_z(3.0, 0, 6.6, door=1.6, dw=0.9)              # 走廊北墙（次卧A 门）
wall_x(3.2, 0, 3.0, door=1.6, dw=0.9)              # 次卧A / 次卧B
# 走廊
wall_x(6.6, 0, 4.2, door=2.0, dw=1.0)
wall_z(4.2, 0, 6.6, door=4.6, dw=0.9)              # 走廊南墙（主卫/衣帽间）
wall_x(3.0, 4.2, 6.5, door=5.4, dw=0.8)            # 主卫 / 衣帽间
# 主卧
wall_z(6.5, 0, 6.6, door=1.8, dw=1.0)              # 主卧北墙
wall_x(6.6, 4.2, 6.5, door=5.6, dw=0.9)            # 衣帽间门（→走廊）
# 右侧
wall_x(6.6, 0, 2.5, door=1.8, dw=1.2)              # 玄关 / 客厅
wall_x(9.6, 0, 2.5, door=1.4, dw=0.9)              # 玄关 / 厨房
wall_z(2.5, 9.6, 14, door=11.2, dw=1.0)            # 厨房 / 餐厅
wall_z(5.5, 6.6, 14, door=9.6, dw=1.6)             # 餐厅 / 客厅（开放门洞）
# 阳台
wall_x(6.6, 12.5, 15, door=13.6, dw=1.0)
wall_x(14, 12.5, 15)

# ---------------------------------------------------------------- 家具
# 次卧 A
B("BedA", 1.8, 2.05, 0.42, 1.5, 2.0, 0, M_LINEN)
B("BedAHead", 1.9, 0.12, 0.9, 1.5, 1.05, 0, M_WOOD)
B("NightA", 0.45, 0.4, 0.5, 2.6, 1.1, 0, M_WOOD)
B("WardA", 0.6, 1.8, 2.3, 0.4, 1.3, 0, M_WOOD)
B("RugA", 2.0, 1.4, 0.02, 1.6, 2.3, 0, M_SAGE)

# 次卧 B
B("BedB", 1.8, 2.05, 0.42, 4.9, 2.0, 0, M_LINEN)
B("BedBHead", 1.9, 0.12, 0.9, 4.9, 1.05, 0, M_WOOD)
B("WardB", 0.6, 1.8, 2.3, 6.25, 1.3, 0, M_WOOD)
B("DeskB", 1.2, 0.6, 0.75, 4.9, 0.5, 0, M_WOOD)
B("ChairB", 0.45, 0.45, 0.45, 4.9, 0.95, 0, M_DARK)

# 主卫
B("Tub", 1.4, 0.75, 0.55, 0.8, 5.9, 0, M_WHITE)
B("VanityM", 1.7, 0.5, 0.85, 1.9, 4.5, 0, M_WOOD)
B("VanityTop", 1.8, 0.55, 0.05, 1.9, 4.5, 0.85, M_MARBLE)
B("MirrorM", 1.5, 0.04, 1.1, 1.9, 4.28, 1.0, M_GLASS)
B("ToiletM", 0.4, 0.6, 0.42, 0.55, 4.6, 0, M_WHITE)

# 衣帽间
B("ClWard1", 3.2, 0.55, 2.3, 4.8, 4.45, 0, M_WOOD)
B("ClWard2", 0.55, 1.6, 2.3, 3.25, 5.5, 0, M_WOOD)
B("ClIsland", 1.2, 0.8, 0.85, 5.0, 5.6, 0, M_WOOD_L)
B("ClIslandTop", 1.3, 0.9, 0.05, 5.0, 5.6, 0.85, M_MARBLE)

# 主卧
B("BedM", 2.2, 2.3, 0.45, 3.0, 10.4, 0, M_LINEN)
B("BedMHead", 2.3, 0.14, 1.05, 3.0, 9.15, 0, M_WOOD)
B("NightM1", 0.5, 0.45, 0.55, 1.55, 9.4, 0, M_WOOD)
B("NightM2", 0.5, 0.45, 0.55, 4.45, 9.4, 0, M_WOOD)
B("RugM", 3.0, 2.4, 0.02, 3.0, 11.4, 0, M_SAGE)
B("DresserM", 0.5, 1.4, 0.8, 5.9, 11.6, 0, M_WOOD_L)
B("MirrorD", 0.04, 1.0, 1.0, 6.15, 11.6, 1.2, M_GLASS)
B("SofaM", 1.6, 0.7, 0.45, 1.2, 11.8, 0, M_LINEN)

# 玄关
B("ShoeCab", 1.6, 0.4, 1.1, 8.0, 0.25, 0, M_WOOD)
B("EntryMirror", 0.8, 0.04, 1.3, 8.9, 0.2, 0.8, M_GLASS)
B("EntryBench", 1.2, 0.4, 0.45, 8.0, 2.2, 0, M_WOOD_L)

# 厨房
B("Counter1", 4.2, 0.65, 0.9, 11.7, 0.45, 0, M_WOOD)
B("Counter1Top", 4.3, 0.7, 0.05, 11.7, 0.45, 0.9, M_MARBLE)
B("Counter2", 0.65, 2.0, 0.9, 13.6, 1.6, 0, M_WOOD)
B("Counter2Top", 0.7, 2.1, 0.05, 13.6, 1.6, 0.9, M_MARBLE)
B("CabUpper", 4.2, 0.35, 0.7, 11.7, 0.22, 1.8, M_WOOD)
B("Stove", 0.7, 0.5, 0.04, 10.6, 0.45, 0.94, M_DARK)
cyl("SinkK", 0.24, 0.05, 12.6, 0.45, 0.9, m=M_METAL, seg=20)
B("Fridge", 0.75, 0.72, 1.95, 13.6, 0.55, 0, M_WHITE)

# 餐厅
B("DiningT", 2.2, 1.05, 0.75, 10.2, 4.0, 0, M_WOOD)
for i, (dx, dz) in enumerate([(-0.7, -0.8), (0, -0.8), (0.7, -0.8), (-0.7, 0.8), (0, 0.8), (0.7, 0.8)]):
    B(f"ChD{i}", 0.44, 0.44, 0.46, 10.2 + dx, 4.0 + dz, 0, M_WOOD_L)
B("Sideboard", 2.0, 0.42, 0.85, 12.6, 2.9, 0, M_WOOD)
B("DiningPendant", 0.9, 0.5, 0.08, 10.2, 4.0, 2.1, M_GOLD)

# 客厅
soft("SofaBase", 3.2, 1.05, 0.26, 10.6, 10.2, 0.06, M_LINEN, 0.05)
soft("SofaSeatL", 1.42, 0.92, 0.2, 9.88, 10.15, 0.3, M_LINEN, 0.08)
soft("SofaSeatR", 1.42, 0.92, 0.2, 11.32, 10.15, 0.3, M_LINEN, 0.08)
soft("SofaBack", 3.2, 0.3, 0.62, 10.6, 10.78, 0.28, M_LINEN, 0.07)
soft("SofaBackCush1", 1.35, 0.22, 0.5, 9.9, 10.62, 0.42, M_LINEN, 0.09)
soft("SofaBackCush2", 1.35, 0.22, 0.5, 11.3, 10.62, 0.42, M_LINEN, 0.09)
soft("SofaArmL", 0.26, 1.0, 0.52, 8.86, 10.2, 0.16, M_LINEN, 0.09)
soft("SofaArmR", 0.26, 1.0, 0.52, 12.34, 10.2, 0.16, M_LINEN, 0.09)
for sx in (9.25, 11.95):
    for sz in (9.85, 10.55):
        cyl("SofaLegX", 0.04, 0.08, sx, sz, 0, m=M_DARK, seg=10)
soft("PillowA", 0.42, 0.16, 0.36, 9.75, 10.52, 0.44, M_TERRA, 0.07, rz=0.2)
soft("PillowB", 0.42, 0.16, 0.36, 11.45, 10.52, 0.44, M_SAGE, 0.07, rz=-0.15)
B("RugL", 4.2, 3.0, 0.02, 10.6, 10.9, 0, M_SAGE)
B("CoffeeT", 1.6, 0.8, 0.42, 10.6, 11.2, 0, M_WOOD)
B("TvCab", 3.0, 0.45, 0.45, 10.6, 9.1, 0, M_WOOD)
B("Tv", 2.5, 0.07, 1.4, 10.6, 8.95, 0.75, M_TV)
B("TvStand", 0.35, 0.2, 0.06, 10.6, 8.99, 0.72, M_METAL)
B("ShelfL", 0.4, 3.4, 2.1, 6.9, 9.6, 0, M_WOOD)
B("PlantL", 0.5, 0.5, 0.5, 13.5, 8.4, 0, M_WOOD_L)
sph("PlantLTop", 0.5, 13.5, 8.4, 1.0, M_GREEN)
B("FloorLamp", 0.35, 0.35, 0.05, 12.9, 11.9, 0, M_DARK)
cyl("FloorLampPole", 0.03, 1.6, 12.9, 11.9, 0.1, m=M_METAL, seg=10)
cyl("FloorLampShade", 0.26, 0.3, 12.9, 11.9, 1.7, m=M_LINEN, seg=18)

# 阳台

B("OutTable", 1.2, 0.8, 0.72, 9.0, 13.6, 0, M_WOOD)
for i, (dx, dz) in enumerate([(-0.9, 0), (0.9, 0), (0, -0.7), (0, 0.7)]):
    B(f"OutChair{i}", 0.45, 0.45, 0.42, 9.0 + dx, 13.6 + dz, 0, M_SAGE)
B("OutSofa", 2.0, 0.8, 0.4, 12.4, 14.2, 0, M_SAGE)
for i, (px, pz) in enumerate([(7.0, 12.9), (13.6, 12.9), (13.6, 14.6)]):
    cyl(f"Pot{i}", 0.24, 0.42, px, pz, 0.2, m=M_WOOD_L)
    sph(f"Plant{i}", 0.34, px, pz, 0.66, M_GREEN)
B("Rail", 7.4, 0.06, 1.05, 10.3, 15.0, 0, M_GLASS)

# 吊灯已按要求去掉（照明由网页光源负责）


# ---------------------------------------------------------------- 补充家具
# ===== 客厅 =====
soft("AccentChair1", 0.78, 0.78, 0.4, 8.30, 9.40, 0.12, M_TERRA, 0.09, rz=0.5)
soft("AccentChair1Back", 0.78, 0.2, 0.6, 8.55, 9.12, 0.32, M_TERRA, 0.09, rz=0.5)
soft("AccentChair2", 0.78, 0.78, 0.4, 12.70, 11.20, 0.12, M_SAGE, 0.09, rz=-0.4)
soft("AccentChair2Back", 0.78, 0.2, 0.6, 12.55, 10.95, 0.32, M_SAGE, 0.09, rz=-0.4)
B("SideTable1", 0.45, 0.45, 0.5, 7.90, 10.30, 0, M_WOOD)
B("SideTable2", 0.45, 0.45, 0.5, 13.10, 10.40, 0, M_WOOD)
B("Art1", 1.6, 0.04, 0.9, 10.60, 5.62, 1.5, M_TERRA)
B("Art2", 1.2, 0.04, 0.8, 7.00, 8.20, 1.5, M_SAGE)
B("WallClockL", 0.34, 0.05, 0.34, 13.90, 8.00, 2.0, M_WHITE)
B("PlantCorner", 0.55, 0.55, 0.5, 6.95, 12.10, 0, M_WOOD_L)
sph("PlantCornerTop", 0.55, 6.95, 12.10, 1.05, M_GREEN)

# ===== 主卧 =====
B("BedBench", 1.8, 0.5, 0.45, 3.00, 11.85, 0, M_TERRA)
B("ArmchairM", 0.85, 0.85, 0.45, 5.60, 9.30, 0, M_SAGE, rz=-0.6)
B("SideTableM", 0.4, 0.4, 0.5, 5.30, 10.30, 0, M_WOOD)
B("ArtM", 1.4, 0.04, 0.9, 3.00, 6.56, 1.5, M_GOLD)
B("NightLampM1", 0.2, 0.2, 0.45, 1.70, 9.40, 0.55, M_GOLD)
B("NightLampM2", 0.2, 0.2, 0.45, 4.30, 9.40, 0.55, M_GOLD)

# ===== 餐厅 =====
B("WineCab", 0.5, 2.0, 2.0, 13.65, 4.40, 0, M_WOOD)
B("DiningRug", 3.2, 2.2, 0.02, 10.20, 4.00, 0, M_LINEN)
B("ArtD", 1.6, 0.04, 0.9, 10.20, 5.44, 1.5, M_TERRA)

# ===== 次卧 A =====
B("DeskA", 1.2, 0.6, 0.75, 2.30, 0.50, 0, M_WOOD)
B("ChairA", 0.45, 0.45, 0.45, 2.30, 0.95, 0, M_DARK)
B("ShelfA", 1.0, 0.3, 1.8, 0.30, 2.40, 0, M_WOOD)

# ===== 次卧 B =====
B("ShelfB", 1.0, 0.3, 1.8, 6.30, 2.40, 0, M_WOOD)

# ===== 主卫 =====
B("ShowerM", 1.2, 1.2, 0.06, 2.30, 6.10, 0, M_TILE)
B("ShowerGlassM", 1.2, 0.04, 2.0, 2.30, 5.52, 0, M_GLASS)
B("TowelRack", 0.9, 0.1, 0.08, 1.00, 6.40, 1.5, M_METAL)

# ===== 衣帽间 =====
B("ClosetMirrorBig", 1.4, 0.04, 1.8, 5.40, 4.26, 0.5, M_GLASS)
B("ClosetRug", 2.2, 1.4, 0.02, 4.80, 5.90, 0, M_LINEN)

# ===== 阳台 =====
B("BalconyPlant1", 0.45, 0.45, 0.42, 7.00, 14.60, 0, M_WOOD_L)
sph("BalconyPlantTop1", 0.42, 7.00, 14.60, 0.85, M_GREEN)
B("BalconyMat", 2.2, 1.2, 0.02, 9.00, 13.60, 0, M_LINEN)


# ===== 主卧补充 =====
soft("BedMQuilt", 2.1, 2.0, 0.16, 3.00, 10.55, 0.46, M_SAGE, 0.07)
soft("BedMFold", 2.1, 0.5, 0.18, 3.00, 9.53, 0.48, M_LINEN, 0.06)
soft("MasterArmchair", 0.86, 0.86, 0.42, 5.55, 9.25, 0.12, M_TERRA, 0.1, rz=-0.6)
soft("MasterArmBack", 0.86, 0.2, 0.6, 5.78, 9.05, 0.36, M_TERRA, 0.1, rz=-0.6)
B("MasterSideT", 0.42, 0.42, 0.5, 5.15, 10.35, 0, M_WOOD)
cyl("MasterLampPole", 0.03, 1.55, 5.95, 12.15, 0.05, m=M_METAL, seg=10)
cyl("MasterLampShade", 0.24, 0.3, 5.95, 12.15, 1.6, m=M_LINEN, seg=18)
B("MasterDresser", 1.2, 0.45, 0.8, 0.75, 12.15, 0, M_WOOD_L)
B("MasterDresserTop", 1.3, 0.5, 0.05, 0.75, 12.15, 0.8, M_MARBLE)
B("MasterDresserMirror", 1.1, 0.05, 0.9, 0.75, 12.36, 1.1, M_GLASS)
soft("MasterRugExt", 3.6, 2.6, 0.02, 3.00, 10.90, 0, M_LINEN, 0.02)
B("MasterPlant", 0.45, 0.45, 0.42, 6.15, 10.65, 0, M_WOOD_L)
sph("MasterPlantTop", 0.45, 6.15, 10.65, 0.82, M_GREEN)

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
