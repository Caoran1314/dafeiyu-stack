# 人格与人生

| 文件 | 用途 |
|---|---|
| `persona_lover.md` | 人格正文（放 AstrBot 的「人格设定」里） |
| `life_story.md` | 22 年人生年表（喂给记忆库当种子） |

## 怎么用

1. 打开 AstrBot → 人格设定 → 新建 → 把 `persona_lover.md` 全文粘进 system prompt
2. **务必关闭安全模式**：`agent_runner.config.persona.safety_mode = false`
   （打开会让她动不动说"我不能……"，人设直接崩）
3. `life_story.md` 的内容可以用 `/记住 ...` 一条条喂，或者生成记忆库后导入

## 改人格

想换成别的人设，直接改这两个文件即可，插件不用动。
