#!/usr/bin/env bash
# 部署后自检：容器状态 / 端口 / 模型 / 插件
set -uo pipefail
echo "== 容器 =="
docker compose ps
echo
echo "== 端口 =="
for p in 16185 16099 11434 9001 9880; do
  if timeout 2 bash -c "</dev/tcp/127.0.0.1/$p" 2>/dev/null; then
    echo "  ✓ $p 通"
  else
    echo "  ✗ $p 不通（看 docker compose logs）"
  fi
done
echo
echo "== Ollama 模型 =="
curl -s http://127.0.0.1:11434/api/tags | head -c 300 || echo "（未就绪）"
echo
echo "== ASR =="
curl -s http://127.0.0.1:9001/healthz || echo "（未就绪，模型可能还没下）"
