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


## 人物：优先用 VRM

页面会先尝试 `model/character.vrm`（VRM 模型），失败才退回 `character.glb`，再退回内置小人。

| 项 | 说明 |
|---|---|
| 加载器 | `three/vrm/three-vrm.module.min.js`（已内置，不依赖外网） |
| 缩放 | 自动缩放到 1.55 m 身高 |
| 朝向 | VRM 默认朝 -Z，代码里已转成 +Z |
| 动作 | 用归一化骨骼驱动（idle/walk/sit/lie/sleep/pet），不依赖模型自带动画 |

### 授权提醒

VRM 模型多数不允许二次分发。`.vrm` 已加入 `.gitignore`，不随仓库和插件包分发；
每个部署者需要自己准备模型。示例：BOOTH 上的「Big Fat Blue Fish」（CC BY-NC-SA 4.0，仅非商用）。


## 已知问题：自定义着色器材质

「Big Fat Blue Fish」是从 Warudo 转出来的 VRM，材质是**自定义 ShaderMaterial（liltoon 烘焙）**，
不是标准 MToon。three.js 加载后会出现：

- 头部像银色金属碗（头饰材质不对）
- 头发/身体偏平
- 模型自带一块版权说明牌

**下一步做法**（待办）：

1. 遍历所有 mesh，把材质重建为 `MeshToonMaterial`，贴图沿用原来的 `map`
2. 版权牌按包围盒位置判断隐藏（在头顶上方、且不是蒙皮网格）
3. 朝向再校一次（现在背对镜头）
4. 按房间给每个锚点单独调机位


## VRM → 网页可用 glb（转换流程）

模型直接用 `.vrm` 在网页里会出问题（自定义着色器、烘焙脸、自带说明牌）。
正确做法是先在 Blender 里转换，再导出普通 glb：

```bash
# 1. 装 VRM 扩展（一次性）
blender --command extension install-file -r user_default -e VRM_Addon_for_Blender-4_10_3.zip

# 2. 转换
blender --background --python tools/blender/convert_vrm_to_glb.py   -- --vrm model/character.vrm --out model/character.glb
```

`convert_vrm_to_glb.py` 做的事：

1. 用 VRM 扩展导入
2. 删除头顶上方的版权说明板
3. 材质 MToon → Principled BSDF（保留颜色贴图、透明度）
4. 落地到 z=0
5. 导出 glb（不带相机灯光）

### 还没解决的

- 部分配件材质（帽子/尾巴）仍偏金属——转换要覆盖所有 slot，含未使用的材质
- glb 没有动画剪辑，网页需要按骨骼名驱动姿势（当前只对 VRM 生效）
- 镜头距离按模型尺寸再校准


## 最终方案（2026-11-03 验证）

**直接用 `.vrm`，不做 glb 转换。**

| 原因 | 说明 |
|---|---|
| glb 导出会丢 MToon | Blender 导出后脸部/头发材质全坏 |
| three-vrm 原生支持 MToon | 加载 .vrm 才是正确路径 |

网页里做的三件事：

1. `three-vrm` 加载 `model/character.vrm`
2. 隐藏 `VEE_EmoteAtlas`（脸部叠加面片 + 版权牌）与 `MToon Outline` 描边壳
3. 把 `ShaderMaterial` 重建为带贴图的卡通材质（模型是 Warudo 转的，材质不是标准 MToon）
4. 用**归一化骨骼**摆姿势（`humanoid.getNormalizedBoneNode`），再 `humanoid.update()`

### 踩过的关键坑

| 现象 | 原因 | 解法 |
|---|---|---|
| 脸是黑红块 | `VEE_EmoteAtlas` 叠加面片 | 隐藏该网格 |
| 头顶金属碗 | 草帽/配件 + 描边壳 | 按名字+材质名过滤 |
| 悬空、只剩头 | 坐姿高度没生效（分支里覆盖了 y） | 高度统一在函数末尾设置 |
| 手臂一直 T-pose | 改的是原始骨骼，`humanoid.update()` 会覆盖 | 改归一化骨骼 |


## 动作库（2026-11-03）

页面里定义在 `ACT`（`index.html`），共 15 个动作：

| 动作 | 触发场景 |
|---|---|
| `idle` | 默认待机（呼吸 + 轻微张望） |
| `walk` | 走路（手臂前后摆） |
| `sit` | 坐沙发/电竞椅 |
| `lie` / `sleep` | 躺床 / 睡觉 |
| `pet` | 蹲下撸猫 |
| `stretch` | 伸懒腰（随机） |
| `yawn` | 打哈欠（随机） |
| `wave` | 招手（随机） |
| `phone` | 看手机（随机 / 床上） |
| `hair` | 理头发（梳妆台） |
| `look` | 窗边张望 |
| `read` | 看书 |
| `typing` | 电脑前打字 |
| `dance` | 跳舞（随机） |
| `yoga` | 瑜伽（地毯） |

随机小动作：非走路状态下每 5–13 秒随机插一个，持续 2.5–4.5 秒。

### 关键实现：几何朝向

**不要用欧拉角猜轴**。这个模型的骨骼轴向不标准，`rotation.z = -1.48` 可能让手臂转向上方。

正确做法是算四元数，让骨骼指向世界方向：

```js
aimBone('armL', 'foreL', new THREE.Vector3(0.10, -1, 0.02));  // 手臂指向下方
```

`aimBone(bone, child, dir)` 取骨-子骨的世界向量，与目标方向求 `setFromUnitVectors`，
再转到父空间乘上去。和模型绑定姿势无关，稳妥。

### 调试钩子

| 钩子 | 作用 |
|---|---|
| `window.__bones()` | 打印所有骨骼世界坐标（验证姿势方向） |
| `window.__do('stretch')` | 强制播放某个动作 |
| `window.__setCam(px,py,pz,tx,ty,tz)` | 指定机位 |
| `window.__model()` / `__cam()` | 模型与相机状态 |


## 整个房间用 Blender 建模（2026-11-03）

`tools/blender/build_apartment.py` 生成完整公寓：墙、门洞、过梁、踢脚线、以及全部家具。

```bash
blender --background --python build_apartment.py -- --out .../model/room.glb
```

| 内容 | 说明 |
|---|---|
| 尺寸 | 12 × 12 m，层高 2.8 m |
| 分区 | 客厅 49㎡ / 主卧 25㎡ / 电竞房 20㎡ / 猫房 25㎡ / 玄关 10㎡ |
| 门洞 | 四处，带过梁（2.1 m 高） |
| 家具 | 沙发、电视柜、茶几、餐桌椅、开放厨房、书架、落地灯、绿植、床、床头柜、衣柜、梳妆台+镜子、电脑桌、双显示器、电竞椅、机箱、置物架、海报、猫爬架×2、猫窝×2、猫砂盆、食盆、抓板、鞋柜 |
| 坐标约定 | Blender `y = -网页z`，导出 +Y 向上后与页面锚点完全对齐 |
| 体积 | 约 750 KB |

页面加载 `room.glb` 后会隐藏代码生成的全部家具（保留灯光、猫、人物）。

### 注意

- 天花板**不导出**，否则俯视会被挡住
- 家具材质用纯色 Principled BSDF，网页里直接可用


## 墙面分色与精致化细节

`build_apartment.py` 里的配色方案：

| 区域 | 墙面 | 地面 |
|---|---|---|
| 客厅 | 暖白 + 电视背景墙（陶土色） | 浅灰瓷砖 |
| 主卧 | 奶油色 + 床头背景墙 | 木地板 |
| 电竞房 | 浅灰 + 深蓝灰背景墙 | 木地板 |
| 猫房 | 鼠尾草绿隔断 | 浅米地板 |
| 玄关 | 暖白 + 挂画 | 木地板 |

细节件：

- 门套（四处门洞）
- 四个房间吊灯（餐桌上另有一盏）
- 主卧窗帘 + 窗帘杆
- 墙面挂画（客厅 2 幅、主卧 1 幅、电竞房 1 幅）
- 沙发腿、坐垫分色、抱枕、盖毯
- 电视音响、机顶盒
- 床品分层（软包床头、被子、折毯）、闹钟、小夜灯、拖鞋
- 电竞房桌垫、RGB 灯带、耳机
- 猫房墙面跳台、抓柱、玩具球、猫垫
- 玄关换鞋凳、地垫

改配色：直接改脚本顶部的 `M_WALL_*` / `M_FLOOR_*` 颜色值，重新导出即可。


## 电影感渲染管线（页面侧）

| 环节 | 做法 |
|---|---|
| 色调映射 | `ACESFilmicToneMapping`，曝光 1.0 |
| 环境反射 | `RoomEnvironment` + `PMREMGenerator`，强度 0.10 |
| 阴影 | `PCFSoftShadowMap` |
| 泛光 | `UnrealBloomPass`（强度 0.09，阈值 0.95） |
| 调色 | 自定义 `GradeShader`：暗角、对比度 1.06、饱和度 1.04、暖色偏移、胶片颗粒 0.018 |
| 灯光 | 各房间暖光 + 卫生间冷光 + 电视冷光，强度按 ACES 重新标定 |
| 材质 | 贴图 + 法线贴图（木/布/石/墙）+ 粗糙度贴图 |

**调参位置**：`index.html` 里 `toneMappingExposure`、`addMoodLight(...)`、`GradeShader.uniforms`、`UnrealBloomPass` 参数。

### 过曝排查经验

ACES 会压暗高光但也会让整体变亮，原来给无 ACES 调的灯光（半球光 1.05、环境光 0.65、
点光 6~7）在 ACES 下会全白。对应的修正值：半球 0.30、环境 0.14、点光 1~2、
环境贴图强度 0.10，曝光 1.0。

### 画质糊 / 噪点

- `EffectComposer` 必须在创建后立刻 `setSize(window.innerWidth, window.innerHeight)`，
  否则会以默认小尺寸渲染再放大 → 满屏马赛克
- 胶片颗粒不要超过 0.02，否则像噪点


## 三室两厅 14 × 15 m（≈210㎡）

脚本：`tools/blender/build_3b2h.py`

| 房间 | 尺寸 | 面积 |
|---|---|---|
| 客厅 | 7.5 × 7 | 52㎡ |
| 餐厅 | 7.5 × 3 | 22㎡ |
| 厨房 | 4.5 × 2.5 | 11㎡ |
| 玄关 | 3 × 2.5 | 7.5㎡ |
| 主卧 | 6.5 × 6 | 39㎡ |
| 主卫 | 3 × 2.3 | 7㎡ |
| 衣帽间 | 3.5 × 2.3 | 8㎡ |
| 次卧 A | 3.25 × 3 | 10㎡ |
| 次卧 B | 3.4 × 3 | 10㎡ |
| 走廊 | 6.5 × 1.2 | 8㎡ |
| 阳台 | 7.5 × 2.5 | 19㎡ |

页面锚点、猫点、行走夹紧范围、房间暖光都按新坐标重写：
`ANCHOR` / `CAT_SPOTS` / `ROOM_RECTS` / `addMoodLight(...)`。

### 户型迭代记录

1. 12×12 四区（客厅/主卧/电竞/猫房）→ 房间偏小
2. 尝试验收 205㎡ 四房图纸（build_plan205.py）→ 房间过多过碎
3. **当前：14×15 三室两厅**，房间普遍放大，客厅 52㎡、主卧 39㎡
