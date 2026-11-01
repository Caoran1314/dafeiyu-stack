# dafeiyu-asr

林小鱼数字人格系统的**语音识别服务**：Vosk 中文模型 + OpenAI 兼容接口，纯本地推理，不联网。

用这个镜像配合 [`dafeiyu-stack`](https://github.com/Caoran1314/dafeiyu-stack) 使用，
让她能听懂你发的语音。

## 特性

- **OpenAI 兼容**：`POST /v1/audio/transcriptions`，现有客户端不用改
- **纯本地**：模型跑在容器里，音频不出机器
- **懒加载**：第一次请求才载入模型，不拖慢启动
- **小**：基础镜像 + vosk，没装 torch
- **健康检查**：`GET /healthz`

## 用法

```yaml
services:
  asr:
    image: caoran1314/dafeiyu-asr:1.0
    container_name: dafeiyu-asr
    restart: unless-stopped
    environment:
      - VOSK_MODEL_DIR=/models/vosk-model-cn
      - PORT=9001
    ports:
      - "127.0.0.1:9001:9001"
    volumes:
      - ./data/asr/models:/models
```

模型要自己下（约 2 GB，不进镜像）：

```bash
mkdir -p data/asr/models && cd data/asr/models
curl -LO https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip
unzip vosk-model-cn-0.22.zip
mv vosk-model-cn-0.22 vosk-model-cn
```

启动后：

```bash
curl http://127.0.0.1:9001/healthz
# {"ok": true, "model": "vosk-model-cn"}

curl -F "file=@test.wav" -F "model=vosk" http://127.0.0.1:9001/v1/audio/transcriptions
# {"text": "..."}
```

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/v1/audio/transcriptions` | multipart：`file`（wav/mp3/ogg）、`model`（忽略） |
| GET | `/v1/models` | 返回可用模型 |
| GET | `/healthz` | 健康检查 |

支持任意 ffmpeg 能解的格式（内部会先转 16k 单声道 wav）。

## 资源

| 项 | 值 |
|---|---|
| 镜像大小 | 约 350 MB（不含模型） |
| 内存 | 空闲 80 MB，载入模型后约 1.2 GB |
| 首次请求 | 10–20 秒（载入模型） |
| 单句识别 | 0.9–1.1 秒（10 秒内音频） |

## 标签

| tag | 说明 |
|---|---|
| `1.0` | 当前稳定版 |
| `latest` | 跟随主分支 |

## 说明

- 只做识别，不保存音频
- 不包含模型（镜像会太大，也不方便换模型）
- 换模型：把新的 Vosk 中文模型放到 `/models/vosk-model-cn` 再重启

## License

MIT
