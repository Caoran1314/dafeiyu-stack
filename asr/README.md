# ASR（Vosk 中文识别）

容器里只放服务，**模型要自己下**（约 2 GB）：

```bash
# 在宿主机执行（路径跟 .env 里 DATA_ROOT 对应）
cd data/asr/models
curl -LO https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip
unzip vosk-model-cn-0.22.zip
mv vosk-model-cn-0.22 vosk-model-cn
```

模型目录结构：

```
data/asr/models/vosk-model-cn/
├── am/
├── conf/
├── graph/
└── ivector/
```

第一次调用会加载模型（约 10–20 秒），之后常驻内存。

接口（OpenAI 兼容）：

- `POST /v1/audio/transcriptions`（multipart: `file`, `model`）
- `GET /healthz`
