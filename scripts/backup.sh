#!/usr/bin/env bash
# 备份她的全部状态（记忆库、心境、人格、生命卡）
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
DATA="${DATA_ROOT:-$HERE/data}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$HERE/backups/$STAMP"
mkdir -p "$OUT"
cp -a "$DATA/astrbot/plugin_data" "$OUT/" 2>/dev/null || true
cp "$DATA/astrbot/data_v4.db" "$OUT/" 2>/dev/null || true
echo "已备份到 $OUT"
du -sh "$OUT" 2>/dev/null || true
