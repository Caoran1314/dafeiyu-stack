#!/usr/bin/env bash
# 把插件整理成"可发布"状态：替换 repo 地址 + 打独立 zip
# 用法：./scripts/prepare-marketplace.sh <你的GitHub用户名>
set -euo pipefail
USER="${1:-}"
if [ -z "$USER" ]; then
  echo "用法：$0 <你的GitHub用户名>"
  exit 1
fi
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/dist-plugins"
mkdir -p "$OUT"

for d in "$HERE"/plugins/*/; do
  name="$(basename "$d")"
  # 1) 替换 repo
  sed -i.bak "s#https://github.com/Caoran1314/dafeiyu-plugins#https://github.com/$USER/$name#" \
    "$d/metadata.yaml" && rm -f "$d/metadata.yaml.bak"
  # 2) 打 zip（根目录就是插件目录，AstrBot 才能直接装）
  ( cd "$d" && zip -qr "$OUT/$name.zip" . -x "*.pyc" -x "__pycache__/*" )
  echo "  ✓ $name → dist-plugins/$name.zip"
done

cat > "$OUT/README.md" <<MD
# 插件包

每个 zip 对应一个插件仓库：\`https://github.com/$USER/<插件名>\`

上架 AstrBot 插件市场：把对应仓库地址提交即可，市场会读 \`metadata.yaml\`。
MD
echo
echo "全部完成，产物在 $OUT"
