# 大肥鱼抖音分享桥

任何来源的截图，都可以让她**配一句话主动发到你 QQ**。

## 为什么要「推送前先看图」

AstrBot 只会给**别人发来的图**做描述；**她自己发出去的图**不会进她的理解。
所以她推完图，被问「那是什么」只能猜。

解决办法：推送前先让本地视觉模型看一眼，把描述写进她发的那句话里。
这样她自己那句「刚刷到一个，一盘炒面，撒了葱花」就在历史里，后面聊起来是一致的。

```
待推送的图 → qwen2.5vl:3b 看图 → "一盘炒面，撒了葱花"
      ↓
她发：「刚刷到一个，你看看，一盘炒面，撒了葱花」+ 图
```

## 它怎么工作

```
图片落进目录（任何截图工具、手动丢图都可以）
      ↓ 每 30 秒扫一次
发现新图 → 等 3 秒写完 → 配一句话 → 主动发给你
      ↓ 同时
把「大肥鱼房间」切到刷手机状态
```

**边界很清楚**：不登录任何账号、不操作 App，只读文件夹。

## 装

```bash
./scripts/install-plugins.sh
docker compose restart astrbot
```

## 配

### 1. 设置收消息的会话（两种方式）

**方式 A：自动**（推荐）

在 QQ 里直接给她发任意一条消息，插件会**自动记住这个会话**（`auto_umo` 默认开）。

**方式 B：手动**

在你想收推送的会话里发：

```
/抖音桥配置
```

⚠️ **会话 ID 格式**：`<平台实例ID>:FriendMessage:<QQ号>`，例如 `napcat:FriendMessage:2224383507`。
平台实例 ID 不是 `aiocqhttp`，要去「配置 → 平台适配器」看实例名（你的叫 `napcat`）。
写错的话日志会报 `cannot find platform for session ...`，消息不会发出。

### 2. 设置截图目录

默认已经包含这两个路径：

```
/AstrBot/data/plugin_data/astrbot_phone_control/shots
/AstrBot/data/plugin_data/astrbot_phone_control/screenshots
```

如果你用别的工具截图，把目录填进 `watch_dirs`（多个用逗号分隔）。

没有截图工具也能用：把图丢进

```
data/astrbot/plugin_data/dafeiyu_douyin_bridge/inbox/
```

一样会被推出去。

### 3. 可选：配文

默认按时间自动生成：

```
白天：刚刷到这个，{title}
深夜：睡不着刷到的，{title}
```

想自己写就填 `caption`，`{title}` 会被替换成同名 `.txt` / `.json` 里的标题。

## 命令

| 命令 | 作用 |
|---|---|
| `/刷到了` | 立刻把最新一张发出来（测试用） |
| `/刷到了 找 banmian` | 从容器附件目录按关键词找图并推 |
| `/刷到了 /AstrBot/data/xxx.jpg` | 推指定容器内文件 |
| `/抖音桥` | 看监视目录、已推送数量、今日配额 |
| `/抖音桥配置` | 把当前会话设为推送目标 |

## 配置

| 键 | 默认 | 说明 |
|---|---|---|
| `watch_dirs` | 空 | 留空用内置路径 |
| `notify_umo` | 空 | 推送目标，用命令自动填 |
| `caption` | 空 | 配文模板 |
| `max_images` | 3 | 一条最多几张 |
| `max_per_day` | 6 | 每日上限 |
| `min_interval` | 600 | 最小间隔（秒） |
| `poll_seconds` | 30 | 扫描间隔 |
| `settle_seconds` | 3 | 等文件写完 |
| `report_room` | true | 顺手切房间状态 |
| `describe` | true | 推送前调用视觉模型看图 |
| `vision_base` | 空 | 视觉模型地址，空则依次试 `ollama` / `172.17.0.1` / `dafeiyu-ollama` / `host.docker.internal` |
| `vision_model` | `qwen2.5vl:3b` | Ollama 里的视觉模型名 |
| `vision_timeout` | 90 | 看图超时（CPU 跑 3B 大约 30–45 秒） |

## 配额说明

默认每天最多 6 次、间隔 10 分钟。防止你睡觉时被刷屏。

想让她更主动：`max_per_day` 调大、`min_interval` 调小。

## 已知限制

- 只发**图片**。抖音视频文件不在此列（要大文件建议直接传网盘）。
- 截图目录必须是她能读到的地方（容器内路径）。
- 同一个图只发一次（按路径+mtime+大小去重）。

## License

MIT © Caoran1314
