#!/usr/bin/env bash
# 构建并推送 ASR 镜像到 Docker Hub
# 用法：./scripts/publish-dockerhub.sh [DockerHub用户名] [tag]
#   用户名默认取 $DOCKER_USER 或 caoran1314
set -euo pipefail
DH_USER="${1:-${DOCKER_USER:-caoran1314}}"
TAG="${2:-1.0}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
IMG="$DH_USER/dafeiyu-asr:$TAG"

say() { printf "\033[36m%s\033[0m\n" "$*"; }

command -v docker >/dev/null 2>&1 || {
  echo "这台机器没有 docker。两种办法："
  echo "  1) 在装了 Docker 的机器上跑这个脚本"
  echo "  2) 用 GitHub Actions 自动构建（见 .github/workflows/docker.yml，配好 secrets 即可）"
  exit 1
}

say "1/4 登录 Docker Hub（自己输入账号密码，脚本不保存）"
docker login || { echo "登录失败"; exit 1; }

say "2/4 构建 $IMG"
docker build -t "$IMG" -t "$DH_USER/dafeiyu-asr:latest" "$HERE/asr"

say "3/4 推送"
docker push "$IMG"
docker push "$DH_USER/dafeiyu-asr:latest"

say "4/4 完成"
cat <<TXT

镜像地址：
  $IMG
  $DH_USER/dafeiyu-asr:latest

别人用的时候，把 docker-compose.yml 里这段：

  asr:
    build: ./asr

换成：

  asr:
    image: $IMG

Docker Hub 仓库页的说明文字用仓库根目录的 DOCKERHUB.md 粘贴即可。
TXT
