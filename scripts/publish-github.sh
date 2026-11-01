#!/usr/bin/env bash
# 一键推到 GitHub（用你自己的授权，脚本不接触任何凭据）
# 用法：./scripts/publish-github.sh [仓库名，默认 dafeiyu-stack]
set -euo pipefail
GH_USER="Caoran1314"
REPO_NAME="${1:-dafeiyu-stack}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

say() { printf "\033[36m%s\033[0m\n" "$*"; }
die() { printf "\033[31m%s\033[0m\n" "$*" >&2; exit 1; }

if [ ! -d .git ]; then
  say "初始化仓库…"
  git init -q
  git config user.name  "${GIT_NAME:-$GH_USER}"
  git config user.email "${GIT_EMAIL:-$GH_USER@users.noreply.github.com}"
fi

git add -A
git commit -q -m "林小鱼 v1.0：数字人格 QQ 机器人（心智层 + 部署包 + 文档）" || echo "（无改动可提交）"
git branch -M main

REMOTE="git@github.com:$GH_USER/$REPO_NAME.git"
if ! git remote get-url origin >/dev/null 2>&1; then
  git remote add origin "$REMOTE"
fi

say "推送到 $REMOTE …"
if ! git push -u origin main 2>/dev/null; then
  cat <<TXT

推送失败。通常是仓库还不存在。

去这里新建一个【空的、不要勾选 README】的仓库：
  https://github.com/new?name=$REPO_NAME

建完再跑一次：
  ./scripts/publish-github.sh $REPO_NAME

TXT
  exit 1
fi

git tag -a v1.0 -m "v1.0" 2>/dev/null || true
git push origin v1.0 2>/dev/null || true

say "完成：https://github.com/$GH_USER/$REPO_NAME"
