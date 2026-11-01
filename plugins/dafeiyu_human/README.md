# 大肥鱼拟人管线

三段处理，专治"一眼 AI"：

1. `on_llm_request`：随机延迟（像在打字）
2. `on_llm_response`：去 AI 腔、书面词换口语、注入错字
3. `on_decorating_result`：一句一行，交给平台分段发

## 配置

| 键 | 说明 |
|---|---|
| `delay_enable` / `delay_short_probability` | 短延迟概率 |
| `typo_rate` | 错字率 |
| `max_chars_per_line` | 单条字数上限 |
| `max_lines` | 最多几条 |

## 效果对照

| 之前 | 之后 |
|---|---|
| "好的，我明白了。那么……" | "行，我知道了" |
| 一大段 300 字 | 拆成 3 短条 |
| 每句带句号 | 不带标点，偶尔错字 |
