# 官方市场提交清单

提交地址：https://cloud.astrbot.app/publish

> 限制：**滚动 24 小时最多 3 次**。10 个插件需要 4 天。

## 提交顺序

| # | 仓库（直接复制） | 展示名 | 版本 | 卡片短描述 |
|---|---|---|---|---|
| 1 | `Caoran1314/dafeiyu_mindcore` | 大肥鱼心智内核 | 0.1.0 | 会遗忘、会晋升、会熟练的记忆库，带向量召回与技能 SM2 |
| 2 | `Caoran1314/dafeiyu_hormone` | 大肥鱼心境 | 0.1.0 | 四激素心境引擎，情绪随时间回归、被对话扰动 |
| 3 | `Caoran1314/dafeiyu_persona_core` | 大肥鱼人格内核 | 0.1.0 | 人格向量单轮钳位，聊再久人设也不会被改写 |
| 4 | `Caoran1314/dafeiyu_human` | 大肥鱼拟人管线 | 0.1.0 | 去 AI 腔、一句一行、偶尔错字，让她像人在打字 |
| 5 | `Caoran1314/dafeiyu_brain` | 大肥鱼记忆大脑 | 0.1.0 | 本地 SQLite 长期记忆，混合召回 + 人格锚点，不依赖云服务 |
| 6 | `Caoran1314/dafeiyu_brain3d` | 大肥鱼3D记忆脑 | 0.1.0 | 把记忆画成 3D 皮层脑，附一条从出生到今天的时间线 |
| 7 | `Caoran1314/dafeiyu_eval` | 大肥鱼拟人度评测 | 0.1.0 | 拟人度测评，只看不改：字数、分条、AI 腔、标点、延迟 |
| 8 | `Caoran1314/dafeiyu_photo` | 大肥鱼相册 | 0.1.0 | 记住你发的照片，聊到相关话题时主动发出来 |
| 9 | `Caoran1314/dafeiyu_room` | 大肥鱼房间 | 0.1.0 | 3D 房间：睡觉、刷手机、电脑前、窗边发呆，状态随手变 |
| 10 | `Caoran1314/dafeiyu_voice` | 大肥鱼音色 | 0.1.0 | GPT-SoVITS 本地克隆音色，只替换 TTS 这一步 |

## 每天提交 3 个

| 天 | 提交 |
|---|---|
| 第 1 天 | mindcore · hormone · persona_core |
| 第 2 天 | human · brain · brain3d |
| 第 3 天 | eval · photo · room |
| 第 4 天 | voice |

## 表单里可能要填的

| 字段 | 值 |
|---|---|
| 作者 | `Caoran1314` |
| 分类 | `AI 增强`（brain3d/room 选 `工具`）|
| 支持平台 | `aiocqhttp`、`webchat` |
| AstrBot 版本 | `>=4.24.0` |
| 开源许可 | MIT |

## 如果被退回

| 退回理由 | 怎么改 |
|---|---|
| 体积超 16MB | 检查 brain3d（478KB）、room（461KB），都远小于限制，可忽略 |
| 元数据不完整 | 对照 `metadata.yaml` 补齐 name/display_name/desc/version/author/repo |
| 仓库不是插件根 | 确认选的是 `dafeiyu_xxx` 而不是 `dafeiyu-stack` |
| 功能不明确 | 补 README 截图与使用说明 |
| 依赖缺失 | 本套插件无第三方依赖，可回复说明只用标准库 + AstrBot SDK |

## 审核期间别人怎么装

自定义源已经能用，不用等审核：

```
https://cdn.jsdelivr.net/gh/Caoran1314/dafeiyu-stack@main/plugin-source/plugins.json
```

或者在 AstrBot 里直接填：`Caoran1314/dafeiyu-stack/plugins/<插件名>`
