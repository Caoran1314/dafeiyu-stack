"""大肥鱼 · 抖音分享桥

把「她在刷抖音」变成「她在 QQ 里给你看」：

- 监视一个目录（phone_control 的截图目录，或你手动丢图的目录）
- 发现新图 → 等它写完 → 主动发给你，配一句话
- 有同名 .json/.txt 侧车文件就用它的标题，没有就用时间+模板

不碰抖音 App、不登录任何账号，只读文件夹 —— 安全边界很清楚。
"""

import asyncio
import json
import os
import re
import time

from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter, MessageChain
from astrbot.api.message_components import Image, Plain
from astrbot.api.star import Context, Star

PLUGIN_NAME = "dafeiyu_douyin_bridge"
DATA_DIR = f"/AstrBot/data/plugin_data/{PLUGIN_NAME}"
STATE_FILE = os.path.join(DATA_DIR, "state.json")
ROOM_ACTIVITY = "/AstrBot/data/plugin_data/dafeiyu_room/activity.json"

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_DIRS = [
    "/AstrBot/data/plugin_data/astrbot_phone_control/shots",
    "/AstrBot/data/plugin_data/astrbot_phone_control/screenshots",
    "/AstrBot/data/plugin_data/dafeiyu_douyin_bridge/inbox",
]



ATTACH_DIRS = ["/AstrBot/data/attachments", "/AstrBot/data/files", "/AstrBot/data/temp"]


def _find_attachment(keyword: str) -> str:
    """在容器附件目录里按文件名关键词找最新的图。"""
    kw = keyword.strip().lower()
    best, best_m = "", 0.0
    for base in ATTACH_DIRS:
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for f in files:
                if os.path.splitext(f)[1].lower() not in IMG_EXT:
                    continue
                if kw and kw not in f.lower():
                    continue
                p = os.path.join(root, f)
                try:
                    m = os.path.getmtime(p)
                except Exception:
                    continue
                if m > best_m:
                    best, best_m = p, m
    return best


class DouyinBridge(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None) -> None:
        super().__init__(context)
        self.cfg = config or {}
        self._task = None
        self._sent = {}
        self._descs = {}
        self._count = {"day": "", "n": 0}
        self._last_ts = 0.0
        self._load_state()

    # ---------------------------------------------------------------- 配置

    def _c(self, key, default):
        try:
            v = self.cfg.get(key, default)
        except Exception:
            return default
        return default if v is None else v

    def _dirs(self) -> list[str]:
        raw = str(self._c("watch_dirs", "") or "")
        if raw.strip():
            return [x.strip() for x in re.split(r"[,;\n]", raw) if x.strip()]
        return list(DEFAULT_DIRS)

    # ---------------------------------------------------------------- 状态

    def _load_state(self):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                d = json.load(f)
            self._sent = {k: float(v) for k, v in (d.get("sent") or {}).items()}
            self._descs = d.get("descs") or {}
            self._count = d.get("count") or {"day": "", "n": 0}
        except Exception:
            self._sent = {}
            self._count = {"day": "", "n": 0}

    def _save_state(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            # 只留最近 500 条
            items = sorted(self._sent.items(), key=lambda x: -x[1])[:500]
            data = {"sent": dict(items), "count": self._count,
                    "descs": self._descs or {}, "ts": time.time()}
            tmp = STATE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            os.replace(tmp, STATE_FILE)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{PLUGIN_NAME}] 保存状态失败：{exc!r}")


    # ---------------------------------------------------------------- 看图

    def _describe_image(self, path: str) -> str:
        """用本地视觉模型给图配一句描述，写进她自己的话里。"""
        if not bool(self._c("describe", True)):
            return ""
        bases = []
        cfg_base = str(self._c("vision_base", "") or "").strip()
        if cfg_base:
            bases.append(cfg_base.rstrip("/"))
        for b in ("http://ollama:11434/v1", "http://172.17.0.1:11434/v1",
                  "http://dafeiyu-ollama:11434/v1", "http://host.docker.internal:11434/v1"):
            if b not in bases:
                bases.append(b)
        model = str(self._c("vision_model", "qwen2.5vl:3b"))
        timeout = int(self._c("vision_timeout", 90))
        key = f"desc:{path}:{int(os.path.getmtime(path))}"
        cached = (self._descs or {}).get(key)
        if cached:
            return cached
        try:
            import base64
            import urllib.request as _u
            raw = open(path, "rb").read()
            if len(raw) > 8_000_000:
                return ""
            b64 = base64.b64encode(raw).decode()
            prompt = str(self._c("vision_prompt",
                "用一句很口语的话说这张图里有什么，像女朋友随口说的，不超过25个字。"))
            body = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ]}],
                "max_tokens": 80, "temperature": 0.4,
            }).encode()
            d, base = None, ""
            last_err = None
            for b in bases:
                try:
                    req = _u.Request(f"{b}/chat/completions", data=body, method="POST")
                    req.add_header("Content-Type", "application/json")
                    req.add_header("Authorization", "Bearer ollama")
                    with _u.urlopen(req, timeout=timeout) as resp:
                        d = json.loads(resp.read().decode())
                    base = b
                    if not self._c("vision_base", ""):
                        try:
                            self.cfg["vision_base"] = b
                        except Exception:
                            pass
                    break
                except Exception as exc:  # noqa: BLE001
                    last_err = exc
            if d is None:
                raise last_err or RuntimeError("no endpoint")
            text = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
            text = " ".join(str(text).split())[:60]
            if text:
                self._descs = self._descs or {}
                self._descs[key] = text
                if len(self._descs) > 300:
                    self._descs = dict(list(self._descs.items())[-300:])
                logger.info(f"[{PLUGIN_NAME}] 看图：{text}")
            return text
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{PLUGIN_NAME}] 看图失败：{exc!r}")
            return ""

    # ---------------------------------------------------------------- 扫描

    def _sidecar_title(self, path: str) -> str:
        base, _ = os.path.splitext(path)
        for ext in (".json", ".txt"):
            p = base + ext
            if not os.path.exists(p):
                continue
            try:
                if ext == ".json":
                    d = json.load(open(p, encoding="utf-8"))
                    for k in ("title", "desc", "text", "summary"):
                        if d.get(k):
                            return str(d[k])[:80]
                else:
                    t = open(p, encoding="utf-8").read().strip()
                    if t:
                        return t[:80]
            except Exception:
                continue
        return ""

    def _scan(self, dirs: list[str]) -> list[str]:
        out = []
        for d in dirs:
            if not os.path.isdir(d):
                continue
            try:
                files = os.listdir(d)
            except Exception:
                continue
            for f in files:
                if os.path.splitext(f)[1].lower() not in IMG_EXT:
                    continue
                p = os.path.join(d, f)
                try:
                    st = os.stat(p)
                except Exception:
                    continue
                key = f"{p}:{int(st.st_mtime)}:{st.st_size}"
                if key in self._sent:
                    continue
                if st.st_size < 3000:          # 太小的多半是占位图
                    continue
                out.append(p)
        out.sort(key=lambda p: os.path.getmtime(p))
        return out

    # ---------------------------------------------------------------- 发送

    def _caption(self, title: str) -> str:
        tpl = str(self._c("caption", "") or "")
        if tpl:
            return tpl.replace("{title}", title or "")
        hour = time.localtime().tm_hour
        when = "刚刷到" if hour >= 6 else "睡不着刷到的"
        if title:
            return f"{when}这个，{title}"
        return f"{when}一个，你看看"

    def _quota_ok(self) -> bool:
        day = time.strftime("%Y-%m-%d")
        if self._count.get("day") != day:
            self._count = {"day": day, "n": 0}
        if self._count["n"] >= int(self._c("max_per_day", 6)):
            return False
        gap = int(self._c("min_interval", 600))
        return time.time() - self._last_ts >= gap

    async def _push(self, images: list[str]) -> int:
        umo = str(self._c("notify_umo", "") or "").strip()
        if not umo:
            logger.warning(f"[{PLUGIN_NAME}] 没配置 notify_umo，跳过发送")
            return 0
        title = self._sidecar_title(images[0])
        text = self._caption(title)
        desc = self._describe_image(images[0])
        if desc and desc not in text:
            text = f"{text}，{desc}" if text else desc
        chain = MessageChain().message(text)
        for p in images[: int(self._c("max_images", 3))]:
            try:
                chain = chain.file_image(p)
            except Exception:
                try:
                    chain.chain.append(Image.fromFileSystem(p))
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"[{PLUGIN_NAME}] 加图失败：{exc!r}")
        try:
            ok = await self.context.send_message(umo, chain)
            if ok is False:
                logger.warning(f"[{PLUGIN_NAME}] 发送失败：平台找不到会话 {umo}（会话 ID 格式应为 <平台实例ID>:FriendMessage:<QQ号>）")
                return 0
            self._last_ts = time.time()
            self._count["n"] = self._count.get("n", 0) + 1
            for p in images[: int(self._c("max_images", 3))]:
                st = os.stat(p)
                self._sent[f"{p}:{int(st.st_mtime)}:{st.st_size}"] = time.time()
            self._save_state()
            logger.info(f"[{PLUGIN_NAME}] 已推送 {len(images)} 张 → {umo}")
            return len(images)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{PLUGIN_NAME}] 推送失败：{exc!r}")
            return 0

    def _report_activity(self):
        """顺手让房间切到「刷抖音」。"""
        if not self._c("report_room", True):
            return
        try:
            os.makedirs(os.path.dirname(ROOM_ACTIVITY), exist_ok=True)
            payload = {"app": "douyin", "label": "刷抖音",
                       "ts": time.time(), "ttl": int(self._c("activity_ttl", 600))}
            tmp = ROOM_ACTIVITY + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, ROOM_ACTIVITY)
        except Exception:
            pass

    # ---------------------------------------------------------------- 循环

    async def _loop(self):
        interval = max(10, int(self._c("poll_seconds", 30)))
        while True:
            try:
                if self._c("enable", True):
                    dirs = self._dirs()
                    found = self._scan(dirs)
                    if found:
                        self._report_activity()
                        if self._quota_ok():
                            await asyncio.sleep(int(self._c("settle_seconds", 3)))
                            await self._push(found)
                        else:
                            # 配额满了也记账，避免下次重复
                            for p in found:
                                st = os.stat(p)
                                self._sent[f"{p}:{int(st.st_mtime)}:{st.st_size}"] = time.time()
                            self._save_state()
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[{PLUGIN_NAME}] 轮询异常：{exc!r}")
            await asyncio.sleep(interval)

    # ---------------------------------------------------------------- 命令

    async def _download(self, url: str) -> str:
        """把 URL 图存进 inbox，返回本地路径。"""
        import urllib.request
        inbox = self._dirs()[-1]
        os.makedirs(inbox, exist_ok=True)
        ext = os.path.splitext(url.split("?")[0])[1].lower()
        if ext not in IMG_EXT:
            ext = ".jpg"
        path = os.path.join(inbox, f"remote_{int(time.time()*1000)}{ext}")

        def _get():
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            return len(data)

        n = await asyncio.to_thread(_get)
        logger.info(f"[{PLUGIN_NAME}] 下载 {n} 字节 → {path}")
        return path


    @filter.on_llm_request(priority=40000)
    async def learn_umo(self, event: AstrMessageEvent, req=None) -> None:
        """自动记住主人发消息的会话，省得手填 notify_umo。"""
        try:
            if not self._c("auto_umo", True):
                return
            umo = str(getattr(event, "unified_msg_origin", "") or "")
            if not umo:
                return
            owner = str(self._c("owner_qq", "") or "").strip()
            sender = str(event.get_sender_id() if hasattr(event, "get_sender_id") else "")
            if owner and sender and sender != owner:
                return
            if umo == str(self._c("notify_umo", "") or ""):
                return
            try:
                self.cfg["notify_umo"] = umo
            except Exception:
                pass
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(os.path.join(DATA_DIR, "notify_umo.txt"), "w", encoding="utf-8") as f:
                f.write(umo)
            logger.info(f"[{PLUGIN_NAME}] 已记住推送目标：{umo}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{PLUGIN_NAME}] 记录会话失败：{exc!r}")

    @filter.command("刷到了")
    async def cmd_last(self, event: AstrMessageEvent, url: str = ""):
        """立刻发最新一张；也可给图片 URL。用法：/刷到了 ｜ /刷到了 https://..."""
        u = str(url or "").strip()
        # /刷到了 找 关键词  → 从容器附件目录找图
        if u.startswith("找"):
            kw = u[1:].strip()
            p = _find_attachment(kw)
            if not p:
                yield event.plain_result(f"附件目录里没找到含「{kw}」的图片。")
                return
            title = self._sidecar_title(p)
            n = await self._push([p])
            yield event.plain_result(
                f"找到 {os.path.basename(p)}，推送{'成功' if n else '失败（检查 /抖音桥 的目标会话）'}")
            return
        # /刷到了 /容器内路径
        if u and not u.startswith(("http://", "https://")) and os.path.exists(u):
            n = await self._push([u])
            yield event.plain_result(f"推送{'成功' if n else '失败'}")
            return
        if u.startswith(("http://", "https://")):
            try:
                p = await self._download(u)
            except Exception as exc:  # noqa: BLE001
                yield event.plain_result(f"下载失败：{exc!r}")
                return
            title = self._sidecar_title(p)
            n = await self._push([p])
            yield event.plain_result(
                f"推送{'成功' if n else '失败（看日志 / 先配 /抖音桥配置）'}")
            return
        found = self._scan(self._dirs())
        if not found:
            yield event.plain_result("没找到新图。检查 watch_dirs 配置的目录。")
            return
        p = found[-1]
        title = self._sidecar_title(p)
        chain = [Plain(self._caption(title))]
        try:
            chain.append(Image.fromFileSystem(p))
        except Exception:
            pass
        yield event.chain_result(chain)

    @filter.command("抖音桥")
    async def cmd_status(self, event: AstrMessageEvent, action: str = ""):
        """看状态。用法：/抖音桥 ｜ /抖音桥 测 一张图路径"""
        a = str(action or "").strip()
        if a.startswith("测"):
            rest = a[1:].strip()
            if rest and os.path.exists(rest) and os.path.splitext(rest)[1].lower() in IMG_EXT:
                n = await self._push([rest])
                yield event.plain_result(f"推送{'成功' if n else '失败'}（看日志）")
                return
        dirs = self._dirs()
        lines = [f"监视目录 {len(dirs)} 个："]
        for d in dirs:
            ok = os.path.isdir(d)
            cnt = 0
            if ok:
                try:
                    cnt = len([f for f in os.listdir(d)
                               if os.path.splitext(f)[1].lower() in IMG_EXT])
                except Exception:
                    pass
            lines.append(f"  {'✓' if ok else '✗'} {d}（{cnt} 张）")
        lines.append(f"已推送 {len(self._sent)} 张｜今日 {self._count.get('n', 0)}/{self._c('max_per_day', 6)}")
        lines.append(f"目标会话：{self._c('notify_umo', '（未配置）')}")
        lines.append(f"推送间隔 ≥{self._c('min_interval', 600)} 秒")
        yield event.plain_result("\n".join(lines))

    @filter.command("抖音桥配置")
    async def cmd_set_umo(self, event: AstrMessageEvent):
        """把当前会话设为推送目标。用法：在你想收消息的会话里发 /抖音桥配置"""
        umo = str(getattr(event, "unified_msg_origin", "") or "")
        if not umo:
            yield event.plain_result("拿不到当前会话 ID。")
            return
        try:
            self.cfg["notify_umo"] = umo
        except Exception:
            pass
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "notify_umo.txt"), "w", encoding="utf-8") as f:
            f.write(umo)
        yield event.plain_result(f"已把这个会话设为推送目标：\n{umo}")

    # ---------------------------------------------------------------- 生命周期

    async def initialize(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        # notify_umo 支持从文件读（方便不改配置就切换）
        p = os.path.join(DATA_DIR, "notify_umo.txt")
        if os.path.exists(p) and not self._c("notify_umo", ""):
            try:
                self.cfg["notify_umo"] = open(p, encoding="utf-8").read().strip()
            except Exception:
                pass
        self._task = asyncio.create_task(self._loop())
        logger.info(f"[{PLUGIN_NAME}] 已启动，监视 {len(self._dirs())} 个目录")

    async def terminate(self):
        if self._task:
            self._task.cancel()
        self._save_state()
