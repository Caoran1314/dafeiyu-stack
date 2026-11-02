"""按参考图生成 蓝发鲸鱼女仆 人物 → character.glb

运行：
  双击 export_character.bat
  或 "%LOCALAPPDATA%\\Programs\\Blender Foundation\\Blender 4.5\\blender.exe" ^
      --background --python build_character.py -- --out 输出.glb

规范：
  · 身高约 1.45 m，原点在脚底，面向 -Y（导出后在 three.js 里面向 +Z）
  · 刚性蒙皮：每个部件绑定到单一骨骼（关节处会有硬折角，但绝对稳定）
  · 动作：idle / walk / sit / lie / sleep / phone / tv / pet
"""
import bpy
import sys
import os
import math
from mathutils import Vector, Euler

argv = sys.argv
out_path = None
if "--" in argv:
    args = argv[argv.index("--") + 1:]
    if "--out" in args:
        out_path = args[args.index("--out") + 1]
if not out_path:
    out_path = os.path.join(os.path.dirname(__file__), "character.glb")

# ---------------------------------------------------------------- 颜色
C_HAIR = (0.29, 0.52, 0.78, 1)
C_HAIR_L = (0.50, 0.70, 0.88, 1)
C_DRESS = (0.16, 0.24, 0.42, 1)
C_WHITE = (0.95, 0.95, 0.93, 1)
C_SKIN = (0.99, 0.91, 0.87, 1)
C_EYE = (0.23, 0.44, 0.71, 1)
C_BLACK = (0.08, 0.08, 0.10, 1)
C_BOW = (0.50, 0.70, 0.88, 1)
C_TAIL = (0.22, 0.38, 0.62, 1)


def mat(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def sphere(name, r, loc, scale=(1, 1, 1), seg=24, ring=16, material=None):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=ring)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    if material:
        o.data.materials.append(material)
    return o


def cyl(name, r1, r2, depth, loc, rot=(0, 0, 0), material=None, verts=20):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2,
                                    depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    bpy.ops.object.shade_smooth()
    if material:
        o.data.materials.append(material)
    return o


def cube(name, size, loc, rot=(0, 0, 0), scale=(1, 1, 1), material=None):
    bpy.ops.mesh.primitive_cube_add(size=size, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        o.data.materials.append(material)
    return o


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m_hair = mat("Hair", C_HAIR, 0.45)
    m_hair_l = mat("HairLight", C_HAIR_L, 0.45)
    m_dress = mat("Dress", C_DRESS, 0.7)
    m_white = mat("White", C_WHITE, 0.75)
    m_skin = mat("Skin", C_SKIN, 0.55)
    m_eye = mat("Eye", C_EYE, 0.25)
    m_black = mat("Black", C_BLACK, 0.4)
    m_bow = mat("Bow", C_BOW, 0.6)
    m_tail = mat("Tail", C_TAIL, 0.5)

    # ---------------- 骨架 ----------------
    bpy.ops.object.armature_add(enter_editmode=True, location=(0, 0, 0))
    arm = bpy.context.active_object
    arm.name = "Rig"
    eb = arm.data.edit_bones
    eb.remove(eb[0])

    def bone(name, head, tail, parent=None, connect=False):
        b = eb.new(name)
        b.head = Vector(head)
        b.tail = Vector(tail)
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
        return b

    bone("root", (0, 0, 0), (0, 0, 0.1))
    bone("hips", (0, 0, 0.62), (0, 0, 0.74), "root")
    bone("spine", (0, 0, 0.74), (0, 0, 0.92), "hips", True)
    bone("chest", (0, 0, 0.92), (0, 0, 1.04), "spine", True)
    bone("neck", (0, 0, 1.04), (0, 0, 1.10), "chest", True)
    bone("head", (0, 0, 1.10), (0, 0, 1.34), "neck", True)

    for side, sx in (("L", 1), ("R", -1)):
        bone(f"shoulder.{side}", (sx * 0.06, 0, 1.00), (sx * 0.15, 0, 1.00), "chest")
        bone(f"upperarm.{side}", (sx * 0.15, 0, 1.00), (sx * 0.17, 0, 0.84), f"shoulder.{side}", True)
        bone(f"forearm.{side}", (sx * 0.17, 0, 0.84), (sx * 0.18, 0, 0.70), f"upperarm.{side}", True)
        bone(f"hand.{side}", (sx * 0.18, 0, 0.70), (sx * 0.18, 0, 0.64), f"forearm.{side}", True)
        bone(f"thigh.{side}", (sx * 0.07, 0, 0.60), (sx * 0.07, 0, 0.34), "hips")
        bone(f"shin.{side}", (sx * 0.07, 0, 0.34), (sx * 0.07, 0, 0.07), f"thigh.{side}", True)
        bone(f"foot.{side}", (sx * 0.07, 0, 0.07), (sx * 0.07, -0.12, 0.03), f"shin.{side}", True)
    bone("tail", (-0.02, 0.10, 0.66), (-0.10, 0.34, 0.52), "hips")
    for side, sx in (("L", 1), ("R", -1)):
        bone(f"hair.{side}", (sx * 0.10, 0.02, 1.28), (sx * 0.16, 0.06, 1.02), "head")

    bpy.ops.object.mode_set(mode="OBJECT")

    parts = []          # (object, bone_name)

    # ---------------- 身体 ----------------
    # 头（脸露出来，头发在后面和侧上方）
    parts.append((sphere("Head", 0.150, (0, 0, 1.235), (1.0, 0.98, 1.05), material=m_skin), "head"))
    parts.append((cyl("Neck", 0.042, 0.042, 0.075, (0, 0.005, 1.095), material=m_skin), "neck"))
    # 后脑头发（往后偏，不挡脸）
    parts.append((sphere("HairBack", 0.168, (0, 0.045, 1.245), (1.02, 1.0, 1.06), material=m_hair), "head"))
    # 刘海：额头上一排压扁的球，做出齐刘海
    for i, (bx, bz, br) in enumerate([(-0.085, 1.30, 0.062), (-0.03, 1.315, 0.066),
                                     (0.03, 1.315, 0.066), (0.085, 1.30, 0.062)]):
        parts.append((sphere(f"Bang{i}", br, (bx, -0.105, bz), (1.15, 0.55, 0.9), material=m_hair), "head"))
    # 两侧鬓发
    for sx in (1, -1):
        parts.append((sphere(f"SideHair{sx}", 0.075, (sx * 0.135, -0.02, 1.19),
                             (0.55, 0.9, 1.5), material=m_hair), "head"))
    # 呆毛
    parts.append((cyl("Ahoge", 0.011, 0.004, 0.17, (0.005, -0.01, 1.40),
                      rot=(math.radians(-16), 0, math.radians(10)), material=m_hair), "head"))
    # 双马尾（长）
    for side, sx in (("L", 1), ("R", -1)):
        parts.append((sphere(f"TwinTail.{side}", 0.075, (sx * 0.185, 0.075, 1.13),
                             (0.62, 0.7, 1.7), material=m_hair), f"hair.{side}"))
        parts.append((sphere(f"TwinTail2.{side}", 0.062, (sx * 0.20, 0.085, 0.88),
                             (0.66, 0.72, 1.7), material=m_hair_l), f"hair.{side}"))
        parts.append((sphere(f"TwinTail3.{side}", 0.048, (sx * 0.205, 0.09, 0.66),
                             (0.7, 0.75, 1.3), material=m_hair_l), f"hair.{side}"))
        parts.append((sphere(f"Bow.{side}", 0.048, (sx * 0.165, 0.02, 1.235),
                             (1.4, 0.55, 0.85), material=m_bow), "head"))
    # 鲸鱼耳鳍
    for side, sx in (("L", 1), ("R", -1)):
        parts.append((cube(f"Fin.{side}", 1, (sx * 0.175, 0.06, 1.30),
                           rot=(0, math.radians(14), math.radians(sx * -20)),
                           scale=(0.095, 0.018, 0.05), material=m_tail), "head"))
    # 女仆头饰（白边 + 布带）
    parts.append((cyl("Headdress", 0.152, 0.152, 0.03, (0, 0.035, 1.375), material=m_white), "head"))
    for i in range(9):
        ang = math.radians(-70 + i * 17.5)
        parts.append((sphere(f"Frill{i}", 0.035, (math.sin(ang) * 0.15, 0.035 + math.cos(ang) * 0.15, 1.392),
                             (1.0, 1.0, 0.6), material=m_white), "head"))

    # 眼睛（大、深蓝、带高光）
    for sx in (1, -1):
        tag = "L" if sx > 0 else "R"
        parts.append((sphere(f"EyeWhite.{tag}", 0.040, (sx * 0.062, -0.118, 1.245),
                             (0.85, 0.55, 1.2), material=m_white), "head"))
        parts.append((sphere(f"Pupil.{tag}", 0.031, (sx * 0.062, -0.132, 1.243),
                             (0.9, 0.5, 1.25), material=m_eye), "head"))
        parts.append((sphere(f"Glint.{tag}", 0.011, (sx * 0.052, -0.146, 1.262),
                             (1.0, 0.5, 1.0), material=m_white), "head"))
    # 腮红
    for sx in (1, -1):
        parts.append((sphere(f"Blush{sx}", 0.026, (sx * 0.095, -0.118, 1.198),
                             (1.2, 0.35, 0.7),
                             material=mat(f"Blush{sx}", (0.98, 0.72, 0.72, 1), 0.8)), "head"))

    # 嘴 + 眉
    parts.append((sphere("Mouth", 0.014, (0, -0.146, 1.185), (1.3, 0.4, 0.7),
                         material=mat("MouthColor", (0.85, 0.52, 0.55, 1), 0.7)), "head"))
    for sx in (1, -1):
        parts.append((cube(f"Brow{sx}", 1, (sx * 0.062, -0.142, 1.300),
                           rot=(0, 0, math.radians(sx * 6)),
                           scale=(0.045, 0.008, 0.008), material=m_hair), "head"))

    # 躯干
    parts.append((sphere("Chest", 0.115, (0, 0, 0.955), (1.12, 0.82, 0.95), material=m_dress), "chest"))
    parts.append((sphere("Chemise", 0.075, (0, -0.075, 0.985), (1.15, 0.55, 1.15), material=m_white), "chest"))
    parts.append((sphere("Waist", 0.098, (0, 0, 0.80), (1.05, 0.82, 0.85), material=m_dress), "spine"))
    parts.append((sphere("Hips", 0.115, (0, 0, 0.68), (1.1, 0.9, 0.85), material=m_dress), "hips"))
    # 腰带 + 金扣
    parts.append((cyl("Belt", 0.125, 0.12, 0.045, (0, 0, 0.755), material=m_black), "spine"))
    for dx in (-0.045, 0.045):
        parts.append((sphere(f"Buckle{dx}", 0.013, (dx, -0.118, 0.755), (1, 0.5, 1),
                             material=mat("Gold", (0.83, 0.68, 0.35, 1), 0.35, 0.8)), "spine"))

    # 裙子（短一点，露出腿）
    parts.append((cyl("Skirt", 0.235, 0.125, 0.21, (0, 0, 0.575), material=m_dress), "hips"))
    parts.append((cyl("SkirtFrill", 0.248, 0.235, 0.04, (0, 0, 0.475), material=m_white), "hips"))
    # 围裙
    parts.append((cube("Apron", 1, (0, -0.105, 0.60), scale=(0.175, 0.025, 0.24), material=m_white), "hips"))
    parts.append((cyl("ApronFrill", 0.175, 0.165, 0.035, (0, -0.02, 0.475), material=m_white), "hips"))
    # 围裙上的鲸鱼图案（简单蓝椭圆 + 尾鳍）
    parts.append((sphere("WhaleBody", 0.032, (0, -0.128, 0.555), (1.4, 0.25, 0.9),
                         material=mat("WhaleBlue", (0.35, 0.58, 0.82, 1), 0.5)), "hips"))

    # 手臂
    for side, sx in (("L", 1), ("R", -1)):
        parts.append((sphere(f"Shoulder.{side}", 0.052, (sx * 0.112, 0, 0.99),
                             (1.0, 0.95, 0.95), material=m_dress), f"shoulder.{side}"))
        parts.append((cyl(f"UpperArm.{side}", 0.042, 0.038, 0.16, (sx * 0.152, 0, 0.905),
                          material=m_dress), f"upperarm.{side}"))
        parts.append((cyl(f"Cuff.{side}", 0.043, 0.043, 0.035, (sx * 0.168, 0, 0.815),
                          material=m_white), f"forearm.{side}"))
        parts.append((cyl(f"ForeArm.{side}", 0.035, 0.032, 0.135, (sx * 0.172, 0, 0.755),
                          material=m_skin), f"forearm.{side}"))
        parts.append((sphere(f"Hand.{side}", 0.035, (sx * 0.175, 0, 0.678),
                             (0.9, 0.8, 1.05), material=m_skin), f"hand.{side}"))

    # 腿（可见）+ 白袜 + 黑皮鞋
    for side, sx in (("L", 1), ("R", -1)):
        parts.append((cyl(f"Thigh.{side}", 0.056, 0.048, 0.24, (sx * 0.068, 0, 0.46), material=m_skin), f"thigh.{side}"))
        parts.append((cyl(f"Sock.{side}", 0.045, 0.04, 0.20, (sx * 0.068, 0, 0.18), material=m_white), f"shin.{side}"))
        parts.append((cube(f"Shoe.{side}", 1, (sx * 0.068, -0.035, 0.035),
                           scale=(0.075, 0.135, 0.048), material=m_black), f"foot.{side}"))

    # 鲸鱼尾巴
    parts.append((sphere("TailBase", 0.072, (-0.02, 0.145, 0.66), (0.75, 1.3, 0.75), material=m_tail), "tail"))
    parts.append((sphere("TailMid", 0.062, (-0.06, 0.27, 0.58), (0.7, 1.3, 0.7), material=m_tail), "tail"))
    parts.append((sphere("TailFin", 0.105, (-0.10, 0.38, 0.50),
                         (1.7, 0.4, 0.85), material=m_tail), "tail"))
    # 领口蝴蝶结
    parts.append((sphere("NeckBow", 0.042, (0, -0.088, 1.058), (1.7, 0.6, 0.75), material=m_bow), "chest"))

    # ---------------- 合并 + 刚性蒙皮 ----------------
    for obj, bone_name in parts:
        vg = obj.vertex_groups.new(name=bone_name)
        vg.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        obj.parent = arm

    # ---------------- 动作 ----------------
    def key_pose(frame, poses):
        bpy.context.scene.frame_set(frame)
        for bname, rot in poses.items():
            pb = arm.pose.bones.get(bname)
            if not pb:
                continue
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = Euler([math.radians(a) for a in rot], "XYZ")
            pb.keyframe_insert("rotation_euler", frame=frame)

    def key_loc(frame, bname, loc):
        bpy.context.scene.frame_set(frame)
        pb = arm.pose.bones.get(bname)
        if not pb:
            return
        pb.location = Vector(loc)
        pb.keyframe_insert("location", frame=frame)

    def new_action(name):
        arm.animation_data_create()
        act = bpy.data.actions.new(name)
        act.use_fake_user = True
        arm.animation_data.action = act
        return act

    # idle：呼吸 + 轻微摆头
    new_action("idle")
    key_pose(1, {"chest": (0, 0, 0), "head": (0, 0, 0), "tail": (0, 0, 6)})
    key_pose(30, {"chest": (-2, 0, 0), "head": (1, 0, 2), "tail": (0, 0, -6)})
    key_pose(60, {"chest": (0, 0, 0), "head": (0, 0, 0), "tail": (0, 0, 6)})

    # walk：手脚摆动
    new_action("walk")
    key_pose(1, {"thigh.L": (18, 0, 0), "thigh.R": (-18, 0, 0),
                 "shin.L": (-8, 0, 0), "shin.R": (10, 0, 0),
                 "upperarm.L": (-14, 0, 0), "upperarm.R": (14, 0, 0), "chest": (0, 0, 3)})
    key_pose(12, {"thigh.L": (0, 0, 0), "thigh.R": (0, 0, 0),
                  "shin.L": (0, 0, 0), "shin.R": (0, 0, 0),
                  "upperarm.L": (0, 0, 0), "upperarm.R": (0, 0, 0), "chest": (0, 0, 0)})
    key_pose(24, {"thigh.L": (-18, 0, 0), "thigh.R": (18, 0, 0),
                  "shin.L": (10, 0, 0), "shin.R": (-8, 0, 0),
                  "upperarm.L": (14, 0, 0), "upperarm.R": (-14, 0, 0), "chest": (0, 0, -3)})
    key_pose(36, {"thigh.L": (0, 0, 0), "thigh.R": (0, 0, 0),
                  "shin.L": (0, 0, 0), "shin.R": (0, 0, 0),
                  "upperarm.L": (0, 0, 0), "upperarm.R": (0, 0, 0), "chest": (0, 0, 0)})
    key_pose(48, {"thigh.L": (18, 0, 0), "thigh.R": (-18, 0, 0),
                  "shin.L": (-8, 0, 0), "shin.R": (10, 0, 0),
                  "upperarm.L": (-14, 0, 0), "upperarm.R": (14, 0, 0), "chest": (0, 0, 3)})

    # sit：坐下（大腿抬起，膝盖弯）
    new_action("sit")
    key_pose(1, {"thigh.L": (-78, 0, 0), "thigh.R": (-78, 0, 0),
                 "shin.L": (76, 0, 0), "shin.R": (76, 0, 0),
                 "chest": (4, 0, 0), "upperarm.L": (-8, 0, 0), "upperarm.R": (-8, 0, 0)})
    key_loc(1, "root", (0, 0, -0.30))
    key_pose(30, {"thigh.L": (-78, 0, 0), "thigh.R": (-78, 0, 0),
                  "shin.L": (76, 0, 0), "shin.R": (76, 0, 0),
                  "chest": (3, 0, 0), "head": (-2, 0, 0)})

    # lie：躺下（整体转 -90°，头部略抬）
    new_action("lie")
    key_pose(1, {"root": (-88, 0, 0), "head": (12, 0, 0), "chest": (4, 0, 0),
                 "upperarm.L": (-10, 0, 8), "upperarm.R": (-10, 0, -8),
                 "thigh.L": (-6, 0, 0), "thigh.R": (-6, 0, 0)})
    key_loc(1, "root", (0, 0.55, 0.60))
    key_pose(30, {"root": (-88, 0, 0), "head": (15, 0, 2), "chest": (5, 0, 0),
                  "upperarm.L": (-12, 0, 10), "upperarm.R": (-12, 0, -10)})
    key_loc(30, "root", (0, 0.55, 0.60))

    # sleep：躺下 + 手臂放下 + 闭眼（用头略低模拟）
    new_action("sleep")
    key_pose(1, {"root": (-90, 0, 0), "head": (10, 0, 0), "chest": (2, 0, 0),
                 "upperarm.L": (12, 0, 6), "upperarm.R": (12, 0, -6),
                 "forearm.L": (-8, 0, 0), "forearm.R": (-8, 0, 0)})
    key_loc(1, "root", (0, 0.55, 0.58))
    key_pose(60, {"root": (-90, 0, 0), "head": (12, 0, 1), "chest": (3, 0, 0),
                  "upperarm.L": (14, 0, 6), "upperarm.R": (14, 0, -6)})
    key_loc(60, "root", (0, 0.55, 0.58))

    # phone：躺着举着手机
    new_action("phone")
    key_pose(1, {"root": (-84, 0, 0), "head": (18, 0, 0), "chest": (6, 0, 0),
                 "upperarm.L": (-58, 0, 10), "forearm.L": (-62, 0, 0),
                 "upperarm.R": (-20, 0, -8), "thigh.L": (-10, 0, 0), "thigh.R": (-14, 0, 0)})
    key_loc(1, "root", (0, 0.55, 0.60))
    key_pose(40, {"root": (-84, 0, 0), "head": (20, 0, 2), "forearm.L": (-64, 0, 0)})
    key_loc(40, "root", (0, 0.55, 0.60))

    # tv：坐着看向前方
    new_action("tv")
    key_pose(1, {"thigh.L": (-80, 0, 0), "thigh.R": (-80, 0, 0),
                 "shin.L": (78, 0, 0), "shin.R": (78, 0, 0),
                 "chest": (-4, 0, 0), "head": (-4, 0, 0),
                 "upperarm.L": (-16, 0, 6), "upperarm.R": (-16, 0, -6)})
    key_loc(1, "root", (0, 0, -0.30))
    key_pose(45, {"chest": (-5, 0, 0), "head": (-6, 0, 0)})

    # pet：蹲下摸猫
    new_action("pet")
    key_pose(1, {"thigh.L": (-96, 0, 0), "thigh.R": (-96, 0, 0),
                 "shin.L": (96, 0, 0), "shin.R": (96, 0, 0),
                 "chest": (26, 0, 0), "head": (16, 0, 0),
                 "upperarm.L": (-46, 0, 10), "forearm.L": (-24, 0, 0),
                 "upperarm.R": (-30, 0, -8)})
    key_loc(1, "root", (0, 0, -0.40))
    key_pose(50, {"chest": (28, 0, 0), "head": (18, 0, 3), "forearm.L": (-28, 0, 0)})

    # 把所有动作放进 NLA，导出器才会全带上
    arm.animation_data.action = None
    for act in bpy.data.actions:
        track = arm.animation_data.nla_tracks.new()
        track.name = act.name
        strip = track.strips.new(act.name, 1, act)
        strip.name = act.name
        track.mute = False

    # ---------------- 导出 ----------------
    bpy.ops.export_scene.gltf(
        filepath=out_path,
        export_format="GLB",
        use_selection=False,
        export_apply=False,          # 有骨架/修改器时不能 apply
        export_yup=True,
        export_animations=True,
        export_nla_strips=True,
        export_cameras=False,
        export_lights=False,
    )
    print("EXPORTED:", out_path)


main()
