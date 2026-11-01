# 配置要点（照着改，别漏）

## 1. 人格安全模式（最容易翻车）

```json
"agent_runner": {
  "config": {
    "persona": {
      "safety_mode": false
    }
  }
}
```

打开时模型会加一层"安全模式"约束，她会频繁拒绝、跳出角色。**必须关**。

## 2. 人格注入

- 人格设定里粘 `persona/persona_lover.md`
- 别在人格里写"你无法发语音""你是 AI"之类的否定句，她会照着念

## 3. 心智三件套

```
dafeiyu_hormone         enable=true  inject=false     ← 只算状态，不抢注入
dafeiyu_persona_core    enable=true  inject=false     ← 同上
dafeiyu_mindcore        inject_mode=primary           ← 唯一注入点
dafeiyu_brain           memory_inject=false           ← 旧链路停注入
```

想回退：把 `dafeiyu_brain.memory_inject` 改回 true，`mindcore.inject_mode` 改成 `supplement`。

## 4. 向量服务

```
embedding_api_base = http://172.17.0.1:11434/v1   # 容器访问宿主机
embedding_model    = bge-m3
```

首次启动会自动给所有记忆补向量（216 条约 1 分钟）。

拉模型：

```bash
docker exec -it dafeiyu-ollama ollama pull bge-m3
```

## 5. 语音

```
api_base      = http://172.17.0.1:9880    # 或容器名
ref_audio_root= /AstrBot/data/refaudio
```

每个情绪一个目录：`平静/ 高兴/ 害羞/ 生气/ 着急/`，里面放 `ref.wav` + `asr.txt`。

## 6. 主动消息

```
间隔 4–8 小时，静默 0–8 点，最多连续未回复 2 次
```

心情差（皮质醇 ≥ 0.45）时会被 `dafeiyu_hormone` 的闸门压掉。
