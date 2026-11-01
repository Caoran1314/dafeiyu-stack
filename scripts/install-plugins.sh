#!/usr/bin/env bash
# 把 plugins/ 下的插件装进 AstrBot 数据目录
# 用法：./scripts/install-plugins.sh [ASTRBOT_DATA 路径，默认 ./data/astrbot]
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${1:-$HERE/data/astrbot}"
DEST="$DATA_DIR/plugins"

mkdir -p "$DEST"
count=0
for d in "$HERE"/plugins/*/; do
  name="$(basename "$d")"
  rm -rf "$DEST/$name"
  cp -r "$d" "$DEST/$name"
  count=$((count+1))
  echo "  ✓ $name"
done
echo "已安装 $count 个插件到 $DEST"
echo
echo "接下来："
echo "  1. 打开 AstrBot WebUI → 插件 → 逐个启用"
echo "  2. dafeiyu_hormone / dafeiyu_mindcore / dafeiyu_persona_core 三者要一起启用"
echo "  3. dafeiyu_mindcore 默认 inject_mode=primary，它会接管人格+心境+记忆的装配"
