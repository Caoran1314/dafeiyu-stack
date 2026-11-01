"""metrics 单测。"""
from metrics import TARGETS, format_report, measure, summarize, verdict


def t_measure_basic():
    m = measure("在\n刚睡醒，脑袋还有点糊")
    assert m["lines"] == 2 and m["multi_part"] == 1
    assert m["chars"] == len("在\n刚睡醒，脑袋还有点糊")
    assert m["ai_mark"] == 0 and m["markdown"] == 0


def t_measure_flags():
    assert measure("综上所述，答案是肯定的")["ai_mark"] == 1
    assert measure("## 标题")["markdown"] == 1
    assert measure("结论：好的")["colon"] == 1
    assert measure("这是——破折号")["dash"] == 1
    assert measure("你说呢？")["question_end"] == 1


def t_summary():
    rows = [
        {"avg_line_chars": 4, "multi_part": 1, "question_end": 0, "ai_mark": 0,
         "markdown": 0, "colon": 0, "dash": 0, "quote": 0, "latency_ms": 2000},
        {"avg_line_chars": 10, "multi_part": 0, "question_end": 1, "ai_mark": 1,
         "markdown": 0, "colon": 1, "dash": 0, "quote": 0, "latency_ms": 8000},
    ]
    s = summarize(rows)
    assert s["count"] == 2
    assert s["avg_chars"] == 7.0
    assert s["multi_part_rate"] == 0.5
    assert s["ai_mark_rate"] == 0.5
    assert s["latency_p50_ms"] > 0


def t_verdict_and_report():
    bad = summarize([{"avg_line_chars": 3, "multi_part": 0, "question_end": 1,
                      "ai_mark": 1, "markdown": 0, "colon": 0, "dash": 0,
                      "quote": 0, "latency_ms": 100}])
    assert verdict(bad), "应该报不达标"
    txt = format_report(bad, "测试")
    assert "测试" in txt and "不达标" in txt
    assert format_report({"count": 0}) == "近 24 小时没有记录"


def t_empty_rows():
    assert summarize([])["count"] == 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("t_")]
    for fn in fns:
        fn()
        print("ok", fn.__name__)
    print(f"\n全部通过（{len(fns)} 项）")
