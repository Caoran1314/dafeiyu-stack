# 完整部署手册

从一台空机器，到她能在 QQ 里回你话。全程两条路：**能脚本的给脚本，必须手动的写清楚点哪里、填什么。**

## 目录

| # | 章节 | 大概耗时 |
|---|---|---|
| 1 | [全景图：哪些能脚本，哪些要手动](#1-全景图哪些能脚本哪些要手动) | — |
| 2 | [前置条件](#2-前置条件) | 5 分钟 |
| 3 | [路线 A：一键脚本](#3-路线-a一键脚本) | 10 分钟 |
| 4 | [路线 B：分步手动](#4-路线-b分步手动) | 30 分钟 |
| 5 | [AstrBot 首次配置（手动）](#5-astrbot-首次配置手动) | 10 分钟 |
| 6 | [NapCat 登录 QQ（手动）](#6-napcat-登录-qq手动) | 10 分钟 |
| 7 | [10 个插件的配置](#7-10-个插件的配置) | 15 分钟 |
| 8 | [验收清单](#8-验收清单) | 5 分钟 |
| 9 | [日常运维](#9-日常运维) | — |
| 10 | [排错表](#10-排错表) | — |
| 11 | [卸载与重置](#11-卸载与重置) | — |

---

## 1. 全景图：哪些能脚本，哪些要手动

```
┌─────────────────────────── 能脚本 ───────────────────────────┐
│ install.sh             拉包 + 起容器 + 装插件 + 重启          │
│ install-plugins.sh     复制 10 个插件到 AstrBot               │
│ healthcheck.sh         检查容器 / 端口 / 模型 / ASR           │
│ backup.sh              备份全部状态                           │
└──────────────────────────────────────────────────────────────┘

┌─────────────────────────── 必须手动 ─────────────────────────┐
│ ① 手机 QQ 扫码          浏览器里点，脚本代替不了              │
│ ② 填模型 API Key        涉及你的账号                          │
│ ③ 粘人格 + 关安全模式    网页表单                              │
│ ④ ollama pull bge-m3    一次性下载 1.2 GB                    │
│ ⑤ 下 Vosk 中文模型       2 GB，要选版本                       │
│ ⑥ 准备语音参考音频        要你自己录音                         │
│ ⑦ 逐插件调参             按需，默认值通常够用                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. 前置条件

### 2.1 机器

| 项 | 最低 | 推荐 |
|---|---|---|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8–16 GB（带 Ollama 建议 16 GB） |
| 磁盘 | 10 GB | 20 GB+（含模型） |
| 系统 | Linux（Debian/Ubuntu/fnOS/群晖/CasaOS）或 Windows/Mac 带 Docker Desktop | Linux 服务器 24 小时开机 |

### 2.2 软件

```bash
docker --version            # 需要 20.10+
docker compose version      # 需要 v2（注意是 "docker compose"，不是 "docker-compose"）
```

没装 Docker：

```bash
# Debian / Ubuntu
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER && newgrp docker
```

> fnOS / 群晖 / 威联通：在应用中心装「Docker」即可，不需要命令行安装。

### 2.3 端口

| 端口 | 谁在用 | 能不能改 |
|---|---|---|
| `16185` | AstrBot 面板 | ✅ 改 `.env` 的 `ASTRBOT_WEBUI_PORT` |
| `16099` | NapCat 面板（扫码用） | ✅ 改 `NAPCAT_WEBUI_PORT` |
| `11434` | Ollama（只绑 127.0.0.1） | ✅ 改 `OLLAMA_PORT` |
| `9001` | ASR（只绑 127.0.0.1） | ✅ 改 `ASR_PORT` |
| `9880` | SoVITS（默认不启动） | ✅ 改 `SOVITS_PORT` |

被占用就改 `.env` 左边那一位，右边是容器内端口，别动。

### 2.4 目录

所有持久化数据都在 `DATA_ROOT`（默认 `./data`）：

```
data/
├── astrbot/          AstrBot 数据（插件、记忆库、人格、配置）
├── napcat/config/    NapCat 配置
├── ntqq/             QQ 登录态（扫码后生成）
├── ollama/           向量模型
├── asr/models/       Vosk 中文模型
├── sovits/           GPT-SoVITS（可选）
└── refaudio/         语音参考音频（可选）
```

---

## 3. 路线 A：一键脚本

```bash
curl -fsSL https://raw.githubusercontent.com/Caoran1314/dafeiyu-stack/main/install.sh | bash
```

脚本做的事：

| 步 | 动作 | 失败会怎样 |
|---|---|---|
| 1 | 检查 docker / compose / curl | 直接报错退出 |
| 2 | 下载发行包到 `~/dafeiyu` | 报错退出（检查网络或 REPO 变量） |
| 3 | 生成 `.env` | — |
| 4 | `docker compose config -q` 校验 | 配置写错会立刻提示 |
| 5 | `docker compose up -d`（4 个容器） | 打印最近 20 行日志后退出 |
| 6 | `./scripts/install-plugins.sh` | 提示但继续 |
| 7 | `docker compose restart astrbot` | — |
| 8 | 打印扫码地址与后续步骤 | — |

### 参数

| 变量 | 作用 |
|---|---|
| `DIR=/opt/dafeiyu` | 装到别处 |
| `NO_START=1` | 只装不启动 |
| `REPO=...` | 用 fork 的仓库 |

```bash
DIR=/opt/dafeiyu NO_START=1 bash install.sh
```

### 脚本跑完后，仍需手动做

跳到 [第 5 步 AstrBot 配置](#5-astrbot-首次配置手动) 和 [第 6 步 QQ 登录](#6-napcat-登录-qq手动)。

---

## 4. 路线 B：分步手动

不用脚本就一条条来。**每一步都给验证命令**，验证不通再往下走。

### 4.1 拿文件

```bash
git clone https://github.com/Caoran1314/dafeiyu-stack.git dafeiyu
cd dafeiyu
cp .env.example .env
```

改 `.env`（至少改前两个）：

```ini
DATA_ROOT=./data
NAPCAT_UID=1000          # Linux 填 `id -u` 的结果
NAPCAT_GID=1000          # Linux 填 `id -g` 的结果
MIRROR=docker.io         # 国内拉不动换成 m.daocloud.io/docker.io
```

### 4.2 起 AstrBot（核心）

AstrBot 是本体，其余都是给它用的。

```bash
docker compose up -d astrbot
docker compose logs -f astrbot
```

看到 AstrBot 启动完成、监听 `6185` 即可。

验证：

```bash
curl -I http://127.0.0.1:16185      # 应返回 200/302
```

浏览器打开 `http://<机器IP>:16185`，**首次登录默认账号密码都是 `astrbot`**，进去第一件事就是改密码。

### 4.3 起 NapCat（QQ 协议端）

```bash
docker compose up -d napcat
docker compose logs -f napcat
```

验证：浏览器打开 `http://<机器IP>:16099`，能看到 NapCat 的登录二维码页面。

### 4.4 起 Ollama（向量，可选但强烈建议）

```bash
docker compose up -d ollama
docker exec -it dafeiyu-ollama ollama pull bge-m3
```

验证：

```bash
curl -s http://127.0.0.1:11434/api/tags | head -c 200
```

应能看到 `bge-m3`。

> 不装 Ollama 也能跑：插件会自动降级为纯词法检索，召回精度略低。

### 4.5 起 ASR（语音识别，可选）

```bash
docker compose up -d asr
docker compose logs -f asr
```

**模型要自己下**（2 GB，不进镜像）：

```bash
mkdir -p data/asr/models && cd data/asr/models
curl -LO https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip
unzip vosk-model-cn-0.22.zip
mv vosk-model-cn-0.22 vosk-model-cn
cd -
docker compose restart asr
```

验证：

```bash
curl -s http://127.0.0.1:9001/healthz
# {"ok": true, "model": "vosk-model-cn"}
```

### 4.6 起 SoVITS（语音合成，可选）

**默认不启动**（占位镜像是假的，直接用会报错）。

先准备镜像，在 `.env` 填：

```ini
SOVITS_IMAGE=你的镜像:tag
```

再启动：

```bash
docker compose --profile voice up -d sovits
```

**参考音频要自己录**（5–10 秒干净人声）：

```
data/refaudio/
├── 平静/ref.wav + asr.txt
├── 高兴/ref.wav + asr.txt
├── 害羞/ref.wav + asr.txt
├── 生气/ref.wav + asr.txt
└── 着急/ref.wav + asr.txt
```

`asr.txt` 里写这段音频**说了什么字**，必须完全一致。

验证：

```bash
curl -s http://127.0.0.1:9880/ | head -c 120
```

### 4.7 装插件（脚本）

```bash
./scripts/install-plugins.sh
docker compose restart astrbot
```

验证：面板 → 插件，应看到 10 个 `dafeiyu_*`。

---

## 5. AstrBot 首次配置（手动）

打开 `http://<机器IP>:16185` → 登录（`astrbot` / `astrbot`）。

### 5.1 改密码

系统设置 → 账号 → 修改密码。**先做这一步**。

### 5.2 配模型提供商

配置 → 模型提供商 → 新增：

| 字段 | 填什么 |
|---|---|
| 类型 | `OpenAI 兼容`（DeepSeek/通义/智谱都选这个） |
| API Base | DeepSeek：`https://api.deepseek.com/v1`<br>智谱：`https://open.bigmodel.cn/api/paas/v4` |
| API Key | 你的 key |
| 模型 | DeepSeek：`deepseek-chat` |

保存后点「设为默认」。

验证：配置页有「测试」按钮，点一下应返回回复。

### 5.3 接 NapCat

配置 → 平台适配器 → `aiocqhttp`：

| 字段 | 值 |
|---|---|
| 启用 | ✅ |
| host | `0.0.0.0` |
| port | `6199` |
| token | 留空，或与 NapCat 填一致 |

> AstrBot 开的是 **WebSocket 服务端**，NapCat 作为客户端连过来。

### 5.4 人格设定

配置 → 人格设定 → 新建：

1. 把 `persona/persona_lover.md` 全文粘进去
2. **关闭安全模式**

```json
"agent_runner": { "config": { "persona": { "safety_mode": false } } }
```

> 开着安全模式，她会频繁说「我不能……」人设直接崩。这是最常见的翻车点。

### 5.5 设管理员

配置 → 基本设置 → 管理员 QQ → 填你的 QQ 号。

没有这步，`/心智状态` 之类的管理命令会被忽略。

---

## 6. NapCat 登录 QQ（手动）

打开 `http://<机器IP>:16099`。

### 6.1 扫码

1. 手机上打开 QQ → 设置 → 账号安全 → 扫一扫
2. 扫页面上的二维码
3. 确认登录

> **用小号。** 有封号风险，别用主号。

### 6.2 配 OneBot 连接

NapCat 页面 → 网络配置 → 添加 **WebSocket 客户端**：

| 字段 | 值 |
|---|---|
| URL | `ws://astrbot:6199/ws` |
| Token | 留空，或与 AstrBot 里填的一致 |
| 心跳 | 默认即可 |

`astrbot` 是 compose 里的服务名，容器之间可以直接用。

保存后验证：AstrBot 面板 → 平台适配器，`aiocqhttp` 状态应变成**已连接**。

### 6.3 测试收发

用另一个号给小号发一条消息，看 AstrBot 日志：

```bash
docker compose logs -f astrbot | grep -i message
```

有日志即通。

---

## 7. 10 个插件的配置

装完不用立刻调。下表说明**哪些必须改、哪些默认就行**。

### 7.1 必须一起启用的三个

| 插件 | 关键配置 | 说明 |
|---|---|---|
| `dafeiyu_mindcore` | `inject_mode=primary` | 唯一注入点，负责装配 |
| `dafeiyu_hormone` | `inject=false` | 只算状态，不抢注入 |
| `dafeiyu_persona_core` | `inject=false` | 同上 |

**改法**：面板 → 插件 → 点插件卡片的齿轮 → 改 → 保存 → 重载。

三者都启用、两个 `inject=false` 之后，一行日志就能确认：

```bash
docker compose logs astrbot | grep 心智装配
# [dafeiyu_mindcore] 心智装配 248 字，记忆 4 条
```

### 7.2 逐插件配置表

| 插件 | 必改 | 默认值可用？ |
|---|---|---|
| `dafeiyu_mindcore` | `embedding_api_base` 默认 `http://ollama:11434/v1` | ✅ 用我们的 compose 就直接跑 |
| `dafeiyu_hormone` | 无 | ✅ |
| `dafeiyu_persona_core` | 无 | ✅（`delta_mode=heuristic`，省钱） |
| `dafeiyu_human` | 无 | ✅ |
| `dafeiyu_brain` | `owner_qq` 填你的 QQ（主人记忆加权 1.8 倍） | ⚠️ 必须填 |
| `dafeiyu_voice` | `enable=true` 且 `api_base=http://sovits:9880` | ⚠️ 默认关，要手动开 |
| `dafeiyu_photo` | `enable=true` | ⚠️ 默认关 |
| `dafeiyu_brain3d` | 无 | ✅ 页面直接开 |
| `dafeiyu_room` | 无 | ✅ |
| `dafeiyu_eval` | 无（只观测） | ✅ |

### 7.3 如果 Ollama 不在同一台机器

改 `dafeiyu_mindcore` 和 `dafeiyu_brain` 的 `embedding_api_base`：

| 你的环境 | 填什么 |
|---|---|
| 同一个 compose | `http://ollama:11434/v1`（默认） |
| Docker Desktop（Win/Mac） | `http://host.docker.internal:11434/v1` |
| Linux 宿主机上跑的 Ollama | `http://172.17.0.1:11434/v1` |
| 另一台机器 | `http://192.168.x.x:11434/v1` |

---

## 8. 验收清单

按顺序打勾，每一条都能独立验证。

### 8.1 容器层

```bash
docker compose ps          # 4 个 Up（+ sovits 若启用）
./scripts/healthcheck.sh   # 端口/模型/ASR 一口气检查
```

### 8.2 接口层

```bash
curl -I http://127.0.0.1:16185                 # AstrBot 面板
curl -s http://127.0.0.1:11434/api/tags         # Ollama
curl -s http://127.0.0.1:9001/healthz           # ASR（若启用）
```

### 8.3 连接层

AstrBot 面板 → 平台适配器 → `aiocqhttp` 显示**已连接**。

### 8.4 插件层

AstrBot 面板 → 插件 → 10 个 `dafeiyu_*` 都是启用状态。

### 8.5 聊天层

QQ 里发：

```
/心智状态
```

正常输出：

```
记忆 218 条（short/mid/long = 15/153/50）
心境 血清素 0.61 多巴胺 0.41 皮质醇 0.19 催产素 0.53
人格 温柔 0.47 粘人 0.60 直率 0.74 敏感 0.84
技能 3 项｜召回加权 f_endo 0.99
```

有这四行就算全部通了。

### 8.6 人格层

随便聊几句，确认：

- 她**不是**一堆分点、不是「作为一个 AI」
- 她会用短句、会分行
- 心情差的时候回得更短

不对就回 [第 5.4 节](#54-人格设定) 检查 `safety_mode`。

---

## 9. 日常运维

### 9.1 备份

```bash
./scripts/backup.sh
# 或手动
tar czf backup-$(date +%F).tgz data/astrbot/plugin_data data/astrbot/data_v4.db
```

QQ 里也能打包她的内部状态：

```
/生命卡 导出
```

### 9.2 升级

```bash
docker compose pull            # 拉新镜像
docker compose up -d
./scripts/install-plugins.sh   # 更新插件
docker compose restart astrbot
```

升级前先备份。

### 9.3 看日志

```bash
docker compose logs -f astrbot          # 全部
docker compose logs astrbot | grep 心智   # 只看心智层
docker compose logs --tail=100 asr       # ASR 最近 100 行
```

### 9.4 只重启单个服务

```bash
docker compose restart astrbot
docker compose restart napcat
```

### 9.5 数据在哪

| 数据 | 路径 |
|---|---|
| 记忆库（旧） | `data/astrbot/plugin_data/dafeiyu_brain/memory.db` |
| 心智库 | `data/astrbot/plugin_data/dafeiyu_mindcore/memory_core.db` |
| 心境 | `data/astrbot/plugin_data/dafeiyu_hormone/hormones.json` |
| 人格 | `data/astrbot/plugin_data/dafeiyu_persona_core/persona_core.json` |
| 生命卡 | `data/astrbot/plugin_data/dafeiyu_mindcore/*.lifecard` |
| AstrBot 主库 | `data/astrbot/data_v4.db` |

---

## 10. 排错表

| 症状 | 原因 | 处理 |
|---|---|---|
| `docker compose up` 报 `pull access denied` | 镜像源或镜像名不对 | 改 `.env` 的 `MIRROR=m.daocloud.io/docker.io` |
| 面板打不开 | 端口冲突 / 没起来 | `docker compose ps` 看状态，`logs` 看报错 |
| 扫码后 QQ 立刻掉线 | 小号风控 | 换网络、隔几小时再扫 |
| AstrBot 显示未连接 | NapCat 的 WS 地址写错 | 用 `ws://astrbot:6199/ws`，不是 `localhost` |
| 她回「我不能…」 | 安全模式没关 | 设 `safety_mode=false` |
| 记忆一直是 0 | 没聊够 / 没开注入 | 聊 4–5 句；看 `memory_inject` |
| 日志刷 `Connection refused :11434` | Ollama 没起或地址错 | 关 `embedding_enable` 或改地址 |
| 3D 页面白屏 | 页面 token 7 天过期 | 从侧边栏重进 |
| 语音没声音 | SoVITS 没起 / 参考音频缺失 | `logs sovits`；检查 `data/refaudio` |
| ASR 不识别 | 模型没下 | 下 `vosk-model-cn` 到 `data/asr/models` |
| 插件列表里没有 `dafeiyu_*` | 复制路径不对 | `ls data/astrbot/plugins` 应该有 10 个目录 |
| 主动消息发不出，日志 `cannot find platform` | 会话 ID 前缀写成了 `aiocqhttp` | 用平台实例 ID：`napcat:FriendMessage:<QQ>` |
| 她发了图却答不上图里是什么 | AstrBot 只给「收到的图」做描述，不给「自己发的图」做描述 | 插件主动发图时，自己先调视觉模型把描述写进配文 |
| 中文变乱码 | 系统 locale | `docker compose exec astrbot locale` 应为 UTF-8 |

---

## 11. 卸载与重置

### 11.1 只重置数据（保留容器）

```bash
docker compose down
rm -rf data/astrbot/plugin_data
docker compose up -d
```

她会变回全新状态（记忆、心境、人格全部归零）。

### 11.2 只换 QQ 号

```bash
docker compose down
rm -rf data/ntqq
docker compose up -d napcat
# 重新打开 :16099 扫码
```

数据不丢。

### 11.3 完全卸载

```bash
docker compose --profile voice down -v
rm -rf data
docker rmi $(docker images | grep -E "astrbot|napcat|dafeiyu" | awk '{print $3}')
```

⚠️ 这会删掉全部记忆。删之前先 `./scripts/backup.sh`。

---

## 附：文件结构

```
dafeiyu-stack/
├── docker-compose.yml    5 个服务（sovits 在 voice profile）
├── .env.example          端口 / 数据目录 / 用户 ID
├── install.sh            一键部署
├── plugins/              10 个插件源码
├── plugin-source/        自定义插件源（plugins.json + zips）
├── persona/              人格正文 + 人生年表
├── asr/                  Vosk 识别服务
├── scripts/
│   ├── install-plugins.sh
│   ├── healthcheck.sh
│   ├── backup.sh
└── docs/
    ├── DEPLOY.md         ← 就是这个文件
    ├── ARCHITECTURE.md
    ├── PLUGINS.md
    ├── MARKET-INSTALL.md
    └── FAQ.md
```
