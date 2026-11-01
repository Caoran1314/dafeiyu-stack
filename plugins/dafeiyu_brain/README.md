# 大肥鱼记忆大脑

最基础的一层：facts + episodes 两张表，加核心锚点。

## 命令

| 命令 | 作用 |
|---|---|
| `/brain` | 看统计 |
| `/brain search 关键词` | 查记忆 |
| `/brain export` | 导出可迁移 JSON |

## 配置要点

- `memory_inject`：是否把召回的记忆注入上下文。**用心智内核时设为 false**
- `recall_min_score`：召回阈值
- `batch_size`：多少句触发一次提取

## 和心智内核的关系

心智内核把这里当**只读种子**导入。两者同时开时，
`memory_inject=false` 可避免重复注入。
