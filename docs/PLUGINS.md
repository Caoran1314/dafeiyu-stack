# 插件清单

10 个插件，分三组。

## 心智组（必需，三个要一起开）

| 插件 | 一句话 | 关键配置 |
|---|---|---|
| `dafeiyu_persona_core` | 六维人格 + 单轮钳位 ±0.12 + 内核校验 | `inject=false`（交给 mindcore）<br>`delta_mode=heuristic` 或 `model` |
| `dafeiyu_hormone` | 四激素心境，随时间回归、被事件扰动 | `inject=false`<br>`gate_proactive=true` 心情差压主动消息 |
| `dafeiyu_mindcore` | 记忆权重/衰减/晋升 + 向量召回 + 技能 SM2 + 离线补偿 + 生命卡 | `inject_mode=primary`<br>`embedding_model=bge-m3` |

## 表达组（按需）

| 插件 | 一句话 | 开启条件 |
|---|---|---|
| `dafeiyu_human` | 去 AI 腔、一句一行、错字、延迟 | 装上即生效 |
| `dafeiyu_voice` | 克隆音色 | 需要 SoVITS + 参考音频，`enable=true` |
| `dafeiyu_photo` | 话题命中时发真实照片 | `enable=true` |
| `dafeiyu_eval` | 拟人度测评（只看不改） | 可选 |
| `dafeiyu_health` | 健康监控：库/状态/磁盘出问题主动告警 | 建议装 |

## 展示组（按需）

| 插件 | 一句话 | 入口 |
|---|---|---|
| `dafeiyu_brain3d` | 3D 皮层脑 + 她的一生时间线 | 面板 → 插件 → 大肥鱼3D记忆脑 |
| `dafeiyu_room` | 3D 房间，状态随时段和聊天变 | 面板 → 插件 → 大肥鱼房间 |

## 依赖关系

```
dafeiyu_brain（旧记忆库）
      │ 只读导入
      ▼
dafeiyu_mindcore ◀── dafeiyu_hormone（读激素算 f_endo / Qmax）
      │            ◀── dafeiyu_persona_core（读人格写进上下文）
      │
      ├──▶ dafeiyu_voice（读激素选语音情绪）
      ├──▶ dafeiyu_photo（读激素定发图意愿）
      ├──▶ dafeiyu_brain3d（读 brain.db 与主库图片）
      └──▶ dafeiyu_room（读激素 + 聊天状态）
```

## 最小可用组合

只要人格和记忆，不要语音/3D：

```
dafeiyu_brain
dafeiyu_human
dafeiyu_persona_core
dafeiyu_hormone
dafeiyu_mindcore
```

其余全部停用也不影响她说话。

## 全部停用会怎样

她退化成一个普通的 AstrBot 机器人：人格靠提示词，没有情绪、没有记忆衰减、没有技能。
不会崩，只是不像人了。

## 安装方式

插件都在本仓库 `plugins/` 目录下。

**一键装**：

```bash
./scripts/install-plugins.sh
```

**单独装**：去 [Releases](https://github.com/Caoran1314/dafeiyu-stack/releases) 下载对应 `dafeiyu_xxx.zip`，
在 AstrBot 插件页「上传安装」。

**从仓库装**：在 AstrBot 里填 `Caoran1314/dafeiyu-stack/plugins/dafeiyu_xxx`。
