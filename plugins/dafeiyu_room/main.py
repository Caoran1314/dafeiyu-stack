"""大肥鱼房间：把她"此刻在干什么"变成一个 3D 房间场景。

状态来源有三层：
1. 时段（0-8 睡、8-19 用电脑、19-24 床上刷手机）
2. 最近有没有聊天（有 → 立刻变成"拿手机"）
3. 她的回复（气泡里滚出她的话）

页面每 2 秒读一次 room.json，切换场景与姿势。
"""

import json
import os
import time

from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Plain
from astrbot.api.star import Context, Star

PLUGIN_NAME = "dafeiyu_room"
PAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages", "room")
OUT = os.path.join(PAGE_DIR, "room.json")
MOOD_FILE = "/AstrBot/data/plugin_data/astrbot_plugin_persona_state/mood.json"
HORMONE_FILE = "/AstrBot/data/plugin_data/dafeiyu_hormone/hormones.json"


def _mood() -> dict:
    """优先读新的四激素心境引擎；没有就退回旧的 PAD。"""
    try:
        with open(HORMONE_FILE, encoding="utf-8") as f:
            h = json.load(f)
        sero = float(h.get("sero", 0.6))
        dopa = float(h.get("dopa", 0.4))
        cort = float(h.get("cort", 0.2))
        oxy = float(h.get("oxy", 0.5))
        return {
            "available": True,
            "joy": max(0.0, min(1.0, dopa)),
            "calm": max(0.0, min(1.0, sero)),
            "cort": max(0.0, min(1.0, cort)),
            "oxy": max(0.0, min(1.0, oxy)),
        }
    except Exception:
        pass
    try:
        with open(MOOD_FILE, encoding="utf-8") as f:
            d = json.load(f)
        return {
            "available": True,
            "joy": max(0.0, min(1.0, float(d.get("joy", 0.5)))),
            "calm": max(0.0, min(1.0, float(d.get("calm", 0.5)))),
        }
    except Exception:
        return {"joy": 0.5, "calm": 0.5, "available": False}


class Room(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None) -> None:
        super().__init__(context)
        self.cfg = config or {}
        self.bubbles: list[dict] = []
        self.last_activity = 0.0
        self.mode = "sleep"
        self._task = None

    def _c(self, key, default):
        try:
            v = self.cfg.get(key, default)
        except Exception:
            return default
        return default if v is None else v

    # ---------------------------------------------------------------- 状态

    def _base_mode(self) -> str:
        h = time.localtime().tm_hour
        if 0 <= h < 8:
            return "sleep"
        if 8 <= h < 19:
            return "desk"
        if 19 <= h < 24:
            return "phone"
        return "sleep"

    def _compute_mode(self) -> str:
        now = time.time()
        quiet_min = float(self._c("quiet_minutes", 25)) * 60
        if now - self.last_activity < quiet_min:
            # 刚聊完 —— 她在拿手机
            if self._base_mode() == "sleep":
                return "phone"
            return "phone"
        return self._base_mode()

    def _label(self, mode: str) -> str:
        return {
            "sleep": "睡着了",
            "phone": "躺床上刷手机",
            "desk": "在电脑前",
            "window": "站在窗边发呆",
            "away": "不在房间",
        }.get(mode, "在房间")

    def _flush(self) -> dict:
        self.mode = self._compute_mode()
        data = {
            "mode": self.mode,
            "label": self._label(self.mode),
            "ts": time.time(),
            "clock": time.strftime("%H:%M"),
            "bubbles": self.bubbles[-8:],
            "mood": _mood(),
        }
        try:
            os.makedirs(PAGE_DIR, exist_ok=True)
            tmp = OUT + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            os.replace(tmp, OUT)
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{PLUGIN_NAME}] 写 room.json 失败：{exc!r}")
        return data

    def _add(self, who: str, text: str) -> None:
        text = " ".join(str(text or "").split())[:160]
        if not text:
            return
        self.bubbles.append({"who": who, "text": text, "ts": time.time()})
        self.bubbles = self.bubbles[-12:]
        self.last_activity = time.time()

    # ---------------------------------------------------------------- 钩子

    @filter.on_llm_request(priority=95000)
    async def on_user(self, event: AstrMessageEvent, req) -> None:
        try:
            txt = ""
            for c in (getattr(getattr(event, "message_obj", None), "message", []) or []):
                if isinstance(c, Plain) and getattr(c, "text", ""):
                    txt += c.text
            if not txt:
                return
            if str(txt).strip().startswith(("/", "／")):
                return
            self._add("you", txt)
            self._flush()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{PLUGIN_NAME}] 记录用户消息失败：{exc!r}")

    @filter.on_decorating_result(priority=8000)
    async def on_reply(self, event: AstrMessageEvent) -> None:
        try:
            result = event.get_result()
            chain = getattr(result, "chain", None) if result else None
            if not chain:
                return
            txt = " ".join(c.text for c in chain
                           if isinstance(c, Plain) and getattr(c, "text", ""))
            self._add("her", txt)
            self._flush()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{PLUGIN_NAME}] 记录回复失败：{exc!r}")

    @filter.command("房间")
    async def cmd_room(self, event: AstrMessageEvent):
        """刷新房间里她的状态。用法：/房间"""
        d = self._flush()
        yield event.plain_result(f"她现在：{d['label']}（{d['clock']}）")

    # ---------------------------------------------------------------- 生命周期

    async def initialize(self) -> None:
        import asyncio
        self._flush()

        async def loop():
            interval = max(5, int(self._c("refresh_seconds", 10)))
            while True:
                try:
                    self._flush()
                except Exception:
                    pass
                await asyncio.sleep(interval)

        self._task = asyncio.create_task(loop())
        logger.info(f"[{PLUGIN_NAME}] 房间已就绪，页面数据={OUT}")

    async def terminate(self) -> None:
        if self._task:
            self._task.cancel()
