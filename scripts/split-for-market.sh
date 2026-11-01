#!/usr/bin/env bash
# 把指定插件拆成独立仓库，用于提交 AstrBot 官方市场
# 用法：GITHUB_TOKEN=ghp_xxx ./scripts/split-for-market.sh dafeiyu_mindcore dafeiyu_hormone
#   不给参数则默认拆 4 个旗舰插件
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PLUG="$HERE/plugins"
OWNER="${GH_OWNER:-Caoran1314}"
TOKEN="${GITHUB_TOKEN:-}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ -z "$TOKEN" ]; then
  echo "缺少 GITHUB_TOKEN 环境变量。"
  echo "去 https://github.com/settings/tokens 生成一个带 repo 权限的 classic token，然后："
  echo "  GITHUB_TOKEN=ghp_xxx $0"
  exit 1
fi

if [ $# -eq 0 ]; then
  set -- dafeiyu_mindcore dafeiyu_hormone dafeiyu_persona_core dafeiyu_human
fi

api() {
  local method="$1" path="$2"
  curl -sS -X "$method" "https://api.github.com$path" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "User-Agent: split-for-market"
}

for name in "$@"; do
  src="$PLUG/$name"
  [ -d "$src" ] || { echo "  ✗ 没有 $name"; continue; }
  work="$TMP/$name"
  cp -r "$src" "$work"
  rm -rf "$work/__pycache__" "$work/.git"

  # 创建仓库（已存在则跳过）
  if api GET "/repos/$OWNER/$name" | grep -q '"message": *"Not Found"'; then
    api POST "/user/repos" -d "{\"name\":\"$name\",\"private\":false,\"auto_init\":false}" >/dev/null
    echo "  新建仓库 $OWNER/$name"
  fi

  cd "$work"
  git init -q
  git config user.name "$OWNER"
  git config user.email "noreply@github.com"
  git add -A
  git commit -q -m "$name 发布版"
  git branch -M main
  git remote add origin "https://x-access-token:$TOKEN@github.com/$OWNER/$name.git"
  GIT_TERMINAL_PROMPT=0 git -c credential.helper= push -f -u origin main >/dev/null 2>&1
  git tag -f "v$(grep -E '^version:' metadata.yaml | head -1 | sed 's/version: *v*//')" >/dev/null 2>&1 || true
  git -c credential.helper= push -f origin --tags >/dev/null 2>&1 || true
  echo "  ✓ $OWNER/$name"
  cd "$HERE"
done

cat <<TXT

完成。接下来到 https://cloud.astrbot.app/publish 逐个提交：
  选仓库 → 解析 → 确认元数据 → 发布

TXT
