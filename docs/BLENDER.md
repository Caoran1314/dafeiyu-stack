# 用 Blender 做模型

房间和人物都走 Blender，脚本在 `tools/blender/`。

## 环境

| 项 | 值 |
|---|---|
| Blender | 4.5.9 LTS 完整版 |
| 路径 | `C:\Users\<你>\AppData\Local\Programs\Blender Foundation\Blender 4.5\blender.exe` |
| 安装方式 | 官方 MSI，按用户安装（不需要管理员） |

## 三个脚本

| 脚本 | 作用 | 输出 |
|---|---|---|
| `build_room.py` | 生成房型骨架（地板/墙/门洞/踢脚线） | `plugins/dafeiyu_room/pages/room/model/room.glb` |
| `build_character.py` | 生成蓝发鲸鱼女仆（骨架 + 8 个动作） | 同上目录 `character.glb` |
| `render_preview.py` | 把模型渲染成图，方便检查 | `tools/blender/_preview/*.png` |

一键重新生成房型：双击 `export_room.bat`。

## 命令行

```bash
BL="$LOCALAPPDATA/Programs/Blender Foundation/Blender 4.5/blender.exe"

# 房型
"$BL" --background --python build_room.py -- --out .../model/room.glb

# 人物
"$BL" --background --python build_character.py -- --out .../model/character.glb

# 预览图
"$BL" --background --python render_preview.py
```

`--background` 表示无界面运行，不需要打开 Blender。

## 页面怎么用这些模型

- **房型**：页面优先加载 `model/room.glb`，成功就隐藏代码生成的墙地；没有就回退
- **人物**：加载 `model/character.glb` 后，自动隐藏程序化小人，改用模型 + 骨骼动画

动作名要包含这些关键字，页面会自动匹配：

| 场景 | 动画名 |
|---|---|
| 待机 | `idle` |
| 走路 | `walk` |
| 坐（沙发/电竞椅） | `sit` / `tv` |
| 躺床上 | `lie` / `phone` |
| 睡觉 | `sleep` |
| 撸猫蹲下 | `pet` |

## 建模规范（自己建模时照这个来）

| 项 | 要求 |
|---|---|
| 单位 | 米 |
| 身高 | 约 1.45 m |
| 原点 | 脚底中心 |
| 朝向 | Blender 里朝 **-Y**（导出后在 three.js 里面向 +Z） |
| 骨骼 | 至少 root/hips/spine/chest/neck/head + 四肢 |
| 蒙皮 | 刚性权重即可（每个部件绑一根骨），避免自动权重失败 |
| 动画 | 每个动作一个 Action，推进 NLA 轨道，导出时勾选 NLA |
| 导出 | glTF 2.0（.glb），+Y 向上，不导出相机/灯光 |
| 体积 | 单个 glb 建议 < 8 MB（插件包上限 16 MB） |

## 已知问题

- 坐姿/躺姿的骨骼位移是**脚本里写死的根骨位移**，和家具高度不一定对齐，需要按家具再调
- 刚性蒙皮在关节处会有硬折角，想要平滑得用权重绘制
- 人物目前是脚本拼的占位模型，五官和头发是球体组合

## 后续

1. 在 Blender 里手工精修人物（发型、脸、裙子），保留同名骨骼和动作
2. 用真实贴图代替纯色材质（`Principled BSDF` + 图片贴图）
3. 房型导出时带上家具（现在是代码家具 + Blender 墙地混搭）
