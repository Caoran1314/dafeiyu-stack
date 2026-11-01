# 怎么发布

## 一、发到 GitHub（一条命令）

```bash
./scripts/publish-github.sh
```

脚本会：初始化仓库 → 提交 → 建 main 分支 → 用你的 SSH 推 → 打 tag。
如果仓库还不存在，它会告诉你打开哪个链接新建（**不要勾 README**）。

推完地址：`https://github.com/Caoran1314/dafeiyu-stack`

## 二、发 Docker Hub（一条命令）

```bash
./scripts/publish-dockerhub.sh
```

依次做：`docker login`（你自己输账号）→ build `caoran1314/dafeiyu-asr:1.0` → push。

> 这台机器没 Docker 也行：push 一个 `v*` tag，GitHub Actions 会自动构建并推送。
> 需要先在仓库 Settings → Secrets 里配 `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`。

Docker Hub 仓库页的描述，直接把根目录 `DOCKERHUB.md` 全文粘进去。

## 三、发插件到 AstrBot 市场

```bash
./scripts/prepare-marketplace.sh Caoran1314
```

会：
1. 把每个插件 `metadata.yaml` 的 `repo` 换成 `https://github.com/Caoran1314/<插件名>`
2. 在 `dist-plugins/` 生成 10 个 zip（根目录就是插件目录）

然后把每个插件单独建仓库（同名），把对应目录推上去，再把仓库地址提交到市场。

## 四、发布前检查清单

- [ ] `.env` 没提交（已在 `.gitignore`）
- [ ] `data/` 没提交
- [ ] 没有硬编码 QQ 号 / 密码 / token（本包已脱敏为 `CHANGE_ME`）
- [ ] `persona/` 里的人格是你愿意公开的版本
- [ ] `docker compose config` 能过
- [ ] README 里的端口与实际 compose 一致

## 五、版本与升级

```bash
git tag v1.1 && git push origin v1.1     # 触发镜像构建
docker compose pull && docker compose up -d
./scripts/install-plugins.sh && docker compose restart astrbot
```

升级前先 `./scripts/backup.sh`。
