# 发布到 AstrBot 官方插件市场

官方市场和你现在的「自定义插件源」是两条完全不同的通道。

## 两条通道的差别

| | 自定义插件源（你现在用的） | 官方插件市场 |
|---|---|---|
| 谁来审 | 没人审，你自己发 | AstrBot 团队审 |
| 仓库形式 | **一个仓库装全部**（你现在这样） | **一个插件一个仓库**，且仓库根目录就是插件目录 |
| 安装来源 | 你的 `plugins.json` + `zips/` | AstrBot Cloud 从你的仓库自动构建 zip |
| 需要的账号 | 无 | AstrBot Cloud 账号 |
| 曝光 | 只有填了你源地址的人能看到 | 所有用户默认可见 |

## 硬性要求

| 要求 | 说明 |
|---|---|
| `metadata.yaml` | 必须有 `name` / `display_name` / `desc` / `version` / `author` / `repo` |
| `repo` | 指向**该插件自己的仓库**，不是 monorepo 的子目录 |
| 仓库根目录 | 必须是插件目录（`main.py` 在根） |
| zip 体积 | ≤ **16 MB**（超了 CI 直接拒） |
| 版本号 | 遵循语义化版本，如 `1.0.0` |
| 排除文件 | `.git`、`__pycache__`、`node_modules` 不要进包 |
| 平台声明 | `support_platforms` 要真实，写错会在别的平台装不上 |

## 流程

### 1. 注册 AstrBot Cloud

打开 https://cloud.astrbot.app/publish ，用 GitHub 或邮箱注册 / 登录。

### 2. 把插件拆成独立仓库

官方市场按**仓库根目录**打包，所以一个插件必须对应一个仓库根。

如果主仓库是 monorepo（像现在的 `dafeiyu-stack`），有两个做法：

**做法 A：拆仓库（推荐给要上架的插件）**

手动做法：

```bash
# 以 dafeiyu_mindcore 为例
cp -r dafeiyu-stack/plugins/dafeiyu_mindcore ~/dafeiyu_mindcore
cd ~/dafeiyu_mindcore
git init && git add -A && git commit -m "v1.0.0"
git remote add origin git@github.com:Caoran1314/dafeiyu_mindcore.git
git push -u origin main
git tag v1.0.0 && git push --tags
```

仓库里只需要插件文件 + `README.md` + `LICENSE` + `.gitignore`：

```gitignore
__pycache__/
*.pyc
.git/
node_modules/
.pytest_cache/
```

**做法 B：只用 Release zip（上不了官方市场）**

只在自定义源里分发，不追求官方市场曝光。

### 3. 提交

打开 https://cloud.astrbot.app/publish ，填：

| 字段 | 填什么 |
|---|---|
| 仓库地址 | `https://github.com/Caoran1314/dafeiyu_mindcore` |
| 分支 | `main` |
| 版本 | 跟 `metadata.yaml` 的 `version` 一致 |

系统会自己拉仓库、读 `metadata.yaml`、构建 zip、跑 CI 检查。

### 4. 等审核

- 自动检查：体积、元数据完整度、能否构建
- 人工检查：功能是否正常、描述是否清楚
- 通过后出现在市场，别人搜得到

### 5. 更新版本

改 `metadata.yaml` 的 `version` → 打 tag → 再提交一次。

市场按 `version` 判断是否为新版本；**版本号不变不会更新**。

## 哪些插件值得上架

不一定全上。按价值/维护成本排：

| 插件 | 建议 | 理由 |
|---|---|---|
| `dafeiyu_mindcore` | ✅ 强烈建议 | 记忆衰减 + 技能 SM2 是真差异化 |
| `dafeiyu_hormone` | ✅ 建议 | 四激素心境，别处没有 |
| `dafeiyu_persona_core` | ✅ 建议 | 人格钳位，通用性强 |
| `dafeiyu_human` | ✅ 建议 | 去 AI 腔，受众广 |
| `dafeiyu_voice` | ⚠️ 谨慎 | 依赖 GPT-SoVITS，别人装不好会来问 |
| `dafeiyu_photo` | ⚠️ 谨慎 | 依赖相册数据 |
| `dafeiyu_brain3d` | ⚠️ 体积 | 478 KB 还行，但依赖 brain.db |
| `dafeiyu_room` | ⚠️ 体积 | 461 KB，页面依赖较多 |
| `dafeiyu_brain` | ❌ 不必 | 已被 mindcore 覆盖 |
| `dafeiyu_eval` | ✅ 可上 | 只观测不干预，风险低 |

## 上架前检查清单

- [ ] `metadata.yaml` 的 `repo` 指向该插件自己的仓库
- [ ] 仓库根目录 `main.py` 能 import（本地跑一次 `python -c "import ast;ast.parse(open('main.py').read())"`）
- [ ] `.gitignore` 排除 `__pycache__`
- [ ] zip ≤ 16 MB
- [ ] `README.md` 写了安装方法和配置说明
- [ ] `LICENSE` 存在
- [ ] `support_platforms` 真实（只写真测过的）
- [ ] 没有硬编码的个人信息（QQ 号、token、路径）

## 常见被拒原因

| 原因 | 怎么修 |
|---|---|
| 体积超 16 MB | 压缩资源、拆出大文件、用 `.gitattributes` |
| `metadata.yaml` 缺字段 | 补 `desc` / `version` / `repo` |
| 装完报 import 错 | 缺依赖没写 `requirements.txt` |
| 描述太短 | 写清「它解决什么问题」，别只写「一个插件」 |
| 截图/资源缺失 | README 加界面截图 |
| 仓库不是插件根目录 | 把插件内容提到仓库根 |

## 和自定义源共存

两套可以同时用，互不冲突：

- **官方市场**：给陌生用户，装得省心
- **自定义源**：给自己/熟人，一次装全套 10 个

主仓库 `dafeiyu-stack` 继续作为**源码总仓**，拆出去的单插件仓库只作发布用途。
