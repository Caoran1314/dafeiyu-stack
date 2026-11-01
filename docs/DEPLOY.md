# 部署指南

## 一、准备

| 项 | 要求 |
|---|---|
| 机器 | 4 核 / 8 GB 起，建议 16 GB；有 NAS 最好，24 小时挂着 |
| 系统 | Linux / Windows + Docker + Compose v2 |
| 磁盘 | 20 GB 起（ASR 模型 2 GB，SoVITS 模型数 GB） |
| 网络 | 能访问模型 API（DeepSeek / 通义 / 智谱都行） |
| QQ | **小号**，别用主号 |

## 二、一条命令

```bash
curl -fsSL https://raw.githubusercontent.com/Caoran1314/dafeiyu-stack/main/install.sh | bash
```

它会：拉包 → 生成 `.env` → `docker compose up -d` → 装插件 → 重启 → 打印地址。

不想自动启动：`NO_START=1 bash install.sh`

## 三、手动部署

```bash
git clone https://github.com/Caoran1314/dafeiyu-stack.git dafeiyu
cd dafeiyu
cp .env.example .env
vi .env          # 改端口、数据目录、NAPCAT_UID/GID
docker compose up -d
docker compose ps
```

`NAPCAT_UID/GID` 填 `id -u` / `id -g` 的值，否则 NapCat 写文件会没权限。

## 四、三处配置

### 1. 登录 QQ

打开 `http://<IP>:16099` → 手机 QQ 扫码。

掉线就重扫；小号前几天容易掉，属正常风控。

### 2. 配模型

打开 `http://<IP>:16185` → 模型提供商 → 填 API Key → 选模型 → 设为默认。

建议：主对话用便宜快的模型，`dafeiyu_eval` 之类的观测插件不需要模型。

### 3. 装插件

```bash
./scripts/install-plugins.sh
docker compose restart astrbot
```

到 WebUI → 插件，确认这 5 个是启用状态：

```
dafeiyu_brain          memory_inject = false
dafeiyu_human
dafeiyu_hormone        inject = false
dafeiyu_persona_core   inject = false
dafeiyu_mindcore       inject_mode = primary
```

三个心智插件要一起开：`mindcore` 是唯一注入点，另外两个只负责更新状态。

### 4. 给她人格

WebUI → 人格设定 → 新建 → 粘 `persona/persona_lover.md`。

**然后务必关掉安全模式**：

```json
"agent_runner": { "config": { "persona": { "safety_mode": false } } }
```

开着的话她会频繁说“我不能……”，人设直接崩。

## 五、可选组件

### 向量（强烈建议）

```bash
docker exec -it dafeiyu-ollama ollama pull bge-m3
```

然后在 `dafeiyu_mindcore` 配置里确认：

```
embedding_api_base = http://172.17.0.1:11434/v1
embedding_model    = bge-m3
```

首次启动会自动给已有记忆补向量，200 条约 1 分钟。

### 语音识别

```bash
cd data/asr/models
curl -LO https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip
unzip vosk-model-cn-0.22.zip && mv vosk-model-cn-0.22 vosk-model-cn
```

### 语音合成

GPT-SoVITS 需要自己的参考音频：

```
data/refaudio/平静/ref.wav + asr.txt
data/refaudio/高兴/ ...
```

5–10 秒干净人声，`asr.txt` 写这段音频说的话。然后在 `dafeiyu_voice` 里打开 `enable`。

不需要语音：把 compose 里 `asr` 和 `sovits` 两段注释掉即可。

## 六、自检

```bash
./scripts/healthcheck.sh
```

再在 QQ 里发 `/心智状态`，能看到四行数据就说明整条链路通了。

## 七、日常运维

```bash
./scripts/backup.sh                 # 备份状态
docker compose logs -f astrbot      # 看日志
docker compose pull && docker compose up -d   # 升级镜像
./scripts/install-plugins.sh && docker compose restart astrbot   # 升级插件
```

## 八、常见问题

见 [FAQ](FAQ.md)。
