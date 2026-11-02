"""大肥鱼 · 健康监控

她挂了不会自己说，这个插件替她说：

- 每 30 分钟自检一次（可调）
- 硬错误立刻推 QQ：记忆库打不开 / 条数归零 / 磁盘不足 / 插件状态文件异常
- 平时安静，只在出事时说话
- `/健康` 随时手动体检
"""

import asyncio
import json
import os
import shutil
import time

from astrbot.api import logger, AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter, MessageChain
from astrbot.api.star import Context, Star

PLUGIN_NAME = "dafeiyu_health"
DATA_DIR = f"/AstrBot/data/plugin_data/{PLUGIN_NAME}"
STATE_FILE = os.path.join(DATA_DIR, "health.json")

CORE = {
    "mindcore": ("/AstrBot/data/plugin_data/dafeiyu_mindcore/memory_core.db", 3600 * 24),
    "hormone": ("/AstrBot/data/plugin_data/dafeiyu_hormone/hormones.json", 3600 * 24 * 3),
    "persona": ("/AstrBot/data/plugin_data/dafeiyu_persona_core/persona_core.json", 3600 * 24 * 30),
    "brain": ("/AstrBot/data/plugin_data/dafeiyu_brain/memory.db", 3600 * 24 * 7),
}


class Health(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None) -> None:
        super().__init__(context)
        self.cfg = config or {}
        self._task = None
        self._last = {}
        self._fails = 0
        self._load()

    def _c(self, key, default):
        try:
            v = self.cfg.get(key, default)
        except Exception:
            return default
        return default if v is None else v

    def _load(self):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                self._last = json.load(f)
        except Exception:
            self._last = {}

    def _save(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp = STATE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._last, f, ensure_ascii=False)
            os.replace(tmp, STATE_FILE)
        except Exception:
            pass

    # ---------------------------------------------------------------- 检查

    def check(self) -> list:
        """返回问题列表，空表示健康。"""
        issues = []

        # 1. 心智库
        path, _ = CORE["mindcore"]
        if not os.path.exists(path):
            issues.append(f"心智库不见了：{path}")
        else:
            try:
                import sqlite3
                con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=10)
                n = con.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
                con.close()
                if n == 0:
                    issues.append("心智库是空的（0 条记忆）")
                self._last["memories"] = n
            except Exception as exc:  # noqa: BLE001
                issues.append(f"心智库打不开：{exc!r}")

        # 2. 关键状态文件
        for name, (p, ttl) in CORE.items():
            if name == "mindcore":
                continue
            if not os.path.exists(p):
                issues.append(f"{name} 状态文件缺失")
                continue
            age = time.time() - os.path.getmtime(p)
            if age > ttl:
                issues.append(f"{name} 状态 {age/3600:.0f} 小时没更新（阈值 {ttl/3600:.0f}h）")

        # 3. 磁盘
        try:
            du = shutil.disk_usage("/AstrBot/data")
            pct = du.free / du.total * 100
            self._last["disk_free_pct"] = round(pct, 1)
            limit = float(self._c("disk_min_pct", 5))
            if pct < limit:
                issues.append(f"磁盘快满了：剩 {pct:.1f}%（低于 {limit}%）")
        except Exception:
            pass

        # 4. 插件目录
        plc = "/AstrBot/data/plugins"
        need = ["dafeiyu_mindcore", "dafeiyu_hormone", "dafeiyu_persona_core"]
        if os.path.isdir(plc):
            missing = [n for n in need if not os.path.isdir(os.path.join(plc, n))]
            if missing:
                issues.append("插件目录缺失：" + "、".join(missing))

        return issues

    def report(self) -> dict:
        issues = self.check()
        self._last["ts"] = time.time()
        self._last["ok"] = not issues
        self._last["issues"] = issues
        self._save()
        return {"ok": not issues, "issues": issues,
                "memories": self._last.get("memories"),
                "disk_free_pct": self._last.get("disk_free_pct")}

    async def _alert(self, text: str):
        umo = str(self._c("notify_umo", "") or "").strip()
        if not umo:
            logger.warning(f"[{PLUGIN_NAME}] 没配 notify_umo，告警只写日志：{text}")
            return
        try:
            await self.context.send_message(
                umo, MessageChain().message(text))
            logger.info(f"[{PLUGIN_NAME}] 已告警 → {umo}")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"[{PLUGIN_NAME}] 告警发送失败：{exc!r}")

    async def _loop(self):
        interval = max(300, int(self._c("interval_seconds", 1800)))
        await asyncio.sleep(60)
        while True:
            try:
                r = self.report()
                if not r["ok"]:
                    # 连续两次才告警，避免瞬时抖动
                    self._fails += 1
                    if self._fails >= 2:
                        text = "【她出问题了】\n" + "\n".join("· " + i for i in r["issues"])
                        await self._alert(text)
                        self._fails = 0
                else:
                    self._fails = 0
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"[{PLUGIN_NAME}] 自检异常：{exc!r}")
            await asyncio.sleep(interval)

    # ---------------------------------------------------------------- 命令

    @filter.command("健康")
    async def cmd_health(self, event: AstrMessageEvent, action: str = ""):
        """体检。用法：/健康 ｜ /健康 测试"""
        a = str(action or "").strip()
        if a in ("测试", "test"):
            await self._alert("【测试告警】这条是手动触发的，收到就说明告警链路通了。")
            yield event.plain_result("已发一条测试告警，看 QQ。")
            return

        r = self.report()
        if r["ok"]:
            yield event.plain_result(
                f"一切正常\n· 记忆 {r['memories']} 条\n"
                f"· 磁盘剩 {r.get('disk_free_pct', '?')}%\n"
                f"· 下次自检 {int(self._c('interval_seconds', 1800))//60} 分钟内")
        else:
            yield event.plain_result("发现问题：\n" + "\n".join("· " + i for i in r["issues"]))

    @filter.command("健康配置")
    async def cmd_set(self, event: AstrMessageEvent):
        """把当前会话设为告警接收方。用法：/健康配置"""
        umo = str(getattr(event, "unified_msg_origin", "") or "")
        if not umo:
            yield event.plain_result("拿不到会话 ID。")
            return
        try:
            self.cfg["notify_umo"] = umo
        except Exception:
            pass
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "notify_umo.txt"), "w", encoding="utf-8") as f:
            f.write(umo)
        yield event.plain_result(f"告警会发到这个会话：\n{umo}")

    # ---------------------------------------------------------------- 生命周期

    async def initialize(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        p = os.path.join(DATA_DIR, "notify_umo.txt")
        if os.path.exists(p) and not self._c("notify_umo", ""):
            try:
                self.cfg["notify_umo"] = open(p, encoding="utf-8").read().strip()
            except Exception:
                pass
        r = self.report()
        logger.info(f"[{PLUGIN_NAME}] 启动自检：{'正常' if r['ok'] else r['issues']}")
        self._task = asyncio.create_task(self._loop())

    async def terminate(self):
        if self._task:
            self._task.cancel()
