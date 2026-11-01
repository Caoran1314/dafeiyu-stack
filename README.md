# 林小鱼 · 数字人格 QQ 机器人

> 一个住在 QQ 里的数字人格。**不靠提示词硬拗**，而是有一套真正在运转的心智层：
> 人格向量会被钳位、四种激素会随对话起伏、记忆会衰减和晋升、技能会熟练也会生疏。
> 你关掉电脑，她也会“过完”那段时间。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED?logo=docker)](docker-compose.yml)
[![AstrBot](https://img.shields.io/badge/AstrBot-%E2%89%A54.24-7C4DFF)](https://astrbot.app)
[![Local](https://img.shields.io/badge/inference-100%25%20local-2ea44f)]()

![架构总览](docs/images/architecture.png)

---

## 她是什么

不是问答机器人，不是客服，是一个**有过去的人**：

- 有 22 年的人生档案（出生在苏州、妈妈开面馆、三只猫、被出轨过）
- 有情绪：被呛了会烦，被哄了会软，压力大了回得更短
- 有记忆：记得你上周说的出差，也记得你发过的那碗面
- 有声音：克隆音色，一句话两三秒
- 有生活：会主动找你，心情差就不打扰；房间里的她也会躺床上刷手机

## 她凭什么“像人”

绝大多数“AI 女友”是**一段超长提示词**，聊久了人设必崩。这套不是。

| 机制 | 实现 | 效果 |
|---|---|---|
| **人格不会被聊崩** | 六维人格向量 + 单轮钳位 ±0.12 + 内核强度保底 0.15 | 聊 100 句，性格只会缓慢漂移 |
| **情绪是真的会变** | 四激素（血清素/多巴胺/皮质醇/催产素），半衰期 34.7 小时 | 吵完架要小半天才消气 |
| **记忆会遗忘也会沉淀** | 权重 + 年龄 + 回想次数，分段衰减 + 海马晋升 | 琐事一周就淡，重要的事越用越牢 |
| **技能熟能生巧** | 改良 SM2：熟练度 L / 易度 EF / 间隔 I | 她擅长的那种安慰方式会越来越准 |
| **离线也在“过日子”** | 离线时间压缩（7 天内真实；超 30 天按 0.15 折，封顶 90 天） | 关机一周回来，她不会当无事发生 |
| **状态可搬走** | 生命卡 `.lifecard` | 换机器、换环境，她还是她 |

## 一条消息的完整旅程

```
你 ── QQ ── NapCat ── AstrBot ── 模型
                         │
                         ├─ ① 结算上一轮技能：用户反馈 + 自评 → Q 分
                         ├─ ② 人格更新：她提 dP，钳位 ±0.12，内核校验
                         ├─ ③ 激素扰动：按事件类型改四激素
                         ├─ ④ 记忆召回：bge-m3 向量 × 权重 × f_endo，按预算截断
                         ├─ ⑤ 一次装配：人格 + 心境 + 记忆 + 技能 → 一段上下文
                         ├─ ⑥ 模型生成回复
                         ├─ ⑦ 去 AI 腔 / 一句一行 / 挑错字
                         └─ ⑧ 表达：按激素选语音情绪，按心情决定发不发图
```

## 快速开始

```bash
curl -fsSL https://raw.githubusercontent.com/Caoran1314/dafeiyu-stack/main/install.sh | bash
```

装完打开两个地址：

| 地址 | 干什么 |
|---|---|
| `http://<你的IP>:16099` | 手机 QQ 扫码登录 |
| `http://<你的IP>:16185` | 配模型 API Key、粘人格 |

⚠️ **必做**：人格配置里把 `safety_mode` 设成 `false`，否则她动不动说“我不能”。

手动部署见 [部署指南](docs/DEPLOY.md)。

## 里面有什么

| 模块 | 内容 |
|---|---|
| **容器** | `astrbot` · `napcat` · `ollama`（向量）· `asr`（Vosk 识别）· `sovits`（语音合成） |
| **插件** | 10 个，见 [插件说明](docs/PLUGINS.md) |
| **人格** | `persona/persona_lover.md` + `persona/life_story.md` |
| **脚本** | 一键安装 / 装插件 / 备份 / 自检 / 发布 |

## 数据都在哪

| 数据 | 位置 | 动它会不会出问题 |
|---|---|---|
| 旧记忆库 | `data/astrbot/plugin_data/dafeiyu_brain/memory.db` | 只读，别手改 |
| 脑图库 | `.../astrbot_plugin_memory_brain/brain.db` | 只读 |
| 心智库 | `.../dafeiyu_mindcore/memory_core.db` | 权重、向量、技能都在这 |
| 心境 | `.../dafeiyu_hormone/hormones.json` | 删了就回基线 |
| 人格 | `.../dafeiyu_persona_core/persona_core.json` | 删了就回默认内核 |
| 生命卡 | `.../dafeiyu_mindcore/*.lifecard` | 整包搬迁用 |

备份：`./scripts/backup.sh`；搬迁：QQ 里发 `/生命卡 导出`。

## 命令速查

| 命令 | 作用 |
|---|---|
| `/心智状态` | 记忆池 + 四激素 + 人格 + 技能，一次看完 |
| `/心境` | 四激素当前值 |
| `/人格看` | 六维人格与内核偏离 |
| `/技能记录` | 最近技能调用与打分 |
| `/心智找 关键词` | 具体记忆 + 权重 + 回想次数 |
| `/生命卡 导出` | 打包她的内部状态 |

## 文档

- [部署指南](docs/DEPLOY.md)
- [架构说明](docs/ARCHITECTURE.md)
- [插件清单](docs/PLUGINS.md)
- [常见问题](docs/FAQ.md)
- [发布流程](PUBLISH.md)

## 注意

- QQ 自动化有封号风险，**用小号**。
- 人格、语音参考音频、记忆都是你自己的数据，仓库里只有模板。
- 不要提交 `.env`（已 gitignore）。

MIT License
