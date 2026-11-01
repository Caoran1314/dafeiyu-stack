"""大肥鱼拟人度评测（dafeiyu_eval）。

只做观测，不改任何行为——保证「测量」和「干预」分离。
- on_llm_request 记开始时间（算延迟）
- on_decorating_result 记最终发出文本的指标
- /eval 出报告；/eval export 导出盲测素材
"""
from __future__ import annotations

import json
import os
import sqlite3
import time

from astrbot import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.message_components import Plain
from astrbot.api.star import Context, Star, StarTools
from astrbot.core.config.astrbot_config import AstrBotConfig

from .metrics import format_report, measure, summarize

PLUGIN_NAME = "dafeiyu_eval"

SCHEMA = """
CREATE TABLE IF NOT EXISTS outbound (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT DEFAULT (datetime('now','localtime')),
  epoch REAL,
  umo TEXT,
  text TEXT,
  chars INT, lines INT, avg_line_chars REAL, multi_part INT,
  question_end INT, ai_mark INT, markdown INT,
  colon INT, dash INT, quote INT, latency_ms REAL
);
CREATE INDEX IF NOT EXISTS ix_out_epoch ON outbound(epoch);
"""


class DafeiyuEval(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None) -> None:
        super().__init__(context)
        self.cfg: dict = dict(config or {})
        self.data_dir = str(StarTools.get_data_dir(PLUGIN_NAME))
        os.makedirs(self.data_dir, exist_ok=True)
        self.db = sqlite3.connect(os.path.join(self.data_dir, "eval.db"), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript(SCHEMA)
        self.db.commit()
        self._t0: dict[str, float] = {}
        logger.info(f"[{PLUGIN_NAME}] 已加载")

    def _c(self, key, default):
        v = self.cfg.get(key, default)
        return default if v is None else v

    @filter.on_llm_request(priority=1000)
    async def mark_start(self, event: AstrMessageEvent, req) -> None:
        try:
            umo = str(getattr(event, "unified_msg_origin", "") or "")
            self._t0[umo] = time.monotonic()
            if len(self._t0) > 500:
                self._t0.clear()
        except Exception:
            pass

    @filter.on_decorating_result(priority=-1000)   # 最后跑，拿到最终文本
    async def measure_out(self, event: AstrMessageEvent) -> None:
        try:
            if not self._c("enable", True):
                return
            result = event.get_result()
            if not result or not getattr(result, "chain", None):
                return
            text = "\n".join(
                comp.text for comp in result.chain
                if isinstance(comp, Plain) and isinstance(getattr(comp, "text", None), str))
            if not text.strip():
                return
            umo = str(getattr(event, "unified_msg_origin", "") or "")
            t0 = self._t0.pop(umo, None)
            latency = (time.monotonic() - t0) * 1000 if t0 else None
            m = measure(text, latency)
            self.db.execute(
                "INSERT INTO outbound(epoch, umo, text, chars, lines, avg_line_chars,"
                " multi_part, question_end, ai_mark, markdown, colon, dash, quote, latency_ms)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (time.time(), umo, text[:2000], m["chars"], m["lines"], m["avg_line_chars"],
                 m["multi_part"], m["question_end"], m["ai_mark"], m["markdown"],
                 m["colon"], m["dash"], m["quote"], m["latency_ms"]))
            self.db.commit()
        except Exception as e:
            logger.warning(f"[{PLUGIN_NAME}] 采集异常已忽略: {e!r}")

    def _rows(self, hours: int) -> list:
        since = time.time() - hours * 3600
        return self.db.execute(
            "SELECT * FROM outbound WHERE epoch >= ? ORDER BY id DESC", (since,)).fetchall()

    @filter.command("eval")
    async def eval_cmd(self, event: AstrMessageEvent):
        """拟人度报告：/eval ｜ /eval 72 ｜ /eval export"""
        try:
            if not event.is_admin():
                return
            args = str(getattr(event, "message_str", "") or "").split()
            sub = args[1] if len(args) > 1 else "24"
            if sub == "export":
                path = os.path.join(self.data_dir, f"blind_{int(time.time())}.jsonl")
                rows = self.db.execute(
                    "SELECT id, text FROM outbound ORDER BY RANDOM() LIMIT 60").fetchall()
                with open(path, "w", encoding="utf-8") as f:
                    for r in rows:
                        f.write(json.dumps({"id": f"bot-{r['id']}", "text": r["text"]},
                                           ensure_ascii=False) + "\n")
                yield event.plain_result(
                    f"导出 {len(rows)} 条到 {os.path.basename(path)}，"
                    "再混入同数量真人回复做盲测")
                return
            hours = int(sub) if sub.isdigit() else 24
            yield event.plain_result(format_report(summarize(self._rows(hours)), f"近 {hours} 小时"))
        except Exception as e:
            logger.warning(f"[{PLUGIN_NAME}] 命令失败: {e!r}")

    async def terminate(self) -> None:
        try:
            self.db.close()
        except Exception:
            pass
        logger.info(f"[{PLUGIN_NAME}] 已卸载")
