#!/usr/bin/env bash
# 全部上架后，删除 10 个发布仓库（代码仍在主仓库 plugins/ 下）
# 用法：GITHUB_TOKEN=ghp_xxx ./scripts/remove-market-repos.sh [--archive]
set -euo pipefail
TOKEN="${GITHUB_TOKEN:-}"
OWNER="${GH_OWNER:-Caoran1314}"
MODE="${1:-}"

[ -z "$TOKEN" ] && { echo "缺少 GITHUB_TOKEN"; exit 1; }

REPOS="dafeiyu_mindcore dafeiyu_hormone dafeiyu_persona_core dafeiyu_human
dafeiyu_brain dafeiyu_brain3d dafeiyu_eval dafeiyu_photo dafeiyu_room dafeiyu_voice"

echo "将处理以下仓库："
for r in $REPOS; do echo "  $OWNER/$r"; done
printf "确认？(yes/NO) "; read -r ans
[ "$ans" = "yes" ] || { echo "已取消"; exit 0; }

for r in $REPOS; do
  if [ "$MODE" = "--archive" ]; then
    curl -sS -X PATCH "https://api.github.com/repos/$OWNER/$r" \
      -H "Authorization: Bearer $TOKEN" -H "User-Agent: cleanup" \
      -H "Content-Type: application/json" -d '{"archived":true}' >/dev/null
    echo "  已归档 $OWNER/$r"
  else
    code=$(curl -sS -o /dev/null -w '%{http_code}' -X DELETE \
      "https://api.github.com/repos/$OWNER/$r" \
      -H "Authorization: Bearer $TOKEN" -H "User-Agent: cleanup")
    echo "  删除 $OWNER/$r → $code"
  fi
done

echo
echo "完成。主仓库仍是唯一源码：https://github.com/$OWNER/dafeiyu-stack"
