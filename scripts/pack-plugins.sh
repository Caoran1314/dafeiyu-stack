#!/usr/bin/env bash
# 把 plugins/ 下每个插件打成 zip（用于发 Release 或单独上传）
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/dist-plugins"
rm -rf "$OUT" && mkdir -p "$OUT"
for d in "$HERE"/plugins/*/; do
  name="$(basename "$d")"
  ( cd "$d" && zip -qr "$OUT/$name.zip" . -x "*.pyc" -x "__pycache__/*" )
  echo "  ✓ $name.zip"
done
echo "产物在 $OUT"
