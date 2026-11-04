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


# ---------------------------------------------------------------- 贴图材质
TEX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")


def tex_mat(name, file, scale=1.0, rough=0.6, metal=0.0, tint=(1, 1, 1), normal=None, rough_map=True):
    """带贴图 + 法线 + 粗糙度的材质"""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal

    path = os.path.join(TEX_DIR, file)
    if os.path.exists(path):
        img = bpy.data.images.load(path, check_existing=True)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        tex.location = (-520, 260)
        mapping = nt.nodes.new("ShaderNodeMapping")
        mapping.inputs["Scale"].default_value = (scale, scale, scale)
        coord = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        # 粗糙度贴图：用同一张图的灰度
        if rough_map:
            rgb2bw = nt.nodes.new("ShaderNodeRGBToBW")
            nt.links.new(tex.outputs["Color"], rgb2bw.inputs["Color"])
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].color = (rough * 0.7, rough * 0.7, rough * 0.7, 1)
            ramp.color_ramp.elements[1].color = (min(1, rough * 1.35),) * 3 + (1,)
            nt.links.new(rgb2bw.outputs["Val"], ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
        if normal:
            npath = os.path.join(TEX_DIR, normal)
            if os.path.exists(npath):
                nimg = bpy.data.images.load(npath, check_existing=True)
                ntex = nt.nodes.new("ShaderNodeTexImage")
                ntex.image = nimg
                ntex.image.colorspace_settings.name = "Non-Color"
                ntex.location = (-520, -120)
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.inputs["Strength"].default_value = 0.85
                nm.location = (-260, -120)
                nt.links.new(ntex.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        bsdf.inputs["Base Color"].default_value = (*tint, 1)
    return m


M_TEX_WOOD = tex_mat("TexWood", "wood.png", 0.5, 0.45)
M_TEX_WOOD_L = tex_mat("TexWoodLight", "wood_light.png", 0.9, 0.45)
M_TEX_FABRIC = tex_mat("TexFabric", "fabric.png", 2.5, 0.95)
M_TEX_MARBLE = tex_mat("TexMarble", "marble.png", 0.6, 0.25)
M_TEX_WALL = tex_mat("TexWall", "wall.png", 3.0, 0.9)
M_TEX_RUG = tex_mat("TexRug", "rug.png", 4.0, 0.98)


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


M_WALL = tex_mat("Wall", "wall.png", 3.0, 0.9, normal="wall_normal.png")
M_FLOOR = tex_mat("Floor", "marble.png", 0.6, 0.28, normal="marble_normal.png")
M_CEIL = mat("Ceil", (0.95, 0.95, 0.94), 0.9)
M_WOOD = tex_mat("Wood", "wood.png", 1.0, 0.48, normal="wood_normal.png")
M_WOOD_L = tex_mat("WoodLight", "wood_light.png", 1.2, 0.5, normal="wood_normal.png")
M_FABRIC = tex_mat("Fabric", "fabric.png", 2.5, 0.95, normal="fabric_normal.png")
M_LINEN = tex_mat("Linen", "fabric.png", 3.0, 0.92, normal="fabric_normal.png")
M_DARK = mat("Dark", (0.10, 0.10, 0.11), 0.5)
M_METAL = mat("Metal", (0.45, 0.47, 0.50), 0.3, 0.8)
M_SCREEN = mat("Screen", (0.06, 0.09, 0.12), 0.15)
M_GREEN = mat("Plant", (0.18, 0.45, 0.26), 0.7)
M_CAT = mat("CatFur", (0.85, 0.82, 0.76), 0.85)
M_RUG = tex_mat("Rug", "rug.png", 3.0, 0.98, normal="fabric_normal.png")
M_GLASS = mat("Glass", (0.35, 0.62, 0.80), 0.1, 0.0, 0.35)
M_CITY = tex_mat("CityNight", "city_night.png", 1.0, 0.9)

# 分房间配色
M_WALL_WARM = mat("WallWarm", (0.94, 0.90, 0.84), 0.88)
M_WALL_SAGE = mat("WallSage", (0.80, 0.85, 0.80), 0.88)
M_WALL_SLATE = mat("WallSlate", (0.26, 0.30, 0.36), 0.85)
M_WALL_TERRA = mat("WallTerra", (0.82, 0.70, 0.60), 0.88)
M_FLOOR_WOOD = tex_mat("FloorWood", "wood.png", 0.35, 0.42, normal="wood_normal.png")
M_FLOOR_TILE = mat("FloorTile", (0.88, 0.88, 0.89), 0.35)
M_FLOOR_CAT = mat("FloorCat", (0.78, 0.80, 0.76), 0.5)
M_GOLD = mat("Gold", (0.80, 0.66, 0.36), 0.3, 0.85)
M_EMIT = mat("Emissive", (1.0, 0.95, 0.85), 0.4)
M_SAGE_FAB = mat("SageFabric", (0.62, 0.70, 0.62), 0.9)
M_TERRA_FAB = mat("TerraFabric", (0.72, 0.48, 0.38), 0.9)



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
# 分房间地板（不同材质）
box("FloorLiving", 7.0, 7.0, 0.1, 2.5, -2.5, -0.05, m=M_FLOOR_TILE, bevel=0)   # 客厅
box("FloorBed", 5.0, 5.0, 0.1, -3.5, -3.5, -0.05, m=M_FLOOR_WOOD, bevel=0)      # 主卧
box("FloorGame", 5.0, 4.0, 0.1, -3.5, 3.0, -0.05, m=M_FLOOR_WOOD, bevel=0)      # 电竞房
box("FloorCat", 5.0, 5.0, 0.1, 3.5, 3.5, -0.05, m=M_FLOOR_CAT, bevel=0)         # 猫房
box("FloorHall", 2.0, 5.0, 0.1, 0.0, 3.5, -0.05, m=M_FLOOR_WOOD, bevel=0)       # 玄关
# 天花板不导出（俯视看不到室内）

# 外墙
box("WallN", R * 2, WALL, H, 0, R, H / 2, m=M_WALL, bevel=0)      # z=+6 → y=-6 不对，见下
# 注意：网页 z=+6 对应 Blender y=-6；这里逐个写清楚
bpy.data.objects.remove(bpy.data.objects["WallN"], do_unlink=True)


def wall_x(name, x, z0, z1, door=None, door_w=1.0, m=M_WALL):
    """沿 z 方向的墙（Blender y 方向），带门洞和过梁"""
    y0, y1 = -z1, -z0
    segs = [(y0, y1)] if door is None else [
        (y0, -door - door_w / 2), (-door + door_w / 2, y1)]
    i = 0
    for a, b in segs:
        if b - a < 0.05:
            continue
        box(f"{name}_{i}", WALL, b - a, H, x, (a + b) / 2, H / 2, m=m, bevel=0)
        i += 1
    if door is not None:
        box(f"{name}_lintel", WALL, door_w, H - 2.1, x, -door, (H + 2.1) / 2, m=M_WALL, bevel=0)


def wall_z(name, z, x0, x1, door=None, door_w=1.0, m=M_WALL):
    """沿 x 方向的墙"""
    y = -z
    segs = [(x0, x1)] if door is None else [
        (x0, door - door_w / 2), (door + door_w / 2, x1)]
    i = 0
    for a, b in segs:
        if b - a < 0.05:
            continue
        box(f"{name}_{i}", b - a, WALL, H, (a + b) / 2, y, H / 2, m=m, bevel=0)
        i += 1
    if door is not None:
        box(f"{name}_lintel", door_w, WALL, H - 2.1, door, y, (H + 2.1) / 2, m=M_WALL, bevel=0)


# 外墙
wall_z("OuterS", -R, -R, R)
wall_z("OuterN", R, -R, R, door=2.5, door_w=3.0)
wall_x("OuterW", -R, -R, R)
wall_x("OuterE", R, -R, R)

# 隔断（与网页一致）
wall_z("BedLiving", 1, -R, -1, door=-3.5, m=M_WALL_WARM)      # 主卧 ↔ 客厅
wall_x("LeftHall", -1, -5, 1, door=-3, m=M_WALL_SAGE)          # 电竞房 ↔ 玄关
wall_x("CatHall", 1, -R, -1, door=-3.5, m=M_WALL_SAGE)         # 猫房 ↔ 玄关
wall_z("CatLiving", -3, 1, R, door=3.6, m=M_WALL_WARM)
# 衣帽间：卧室内 2×2（x -3..-1，z 1..3），门在 z=3
wall_x("ClosetW", -3.0, 1, 3, None, 0, m=M_WALL_WARM)
wall_z("ClosetN", 3.0, -3, -1, door=-2.1, door_w=0.8, m=M_WALL_WARM)

# 踢脚线
for (x, z, w, d) in [(0, -R + 0.07, R * 2, 0.02), (0, R - 0.07, R * 2, 0.02),
                     (-R + 0.07, 0, 0.02, R * 2), (R - 0.07, 0, 0.02, R * 2)]:
    box("Baseboard", w, d, 0.1, x, -z, 0.05, m=M_WALL, bevel=0)

# 主卧窗户（西墙 x=-6，z=4.6）
win_x, win_z = -R + 0.02, 4.6
box("WinFrame", 0.06, 2.2, 1.6, win_x, -win_z, 1.62, m=M_WALL, bevel=0)
box("WinGlass", 0.02, 2.0, 1.4, win_x + 0.04, -win_z, 1.62, m=M_CITY, bevel=0)


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
box("SofaBack", 1.9, 0.22, 0.66, sx, sy + 0.4, 0.55, m=M_FABRIC)
box("SofaArmL", 0.22, 0.95, 0.5, sx - 0.95, sy, 0.4, m=M_FABRIC)
box("SofaArmR", 0.22, 0.95, 0.5, sx + 0.95, sy, 0.4, m=M_FABRIC)
box("SofaCushion", 1.7, 0.8, 0.14, sx, sy + 0.02, 0.42, m=M_LINEN)
for dx in (-0.45, 0.45):
    box("SofaPillow", 0.42, 0.16, 0.34, sx + dx, sy + 0.28, 0.58, rz=0.1, m=M_LINEN)

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
box("KitchenCounter", 0.62, 2.6, 0.88, 5.6, -1.6, 0.44, m=M_WOOD)
box("KitchenTop", 0.68, 2.66, 0.05, 5.6, -1.6, 0.9, m=M_WOOD_L, bevel=0)
box("KitchenSink", 0.5, 0.5, 0.04, 5.55, -1.2, 0.92, m=M_METAL, bevel=0)
box("KitchenCabinet", 0.6, 2.6, 0.7, 5.62, -1.6, 1.75, m=M_FABRIC)

# 书架（东墙）
box("ShelfBody", 0.34, 1.5, 1.9, -0.78, -4.6, 0.95, m=M_WOOD)
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
bx, by = J(-4.20, 4.55)
box("BedFrame", 2.1, 1.6, 0.3, bx, by, 0.15, m=M_DARK)
box("BedMattress", 2.0, 1.5, 0.24, bx, by, 0.42, m=M_FABRIC)
box("BedSheet", 1.95, 1.45, 0.1, bx, by, 0.56, m=M_LINEN)
box("BedHead", 2.12, 0.12, 0.9, bx, by + 0.8, 0.62, m=M_WOOD)
box("BedPillow1", 0.6, 0.34, 0.14, bx - 0.5, by + 0.5, 0.64, rz=0.05, m=M_FABRIC)
box("BedPillow2", 0.6, 0.34, 0.14, bx + 0.05, by + 0.5, 0.64, m=M_FABRIC)

for nx in (-5.55, -2.85):
    box("Nightstand", 0.45, 0.42, 0.5, nx, -4.55, 0.25, m=M_WOOD)
    box("NsTop", 0.48, 0.45, 0.04, nx, -4.55, 0.52, m=M_WOOD_L, bevel=0)

# 衣柜（西墙 x=-5.62，z=2.4）
box("Wardrobe", 0.6, 2.6, 2.3, -5.62, -1.9, 1.15, m=M_WOOD)
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


# ---------------------------------------------------------------- 精致化细节
# 门套（四处门洞）
def door_casing(x, z, along="z", w=1.0):
    if along == "z":
        for dz in (-w / 2 - 0.05, w / 2 + 0.05):
            box("Casing", WALL + 0.06, 0.1, 2.15, x, -z + dz, 1.06, m=M_WOOD_L, bevel=0)
        box("CasingTop", WALL + 0.06, w + 0.2, 0.12, x, -z, 2.16, m=M_WOOD_L, bevel=0)
    else:
        for dx in (-w / 2 - 0.05, w / 2 + 0.05):
            box("Casing", 0.1, WALL + 0.06, 2.15, x + dx, -z, 1.06, m=M_WOOD_L, bevel=0)
        box("CasingTop", w + 0.2, WALL + 0.06, 0.12, x, -z, 2.16, m=M_WOOD_L, bevel=0)


door_casing(-3.5, 1, "x", 1.0)     # 主卧门（墙沿 X）
door_casing(-1, -3, "z", 1.0)      # 电竞房门（墙沿 Z）
door_casing(1, -4.5, "z", 0.9)     # 猫房门（墙沿 Z）
door_casing(3.6, -3, "x", 1.0)     # 猫房→客厅
door_casing(0.2, -3.5, "x", 0.8)   # 卫生间门
door_casing(-2.1, 3, "x", 0.8)     # 衣帽间门

# 背景墙
box("FeatureTvWall", 3.6, 0.06, 2.2, 2.4, -5.92, 1.12, m=M_WALL_TERRA, bevel=0)
box("FeatureBedWall", 3.2, 0.06, 2.2, -4.0, -5.92, 1.12, m=M_WALL_WARM, bevel=0)
box("FeatureGameWall", 3.4, 0.06, 2.2, -3.5, 5.92, 1.12, m=M_WALL_SLATE, bevel=0)

# 窗帘（主卧）
for dz in (-0.95, 0.95):
    box("Curtain", 0.08, 0.55, 2.3, -5.75, -(4.6 + dz), 1.15, m=M_SAGE_FAB, bevel=0)
box("CurtainRod", 0.05, 2.4, 0.05, -5.75, -4.6, 2.35, m=M_METAL, bevel=0)

# 吊灯（四个房间）
def pendant(name, x, z, y=2.3):
    cyl(f"{name}_rod", 0.012, 0.5, x, -z, y + 0.25, m=M_METAL, seg=8)
    cyl(f"{name}_shade", 0.26, 0.18, x, -z, y, m=M_GOLD, seg=20)
    sph(f"{name}_bulb", 0.09, x, -z, y - 0.08, m=M_EMIT)


pendant("PendantLiving", 2.4, 2.4)
pendant("PendantBed", -3.6, 3.4)
pendant("PendantGame", -3.5, -3.0)
pendant("PendantCat", 3.5, -3.5)

# 客厅装饰：抱枕、书、绿植小盆栽
box("PillowAccent", 0.36, 0.14, 0.3, 2.0, -3.9, 0.56, rz=0.3, m=M_TERRA_FAB)
box("Book1", 0.26, 0.18, 0.04, 2.3, -4.3, 0.46, rz=0.2, m=M_TERRA_FAB, bevel=0)
box("Book2", 0.24, 0.17, 0.035, 2.34, -4.29, 0.5, rz=0.35, m=M_LINEN, bevel=0)
cyl("SmallPot", 0.09, 0.16, 2.85, -4.3, 0.5, m=M_WOOD_L)
sph("SmallPlant", 0.11, 2.85, -4.3, 0.63, m=M_GREEN)

# 主卧装饰：床尾毯、闹钟、小夜灯、拖鞋
box("BedThrow", 1.9, 0.55, 0.05, -4.0, -3.95, 0.63, m=M_TERRA_FAB, bevel=0)
box("Clock", 0.14, 0.1, 0.12, -2.45, -4.75, 0.6, m=M_DARK, bevel=0.01)
cyl("NightLampBase", 0.07, 0.06, -5.55, -4.75, 0.57, m=M_GOLD)
sph("NightLampBulb", 0.07, -5.55, -4.75, 0.64, m=M_EMIT)
box("Slippers", 0.34, 0.16, 0.05, -4.9, -3.7, 0.03, m=M_FABRIC, bevel=0.01)

# 电竞房装饰：桌垫、RGB 灯带、耳机
box("DeskMat", 0.8, 0.34, 0.01, -3.5, -4.62, 0.795, m=M_WALL_SLATE, bevel=0)
box("RgbStrip", 1.9, 0.03, 0.02, -3.5, -4.92, 0.72, m=M_EMIT, bevel=0)
box("Headset", 0.14, 0.1, 0.14, -3.9, -4.55, 0.88, m=M_DARK, bevel=0.01)

# 猫房装饰：墙面猫跳台、玩具球
for i, (cx, cz, ch) in enumerate([(1.2, -4.4, 1.2), (2.0, -4.4, 1.6), (2.8, -4.4, 1.35)]):
    box(f"CatShelf{i}", 0.5, 0.26, 0.06, cx, -cz, ch, m=M_WOOD_L, bevel=0)
sph("CatToy", 0.07, 3.0, -2.9, 0.08, m=M_TERRA_FAB)
box("CatCushion", 0.6, 0.4, 0.08, 4.6, -2.6, 0.18, m=M_SAGE_FAB, bevel=0.02)

# 玄关装饰：挂画、换鞋凳、地垫
box("HallArt", 0.7, 0.04, 0.9, 0.0, 5.94, 1.6, m=M_WALL_TERRA, bevel=0)
box("ShoeBench", 0.9, 0.32, 0.42, -0.6, 5.5, 0.21, m=M_WOOD, bevel=0.01)
box("Doormat", 1.0, 0.6, 0.02, 0.0, 5.2, 0.01, m=M_TERRA_FAB, bevel=0)


# ---------------------------------------------------------------- 精致化细节 2
# 沙发腿 + 坐垫分色
for dx in (-0.82, 0.82):
    for dy in (-0.38, 0.38):
        box("SofaLeg", 0.07, 0.07, 0.14, 2.4 + dx, -3.6 + dy, 0.07, m=M_DARK, bevel=0.005)
box("SofaSeatL", 0.82, 0.78, 0.14, 1.95, -3.58, 0.44, m=M_SAGE_FAB, bevel=0.02)
box("SofaSeatR", 0.82, 0.78, 0.14, 2.85, -3.58, 0.44, m=M_SAGE_FAB, bevel=0.02)
box("SofaThrow", 0.5, 0.5, 0.06, 2.9, -3.5, 0.53, rz=0.2, m=M_TERRA_FAB, bevel=0.01)

# 电视音响 + 机顶盒
box("Soundbar", 1.2, 0.1, 0.08, 2.4, -5.62, 0.5, m=M_DARK, bevel=0.01)
box("TvBox", 0.3, 0.18, 0.06, 2.95, -5.6, 0.47, m=M_DARK, bevel=0.005)

# 床头软包 + 被子分色
box("BedHeadSoft", 1.9, 0.08, 0.7, -4.0, 4.62, 0.75, m=M_WALL_WARM, bevel=0.03)
box("BedDuvet", 1.9, 1.1, 0.12, -4.0, -4.15, 0.63, m=M_SAGE_FAB, bevel=0.03)
box("BedDuvetFold", 1.9, 0.3, 0.14, -4.0, -4.55, 0.66, m=M_LINEN, bevel=0.02)

# 墙面挂画（客厅、主卧、电竞房）
def art(name, x, y, z, w=0.7, h=0.5, rot=0, m=M_TERRA_FAB):
    box(name, w, 0.04, h, x, y, z, rz=rot, m=M_WOOD_L, bevel=0.01)
    box(name + "_canvas", w * 0.86, 0.02, h * 0.82, x, y + 0.03, z, rz=rot, m=m, bevel=0)


art("ArtLiving", 4.6, -5.9, 1.6, 0.8, 0.55, 0, M_WALL_TERRA)
art("ArtLiving2", 0.9, -5.9, 1.7, 0.55, 0.45, 0, M_SAGE_FAB)
art("ArtBed", -2.6, -1.08, 1.55, 0.6, 0.45, math.pi / 2, M_GOLD)
art("ArtGame", -5.9, 3.2, 1.7, 0.6, 0.5, math.pi / 2, M_WALL_TERRA)

# 猫房墙面跳台垫 + 猫抓柱
box("CatScratchPost", 0.16, 0.16, 0.9, 4.2, 4.6, 0.45, m=M_CAT, bevel=0.02)
box("CatScratchBase", 0.5, 0.5, 0.06, 4.2, 4.6, 0.03, m=M_WOOD_L, bevel=0.01)

# 餐厅吊灯
cyl("DiningPendant", 0.22, 0.16, 4.7, 1.3, 2.0, m=M_GOLD, seg=18)
cyl("DiningPendantRod", 0.01, 0.6, 4.7, 1.3, 2.35, m=M_METAL, seg=8)
sph("DiningBulb", 0.08, 4.7, 1.3, 1.9, m=M_EMIT)

# 客厅地毯边缘压条（视觉分隔）
box("RugTrim", 2.9, 0.04, 0.02, 2.4, -5.85, 0.02, m=M_WOOD, bevel=0)


# ---------------------------------------------------------------- 卫生间 + 家电
# 卫生间隔墙（玄关 z=-3.4，门在 x=0.3）
wall_z("BathWall", -3.4, -1, 1, door=0.3, door_w=0.8, m=M_WALL_WARM)

# 浴缸
box("BathTub", 1.5, 0.7, 0.5, 0.0, 5.1, 0.25, m=M_FABRIC, bevel=0.04)
box("BathInner", 1.28, 0.5, 0.34, 0.0, 5.1, 0.36, m=M_GLASS, bevel=0.03)
box("BathTaps", 0.1, 0.1, 0.16, 0.62, 5.1, 0.58, m=M_METAL, bevel=0.01)

# 洗手台 + 镜子
box("VanityBody", 0.8, 0.42, 0.8, 0.55, 3.75, 0.4, m=M_WOOD_L)
box("VanityTop", 0.84, 0.45, 0.05, 0.55, 3.75, 0.82, m=M_TEX_MARBLE, bevel=0)
cyl("Basin", 0.16, 0.1, 0.55, 3.75, 0.87, m=M_FABRIC, seg=20)
cyl("BathMirror", 0.32, 0.02, 0.55, 3.38, 1.5, rz=math.pi / 2, m=M_GLASS)
cyl("BathMirrorRing", 0.35, 0.03, 0.57, 3.38, 1.5, rz=math.pi / 2, m=M_METAL)

# 马桶
box("ToiletBase", 0.36, 0.5, 0.4, -0.6, 5.0, 0.2, m=M_FABRIC, bevel=0.05)
box("ToiletTank", 0.36, 0.18, 0.36, -0.6, 5.24, 0.56, m=M_FABRIC, bevel=0.03)
box("ToiletSeat", 0.36, 0.4, 0.06, -0.6, 4.96, 0.42, m=M_FABRIC, bevel=0.02)

# 玄关鞋柜挪到卫生间外
box("ShoeCabinet2", 1.2, 0.36, 0.9, 0, 2.2, 0.45, m=M_WOOD)
box("ShoeTop2", 1.2, 0.38, 0.04, 0, 2.2, 0.92, m=M_WOOD_L, bevel=0)

# 冰箱（厨房北端）
box("Fridge", 0.72, 0.68, 1.9, 5.62, -0.3, 0.95, m=M_FABRIC, bevel=0.03)
box("FridgeDoor", 0.02, 0.66, 1.86, 5.25, -0.3, 0.95, m=M_FABRIC, bevel=0.01)
box("FridgeHandle", 0.05, 0.05, 0.5, 5.22, -0.05, 1.15, m=M_METAL, bevel=0.01)

# 微波炉 + 咖啡机（台面上）
box("Microwave", 0.5, 0.36, 0.3, 5.6, -2.6, 1.12, m=M_DARK, bevel=0.02)
box("MicrowaveDoor", 0.02, 0.3, 0.24, 5.34, -2.6, 1.12, m=M_SCREEN, bevel=0.01)
box("CoffeeMachine", 0.26, 0.3, 0.36, 5.6, -3.1, 1.15, m=M_METAL, bevel=0.02)
cyl("CoffeeCup", 0.05, 0.1, 5.6, -3.1, 0.99, m=M_FABRIC, seg=14)

# 墙上挂钟（客厅）
cyl("WallClock", 0.22, 0.04, 5.9, 1.9, 2.15, rz=math.pi / 2, m=M_FABRIC, seg=24)
cyl("ClockRim", 0.25, 0.02, 5.86, 1.9, 2.15, rz=math.pi / 2, m=M_WOOD, seg=24)

# 餐桌摆件：果盘 + 花瓶
cyl("FruitBowl", 0.16, 0.08, 4.7, 1.3, 0.83, m=M_GOLD, seg=18)
for i, ang in enumerate((0, 1.6, 3.1, 4.6)):
    sph("Fruit", 0.06, 4.7 + math.cos(ang) * 0.07, -1.3 + math.sin(ang) * 0.07, 0.88, m=M_TERRA_FAB)
cyl("Vase", 0.08, 0.24, 4.3, 1.35, 0.9, m=M_SAGE_FAB, seg=16)
sph("VaseFlower", 0.1, 4.3, 1.35, 1.08, m=M_GREEN)

# 书架摆件
for i in range(3):
    box(f"ShelfItem{i}", 0.12, 0.12, 0.18, 5.52, -4.2 + i * 0.45, 1.35, m=M_GOLD, bevel=0.01)

# 床边地毯花纹压边
box("BedRugTrim", 2.0, 0.03, 0.02, -4.0, 2.28, 0.02, m=M_WOOD_L, bevel=0)


# ---------------------------------------------------------------- 书房 / 衣帽间 / 阳台
# 书房（x 3.2~6，z 3.2~6）
box("StudyDeskTop", 0.7, 1.6, 0.06, 5.55, -4.6, 0.76, m=M_WOOD)
for ddy in (-0.7, 0.7):
    box("StudyDeskLeg", 0.07, 0.07, 0.74, 5.55, -4.6 + ddy, 0.37, m=M_DARK, bevel=0)
box("StudyChairSeat", 0.45, 0.45, 0.08, 4.95, -4.6, 0.46, m=M_SAGE_FAB, bevel=0.02)
box("StudyChairBack", 0.45, 0.08, 0.5, 4.72, -4.6, 0.72, m=M_SAGE_FAB, bevel=0.02)
box("StudyLamp", 0.16, 0.16, 0.03, 5.5, -5.3, 0.8, m=M_DARK, bevel=0)
box("StudyLampArm", 0.04, 0.04, 0.34, 5.5, -5.3, 0.98, m=M_DARK, bevel=0)
cyl("StudyLampHead", 0.1, 0.08, 5.5, -5.2, 1.16, m=M_GOLD, seg=16)
box("StudyShelf", 1.4, 0.3, 1.8, 3.9, -5.7, 0.9, m=M_WOOD)
for i in range(4):
    box("StudyShelfBoard", 1.36, 0.28, 0.04, 3.9, -5.7, 0.3 + i * 0.45, m=M_WOOD_L, bevel=0)
rug("StudyRug", 4.4, -4.4, 0.9)
box("StudyBooks1", 0.3, 0.22, 0.05, 5.4, -4.3, 0.8, rz=0.2, m=M_TERRA_FAB, bevel=0)
box("StudyBooks2", 0.28, 0.2, 0.04, 5.42, -4.32, 0.84, rz=0.35, m=M_SAGE_FAB, bevel=0)

# 衣帽间（x -2.6~-1，z 1~6）
box("ClosetWard1", 0.5, 4.4, 2.3, -1.32, -3.4, 1.15, m=M_WOOD)
for i in range(5):
    box("ClosetDoor1", 0.02, 0.85, 2.2, -1.58, -5.3 + i * 0.9, 1.15, m=M_WOOD_L, bevel=0)
box("ClosetWard2", 1.7, 0.45, 2.2, -2.1, -1.32, 1.1, m=M_WOOD)
box("ClosetIsland", 0.8, 0.7, 0.85, -2.15, -3.4, 0.42, m=M_WOOD_L)
box("ClosetIslandTop", 0.85, 0.75, 0.05, -2.15, -3.4, 0.87, m=M_TEX_MARBLE, bevel=0)
cyl("ClosetMirror", 0.4, 0.03, -3.12, -4.6, 1.5, rz=math.pi / 2, m=M_GLASS, seg=28)
cyl("ClosetMirrorRing", 0.44, 0.04, -3.14, -4.6, 1.5, rz=math.pi / 2, m=M_GOLD, seg=28)
rug("ClosetRug", -2.15, -3.9, 0.75, M_RUG)

# 阳台（z 6~8，x -1~6）
box("BalconyFloor", 7.0, 2.0, 0.12, 2.5, -7.0, -0.02, m=M_FLOOR_TILE, bevel=0)
# 玻璃栏板
box("BalconyRailFront", 7.0, 0.06, 1.05, 2.5, -8.0, 0.52, m=M_GLASS, bevel=0)
box("BalconyRailL", 0.06, 2.0, 1.05, -1.0, -7.0, 0.52, m=M_GLASS, bevel=0)
box("BalconyRailR", 0.06, 2.0, 1.05, 6.0, -7.0, 0.52, m=M_GLASS, bevel=0)
box("BalconyRailTop", 7.0, 0.08, 0.06, 2.5, -8.0, 1.06, m=M_METAL, bevel=0)
# 阳台家具
box("BalconyTable", 1.0, 0.6, 0.06, 2.2, -7.3, 0.72, m=M_WOOD)
for dx in (-0.4, 0.4):
    for dy in (-0.22, 0.22):
        box("BalconyTableLeg", 0.06, 0.06, 0.7, 2.2 + dx, -7.3 + dy, 0.35, m=M_DARK, bevel=0)
box("BalconyChair1", 0.44, 0.44, 0.06, 1.2, -7.3, 0.42, m=M_SAGE_FAB, bevel=0.02)
box("BalconyChair1Back", 0.44, 0.06, 0.42, 1.2, -7.52, 0.64, m=M_SAGE_FAB, bevel=0.02)
box("BalconyChair2", 0.44, 0.44, 0.06, 3.2, -7.3, 0.42, m=M_SAGE_FAB, bevel=0.02)
box("BalconyChair2Back", 0.44, 0.06, 0.42, 3.2, -7.52, 0.64, m=M_SAGE_FAB, bevel=0.02)
for i, bx in enumerate((0.0, 5.4)):
    cyl("BalconyPot", 0.2, 0.36, bx, -7.0, 0.18, m=M_WOOD_L)
    for k in range(4):
        a = k * 1.6
        sph("BalconyLeaf", 0.22, bx + math.cos(a) * 0.1, -7.0 + math.sin(a) * 0.1, 0.5 + k * 0.12, m=M_GREEN, sy=0.85)
# 晾衣架
box("DryingRack", 1.4, 0.04, 0.04, 4.6, -7.6, 1.5, m=M_METAL, bevel=0)
box("DryingRackL", 0.04, 0.04, 0.5, 3.9, -7.6, 1.25, m=M_METAL, bevel=0)
box("DryingRackR", 0.04, 0.04, 0.5, 5.3, -7.6, 1.25, m=M_METAL, bevel=0)

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
