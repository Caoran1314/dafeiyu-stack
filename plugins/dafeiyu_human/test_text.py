"""dafeiyu_human.text 的单元测试：不依赖 AstrBot，直接 python 跑。"""
import random

from text import (
    apply_typos,
    ban_punctuation,
    drop_slop,
    polish,
    split_lines,
    strip_markdown,
)


def t_basic_polish():
    raw = ("首先，我们来分析一下：这个问题**很重要**。\n"
           "希望这个回答对你有帮助。\n"
           "我觉得非常可以\n"
           "你说呢？")
    out, meta = polish(raw, {"typo_rate": 0.0}, random.Random(1))
    assert "首先" not in out, out
    assert "对你有帮助" not in out, out
    assert "：" not in out and "**" not in out, out
    assert "。" not in out, out
    assert "\n" in out, out
    assert all(len(x) <= 30 for x in out.splitlines()), out


def t_punctuation():
    s = ban_punctuation('他说：“走吧”——然后呢：好的。')
    assert "：" not in s and "——" not in s and '"' not in s, s
    assert not s.endswith("。"), s


def t_slop_all_removed_fallback():
    raw = "首先，我们要客观。其次，综合考虑。综上所述，答案是肯定的。"
    out, meta = polish(raw, {"typo_rate": 0.0}, random.Random(2))
    assert out, "不能返回空"
    assert meta["fallback"] or out.strip(), meta


def t_markdown():
    s = strip_markdown("# 标题\n- 列表项\n1. 有序项\n**加粗**")
    assert "#" not in s and "**" not in s, s
    assert "标题" in s and "列表项" in s


def t_split():
    lines = split_lines("这是一句很长很长的话" * 5, 20)
    assert lines and all(len(x) <= 20 for x in lines), lines


def t_typo():
    out, n = apply_typos("我觉得你在做什么", 1.0, random.Random(3))
    assert n > 0, out
    assert out != "我觉得你在做什么", out


def t_typo_protect_url():
    src = "看这个 https://example.com/在吗 很好"
    out, _ = apply_typos(src, 1.0, random.Random(4))
    assert "https://example.com/在吗" in out, out


def t_empty():
    out, meta = polish("", None, None)
    assert out == "" and meta["fallback"]


def t_drop_slop_keeps_rest():
    s, hits = drop_slop("在\n有什么可以帮您的\n饿")
    assert "有什么可以帮您" not in s
    assert "饿" in s and hits


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for fn in fns:
        fn()
        print("ok", fn.__name__)
    print(f"\n全部通过（{len(fns)} 项）")
