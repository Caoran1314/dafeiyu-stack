"""按「205㎡ 偶数层标准户型」重建：
4+1 房两厅三卫一庭院

坐标：单位米，x 向右，z 向下（Blender y = -z）
建筑 14 × 12，花园 10 × 4 接在下方（z 12..16）
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

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = "METRIC"
TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "textures")


# ---------------------------------------------------------------- 材质
def tex_mat(name, file, scale=1.0, rough=0.6, metal=0.0, normal=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    p = os.path.join(TEX, file)
    if os.path.exists(p):
        img = bpy.data.images.load(p, check_existing=True)
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = img
        coord = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (scale, scale, scale)
        nt.links.new(coord.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
        if normal:
            np_ = os.path.join(TEX, normal)
            if os.path.exists(np_):
                ni = bpy.data.images.load(np_, check_existing=True)
                ntex = nt.nodes.new("ShaderNodeTexImage")
                ntex.image = ni
                ntex.image.colorspace_settings.name = "Non-Color"
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nm.inputs["Strength"].default_value = 0.7
                nt.links.new(ntex.outputs["Color"], nm.inputs["Color"])
                nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
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
M_FLOOR_WOOD = tex_mat("FloorOak", "floor_oak.png", 0.5, 0.55, normal="wood_normal.png")
M_FLOOR_STONE = tex_mat("FloorStone", "marble_warm.png", 0.55, 0.3, normal="marble_normal.png")
M_WOOD = tex_mat("WoodWalnut", "wood_walnut.png", 1.1, 0.55, normal="wood_normal.png")
M_WOOD_L = tex_mat("WoodLight", "wood_light.png", 1.2, 0.55, normal="wood_normal.png")
M_FABRIC = tex_mat("Linen", "fabric_linen.png", 2.2, 0.95, normal="fabric_normal.png")
M_STONE = tex_mat("Marble", "marble_warm.png", 0.7, 0.28)
M_DARK = plain("Dark", (0.09, 0.09, 0.10), 0.5)
M_METAL = plain("Metal", (0.42, 0.44, 0.47), 0.3, 0.85)
M_GLASS = plain("Glass", (0.55, 0.68, 0.75), 0.1, 0.0)
M_SCREEN = plain("Screen", (0.05, 0.07, 0.10), 0.15)
M_GREEN = plain("Plant", (0.22, 0.42, 0.26), 0.8)
M_WHITE = plain("White", (0.92, 0.92, 0.90), 0.6)
M_TILE = tex_mat("Tile", "marble_warm.png", 2.0, 0.35)
M_CITY = tex_mat("City", "city_night.png", 1.0, 0.9)
M_SAGE = plain("SageFabric", (0.60, 0.66, 0.58), 0.9)
M_TERRA = plain("TerraFabric", (0.70, 0.46, 0.38), 0.9)
M_GOLD = plain("Gold", (0.78, 0.64, 0.36), 0.3, 0.8)


# ---------------------------------------------------------------- 工具
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


def cyl(name, r, h, x, y, z, rz=0.0, m=None, seg=24, scale=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=h, location=(x, y, z))
    o = bpy.context.active_object
    o.name = name
    o.rotation_euler[2] = rz
    if scale:
        o.scale = scale
    if m:
        o.data.materials.append(m)
    return o


def sph(name, r, x, y, z, m=None, s=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=18, ring_count=12, radius=r, location=(x, y, z))
    o = bpy.context.active_object
    o.name = name
    if s:
        o.scale = s
    if m:
        o.data.materials.append(m)
    return o


def B(name, w, d, h, x, z, *rest):
    """网页坐标写法：w 沿 x，d 沿 z，h 高；rest 可为 (材质) / (底面高度, 材质)"""
    y = 0.0
    m = None
    rz = 0.0
    nums = [a for a in rest if isinstance(a, (int, float))]
    mats = [a for a in rest if not isinstance(a, (int, float))]
    if nums:
        y = nums[0]
    if len(nums) > 1:
        rz = nums[1]
    if mats:
        m = mats[0]
    return box(name, w, d, h, x, -z, y + h / 2, rz=rz, m=m)


def wall_z(z, x0, x1, door=None, dw=1.0, h=H):
    y = -z
    segs = [(x0, x1)] if door is None else [(x0, door - dw / 2), (door + dw / 2, x1)]
    for i, (a, b) in enumerate(segs):
        if b - a > 0.05:
            box(f"W_{int(z*100)}_{int(a*100)}", b - a, WALL, h, (a + b) / 2, y, h / 2, m=M_WALL, bevel=0)
    if door is not None:
        box(f"WL_{int(z*100)}_{int(door*100)}", dw, WALL, h - 2.1, door, y, (h + 2.1) / 2, m=M_WALL, bevel=0)


def wall_x(x, z0, z1, door=None, dw=1.0, h=H):
    segs = [(z0, z1)] if door is None else [(z0, door - dw / 2), (door + dw / 2, z1)]
    for i, (a, b) in enumerate(segs):
        if b - a > 0.05:
            box(f"W_{int(x*100)}_{int(a*100)}", WALL, b - a, h, x, -(a + b) / 2, h / 2, m=M_WALL, bevel=0)
    if door is not None:
        box(f"WL_{int(x*100)}_{int(door*100)}", WALL, dw, h - 2.1, x, -door, (h + 2.1) / 2, m=M_WALL, bevel=0)


# ---------------------------------------------------------------- 地面（分区材质）
floors = [
    ("F_Garden", 4, 14, 12, 16, M_TILE),
    ("F_Living", 8.0, 14, 6.4, 11.6, M_FLOOR_STONE),
    ("F_Dining", 9.2, 14, 3.6, 6.4, M_FLOOR_STONE),
    ("F_Kitchen", 9.2, 14, 3.6, 6.4, M_TILE),
    ("F_Bed1", 2.4, 6.0, 0, 3.8, M_FLOOR_WOOD),
    ("F_Study1", 6.8, 9.4, 0, 3.8, M_FLOOR_WOOD),
    ("F_Bed2", 9.4, 14, 0, 3.8, M_FLOOR_WOOD),
    ("F_Master", 1.4, 4.8, 7.4, 11.8, M_FLOOR_WOOD),
    ("F_MasterBath", 0, 1.4, 7.4, 11.8, M_TILE),
    ("F_Bed3", 4.8, 7.4, 7.4, 11.8, M_FLOOR_WOOD),
    ("F_Hall", 3.0, 9.2, 3.8, 6.4, M_FLOOR_STONE),
    ("F_Closet1", 0.6, 3.0, 6.4, 7.4, M_FLOOR_WOOD),
    ("F_Closet2", 4.8, 6.8, 6.4, 7.4, M_FLOOR_WOOD),
    ("F_Bath2", 3.0, 4.8, 3.8, 5.4, M_TILE),
    ("F_SvcBalcony", 4.8, 7.4, 11.8, 12.6, M_TILE),
    ("F_LiftHall", 0, 3.0, 5.4, 7.4, M_FLOOR_STONE),
]
for name, x0, x1, z0, z1, mat in floors:
    box(name, x1 - x0, z1 - z0, 0.1, (x0 + x1) / 2, -(z0 + z1) / 2, -0.05, m=mat, bevel=0)

# ---------------------------------------------------------------- 外墙
wall_z(0, 2.4, 14)                       # 上外墙（次卧/书房一侧）
wall_x(14, 0, 11.6)                      # 右外墙
wall_z(11.6, 7.4, 14, door=9.0, dw=2.4)  # 客厅→花园 推拉门
wall_z(12.6, 4.8, 7.4)                   # 服务阳台外沿
wall_x(4.8, 11.6, 12.6)
wall_x(7.4, 11.6, 12.6)
wall_z(7.4, 0, 1.4)                      # 主卫上沿外墙
wall_x(0, 5.4, 11.6)                     # 左外墙
wall_z(5.4, 0, 3.0, door=1.4, dw=1.2)    # 入户门（电梯厅→玄关）
wall_x(2.4, 0, 3.8)                      # 左侧凹口

# ---------------------------------------------------------------- 内墙
# 上排：次卧A / 次卫 / 书房 / 次卧B
wall_x(2.4, 0, 7.4, door=6.2, dw=0.9)
wall_x(6.0, 0, 3.8, door=1.6, dw=0.8)
wall_x(9.4, 0, 3.8, door=2.2, dw=0.9)
wall_z(3.8, 0, 9.4, door=4.0, dw=1.0)    # 上排与走廊之间（门在次卧A、书房）
# 次卫与书房之间
wall_x(6.8, 0, 3.0)
wall_z(3.0, 6.0, 6.8)
# 走廊下沿
wall_z(6.4, 0.0, 3.0, door=1.6, dw=1.0)   # 衣帽间A
wall_z(6.4, 3.0, 4.8, door=3.6, dw=0.9)   # 次卫下沿/玄关
wall_z(6.4, 4.8, 7.4, door=5.4, dw=0.9)   # 衣帽间B
# 主卧/主卫
wall_x(1.4, 7.4, 11.8, door=9.2, dw=0.9)
wall_z(7.4, 0.0, 1.4)
wall_z(7.4, 2.4, 4.8, door=3.4, dw=0.9)   # 主卧上墙（门）
wall_x(4.8, 7.4, 11.8, door=10.4, dw=0.9)  # 主卧 / 次卧C
wall_x(7.4, 7.4, 11.8, door=9.6, dw=1.0)   # 次卧C / 客厅
# 客厅与餐厅
wall_z(6.4, 9.2, 14, door=10.6, dw=1.2)
wall_x(9.2, 3.8, 6.4)
# 厨房隔断（中厨 / 西厨）
wall_z(5.4, 9.2, 14, door=10.2, dw=0.9)
# 电梯厅
wall_x(3.0, 5.4, 7.4, door=6.4, dw=1.0)
wall_z(5.4, 0, 3.0, door=1.4, dw=1.2)

# ---------------------------------------------------------------- 家具（按图纸）
# 次卧 A（左上）
B("Bed1", 1.8, 2.1, 0.42, 3.4, 1.4, 0.0, M_FABRIC)
B("Bed1Head", 1.9, 0.12, 0.85, 3.4, 0.35, 0.0, M_WOOD)
B("Night1", 0.45, 0.4, 0.5, 2.65, 0.9, 0.0, M_WOOD)
B("Ward1", 1.6, 0.6, 2.3, 4.9, 0.4, 0.0, M_WOOD)
B("Rug1", 2.4, 2.0, 0.02, 3.4, 2.6, 0.0, M_SAGE)

# 次卫
B("Toilet1", 0.4, 0.6, 0.42, 6.25, 0.7, 0.0, M_WHITE)
B("Sink1", 0.7, 0.45, 0.85, 6.25, 2.4, 0.0, M_WHITE)
B("Shower1", 1.0, 1.0, 0.05, 6.5, 3.3, 0.0, M_TILE)
cyl("ShowerGlass", 0.5, 1.9, 6.5, -3.3, 0.95, m=M_GLASS, seg=12, scale=(1.0, 1.0, 1.0))

# 书房（上排中）
B("DeskStudy", 1.7, 0.75, 0.75, 8.1, 1.2, 0.0, M_WOOD)
B("ChairStudy", 0.5, 0.5, 0.45, 8.1, 1.9, 0.0, M_DARK)
B("ShelfStudy", 1.8, 0.35, 2.1, 8.1, 0.25, 0.0, M_WOOD)
B("RugStudy", 2.2, 1.8, 0.02, 8.1, 2.4, 0.0, M_FABRIC)

# 次卧 B（右上）
B("Bed2", 2.0, 2.2, 0.42, 11.6, 1.6, 0.0, M_FABRIC)
B("Bed2Head", 2.1, 0.12, 0.85, 11.6, 0.5, 0.0, M_WOOD)
B("Night2", 0.45, 0.4, 0.5, 10.3, 0.9, 0.0, M_WOOD)
B("Night3", 0.45, 0.4, 0.5, 12.9, 0.9, 0.0, M_WOOD)
B("Ward2", 2.4, 0.6, 2.3, 12.3, 3.4, 0.0, M_WOOD)
B("Rug2", 2.6, 2.0, 0.02, 11.6, 2.9, 0.0, M_SAGE)

# 卫生间（走廊左）
B("Toilet2", 0.4, 0.6, 0.42, 3.35, 4.2, 0.0, M_WHITE)
B("Sink2", 0.7, 0.45, 0.85, 4.4, 4.2, 0.0, M_WHITE)
B("Mirror2", 0.6, 0.03, 0.8, 4.55, 4.2, 1.2, M_GLASS)

# 玄关
B("ShoeCab", 1.6, 0.38, 1.0, 3.9, 6.15, 0.0, M_WOOD)
B("Mirror3", 0.6, 0.04, 1.2, 3.6, 6.36, 0.9, M_GLASS)

# 中西厨
B("CounterC", 3.6, 0.65, 0.9, 11.2, 3.95, 0.0, M_WOOD)
B("CounterCTop", 3.7, 0.7, 0.05, 11.2, 3.95, 0.9, M_STONE)
B("CounterW", 2.4, 0.65, 0.9, 10.6, 5.1, 0.0, M_WOOD)
B("Island", 1.8, 0.9, 0.9, 11.8, 4.9, 0.0, M_WOOD)
B("IslandTop", 1.9, 1.0, 0.06, 11.8, 4.9, 0.9, M_STONE)
B("Stove", 0.7, 0.5, 0.04, 10.6, 3.95, 0.94, M_DARK)
cyl("SinkK", 0.22, 0.04, 12.4, -3.95, 0.94, m=M_METAL, seg=20)
B("Fridge", 0.75, 0.7, 1.95, 13.35, 4.3, 0.0, M_WHITE)
B("CabUpper", 3.6, 0.35, 0.7, 11.2, 3.72, 1.75, M_WOOD)

# 餐厅（西餐）
B("DiningT", 1.9, 1.0, 0.75, 11.4, 6.0, 0.0, M_WOOD)
for i, (dx, dz) in enumerate([(-0.6, -0.75), (0.0, -0.75), (0.6, -0.75), (-0.6, 0.75), (0.0, 0.75), (0.6, 0.75)]):
    B(f"DChair{i}", 0.42, 0.42, 0.45, 11.4 + dx, 6.0 + dz, 0.0, M_WOOD_L)

# 客厅
B("SofaMain", 3.0, 1.0, 0.42, 11.6, 9.2, 0.0, M_FABRIC)
B("SofaBack", 3.0, 0.24, 0.75, 11.6, 8.75, 0.0, M_FABRIC)
B("SofaArmL", 0.24, 1.0, 0.55, 10.0, 9.2, 0.0, M_FABRIC)
B("SofaArmR", 0.24, 1.0, 0.55, 13.2, 9.2, 0.0, M_FABRIC)
B("RugLiving", 3.6, 2.6, 0.02, 11.6, 9.9, 0.0, M_FABRIC)
B("CoffeeT", 1.4, 0.7, 0.42, 11.6, 10.2, 0.0, M_WOOD)
B("TvCab", 2.6, 0.45, 0.45, 11.6, 8.2, 0.0, M_WOOD)
B("Tv", 2.2, 0.08, 1.25, 11.6, 8.05, 0.75, M_SCREEN)
B("BookShelfL", 0.4, 3.0, 2.1, 8.3, 9.6, 0.0, M_WOOD)

# 主卫
B("Tub", 1.3, 0.75, 0.55, 0.7, 10.8, 0.0, M_WHITE)
B("VanityM", 1.6, 0.5, 0.85, 0.8, 9.4, 0.0, M_WOOD)
B("VanityMTop", 1.7, 0.55, 0.05, 0.8, 9.4, 0.85, M_STONE)
B("MirrorM", 1.4, 0.04, 1.1, 0.8, 9.15, 1.1, M_GLASS)
B("ToiletM", 0.4, 0.6, 0.42, 0.6, 8.1, 0.0, M_WHITE)

# 主卧
B("BedM", 2.0, 2.2, 0.45, 3.1, 10.3, 0.0, M_FABRIC)
B("BedMHead", 2.1, 0.14, 1.0, 3.1, 9.05, 0.0, M_WOOD)
B("NightM1", 0.5, 0.45, 0.55, 1.95, 9.35, 0.0, M_WOOD)
B("NightM2", 0.5, 0.45, 0.55, 4.25, 9.35, 0.0, M_WOOD)
B("RugM", 2.8, 2.2, 0.02, 3.1, 11.1, 0.0, M_SAGE)

# 次卧 C（下方中）
B("BedC", 1.8, 2.0, 0.42, 6.1, 10.4, 0.0, M_FABRIC)
B("BedCHead", 1.9, 0.12, 0.9, 6.1, 9.25, 0.0, M_WOOD)
B("WardC", 1.8, 0.6, 2.3, 6.1, 7.8, 0.0, M_WOOD)
B("DeskC", 1.2, 0.6, 0.75, 5.2, 11.4, 0.0, M_WOOD)

# 衣帽间 x2
for idx, cx in [(1, 1.7), (2, 5.8)]:
    B(f"ClWard{idx}a", 0.5, 3.0, 2.3, cx - 0.9, 7.0, 0.0, M_WOOD)
    B(f"ClWard{idx}b", 0.5, 3.0, 2.3, cx + 0.9, 7.0, 0.0, M_WOOD)
    B(f"ClIsland{idx}", 0.9, 0.7, 0.85, cx, 7.0, 0.0, M_WOOD_L)

# 服务阳台
B("Washer", 0.65, 0.65, 0.9, 5.2, 12.2, 0.0, M_WHITE)
B("Dryer", 0.65, 0.65, 0.9, 6.0, 12.2, 0.0, M_WHITE)
B("SvcSink", 0.6, 0.5, 0.85, 6.9, 12.2, 0.0, M_METAL)

# 电梯厅
B("LiftBox", 1.2, 1.2, 2.4, 1.0, 6.4, 0.0, M_METAL)
B("BenchL", 1.4, 0.45, 0.45, 2.2, 6.7, 0.0, M_WOOD)

# 花园
B("GardenDeck", 4.0, 4.0, 0.06, 11.0, 14.0, 0.0, M_TILE)
B("GardenTable", 1.2, 0.8, 0.72, 10.6, 14.0, 0.0, M_WOOD)
for i, (dx, dz) in enumerate([(-0.9, 0), (0.9, 0), (0, -0.7), (0, 0.7)]):
    B(f"GChair{i}", 0.45, 0.45, 0.42, 10.6 + dx, 14.0 + dz, 0.0, M_DARK)
cyl("Parasol", 0.1, 2.4, 10.6, -14.0, 1.2, m=M_METAL, seg=10)
cyl("ParasolTop", 1.5, 0.12, 10.6, -14.0, 2.4, m=M_FABRIC, seg=20, scale=(1, 1, 1))
for i, (px, pz) in enumerate([(7.2, 13.0), (13.6, 13.2), (7.6, 15.4), (13.2, 15.4)]):
    cyl(f"GPot{i}", 0.25, 0.45, px, -pz, 0.22, m=M_WOOD_L)
    sph(f"GPlant{i}", 0.35, px, -pz, 0.7, m=M_GREEN)
B("GardenFence1", 10.0, 0.08, 1.2, 9.0, 16.0, 0.0, M_METAL)
B("GardenFence2", 0.08, 4.0, 1.2, 14.0, 14.0, 0.0, M_METAL)

# 灯（发光片，网页里另加光源）
for i, (lx, lz, r) in enumerate([(11.6, 9.4, 0.3), (11.4, 6.0, 0.26), (3.1, 10.2, 0.26),
                                 (3.4, 1.6, 0.24), (8.1, 1.6, 0.22), (11.6, 1.6, 0.24),
                                 (3.9, 5.9, 0.2), (11.2, 4.2, 0.24), (1.4, 6.4, 0.2)]):
    cyl(f"Lamp{i}", r, 0.06, lx, -lz, 2.72, m=M_GOLD, seg=18)

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
