"""拟人度度量：纯函数，喂给 eval 插件用。

指标选择依据（对应报告 §8）：
- 平均单条字数 / 多段占比  -> 像不像在「打字」
- 问句结尾占比            -> 有没有客服腔
- AI 黑名单命中 / markdown -> 一眼假
- 延迟中位数与 P90        -> 秒回还是像人
"""
from __future__ import annotations

import re

AI_MARKS = (
    "综上所述", "值得注意的是", "有什么可以帮", "希望对你有帮助", "作为一个AI",
    "作为一个 AI", "这是个好问题", "我理解你的感受", "随时找我", "首先", "其次",
)
QUESTION_TAIL = ("吗", "呢", "么", "嘛", "?", "？")


def measure(text: str, latency_ms: float | None = None) -> dict:
    text = text or ""
    lines = [x for x in text.splitlines() if x.strip()]
    chars = [len(x) for x in lines] or [0]
    avg_chars = sum(chars) / len(chars)
    body = text.rstrip()
    return {
        "chars": len(text),
        "lines": len(lines),
        "avg_line_chars": round(avg_chars, 1),
        "multi_part": 1 if len(lines) >= 2 else 0,
        "question_end": 1 if body.endswith(QUESTION_TAIL) else 0,
        "ai_mark": 1 if any(m in text for m in AI_MARKS) else 0,
        "markdown": 1 if re.search(r"[#*`>]|\n\s*[-*+]\s|\n\s*\d+\.\s", text) else 0,
        "colon": 1 if re.search(r"[：:]", text) else 0,
        "dash": 1 if "——" in text or "—" in text else 0,
        "quote": 1 if re.search(r'[“”"「」]', text) else 0,
        "latency_ms": round(float(latency_ms), 1) if latency_ms is not None else None,
    }


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    vs = sorted(values)
    idx = min(len(vs) - 1, max(0, int(round((len(vs) - 1) * p))))
    return float(vs[idx])


def summarize(rows: list) -> dict:
    """rows: 可迭代的 sqlite Row 或 dict，字段同 measure() + ts。"""
    data = [dict(r) for r in rows]
    n = len(data)
    if not n:
        return {"count": 0}

    def rate(key: str) -> float:
        return round(sum(int(d.get(key) or 0) for d in data) / n, 3)

    lats = [float(d["latency_ms"]) for d in data if d.get("latency_ms") is not None]
    out = {
        "count": n,
        "avg_chars": round(sum(float(d.get("avg_line_chars") or 0) for d in data) / n, 1),
        "multi_part_rate": rate("multi_part"),
        "question_rate": rate("question_end"),
        "ai_mark_rate": rate("ai_mark"),
        "markdown_rate": rate("markdown"),
        "colon_rate": rate("colon"),
        "dash_rate": rate("dash"),
        "quote_rate": rate("quote"),
    }
    if lats:
        out["latency_p50_ms"] = round(_pct(lats, 0.5), 1)
        out["latency_p90_ms"] = round(_pct(lats, 0.9), 1)
    return out


# 目标区间（报告 §8.2），用于给出「哪项不达标」
TARGETS = {
    "avg_chars": (8.0, 20.0),
    "multi_part_rate": (0.50, 1.0),   # 多段越多越像打字，100% 是好事
    "question_rate": (0.0, 0.35),
    "ai_mark_rate": (0.0, 0.02),
    "markdown_rate": (0.0, 0.02),
    "colon_rate": (0.0, 0.05),
}


def verdict(summary: dict) -> list[str]:
    """返回不达标的项，给运维看。"""
    bad = []
    for key, (lo, hi) in TARGETS.items():
        if key not in summary:
            continue
        v = float(summary[key])
        if v < lo or v > hi:
            bad.append(f"{key}={v} 不在 [{lo},{hi}]")
    return bad


def format_report(summary: dict, title: str = "近 24 小时") -> str:
    if not summary.get("count"):
        return f"{title}没有记录"
    lines = [
        f"{title}（{summary['count']} 条）",
        f"平均单条 {summary['avg_chars']} 字",
        f"多段占比 {summary['multi_part_rate']:.0%}",
        f"问句结尾 {summary['question_rate']:.0%}",
        f"AI 腔 {summary['ai_mark_rate']:.0%}",
        f"markdown {summary['markdown_rate']:.0%}",
        f"冒号 {summary['colon_rate']:.0%} / 破折号 {summary['dash_rate']:.0%}",
    ]
    if "latency_p50_ms" in summary:
        lines.append(f"延迟 P50 {summary['latency_p50_ms']/1000:.1f}s / "
                     f"P90 {summary['latency_p90_ms']/1000:.1f}s")
    bad = verdict(summary)
    if bad:
        lines.append("不达标: " + "；".join(bad))
    return "\n".join(lines)
