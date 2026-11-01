#!/usr/bin/env bash
# 一行安装：curl -fsSL <raw地址>/install.sh | bash
# 可选环境变量：
#   REPO=https://github.com/<user>/dafeiyu-stack   仓库地址
#   DIR=~/dafeiyu                                  安装目录
#   NO_START=1                                     只装不启动
set -euo pipefail

REPO="${REPO:-https://github.com/Caoran1314/dafeiyu-stack}"
DIR="${DIR:-$HOME/dafeiyu}"
NO_START="${NO_START:-0}"

say() { printf "\033[36m%s\033[0m\n" "$*"; }
die() { printf "\033[31m%s\033[0m\n" "$*" >&2; exit 1; }

say "== 林小鱼 · 安装器 =="

# 依赖检查
command -v docker >/dev/null 2>&1 || die "没装 Docker。先装 Docker 再来。"
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 不可用（需要 'docker compose' 子命令）。"
command -v curl >/dev/null 2>&1 || die "没装 curl。"
command -v unzip >/dev/null 2>&1 || say "提示：没装 unzip，将用 docker 解压"

say "安装到：$DIR"
mkdir -p "$DIR"
cd "$DIR"

if [ ! -f docker-compose.yml ]; then
  say "拉取发行包…"
  TMP="$(mktemp -d)"
  curl -fsSL "$REPO/archive/refs/heads/main.zip" -o "$TMP/src.zip" || die "下载失败，检查 REPO 地址"
  if command -v unzip >/dev/null 2>&1; then
    unzip -q "$TMP/src.zip" -d "$TMP"
  else
    docker run --rm -v "$TMP":/w -w /w alpine unzip -q src.zip
  fi
  SRC="$(find "$TMP" -maxdepth 1 -type d -name '*stack*' | head -1)"
  [ -n "$SRC" ] || die "压缩包结构不对"
  cp -a "$SRC/." "$DIR/"
  rm -rf "$TMP"
fi

if [ ! -f .env ]; then
  cp .env.example .env
  say "已生成 .env（之后可以改端口和数据目录）"
fi

if [ "$NO_START" != "1" ]; then
  say "启动容器…"
  docker compose pull --quiet || true
  docker compose up -d
  say "装插件…"
  ./scripts/install-plugins.sh || true
  say "重启 AstrBot 让插件生效…"
  docker compose restart astrbot || true

  IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  IP="${IP:-127.0.0.1}"
  P_AST="$(grep -E '^ASTRBOT_WEBUI_PORT=' .env | cut -d= -f2 || echo 16185)"
  P_NAP="$(grep -E '^NAPCAT_WEBUI_PORT=' .env | cut -d= -f2 || echo 16099)"
  cat <<TXT

======================================
  装好了，三步收尾：

  1) 扫码登录 QQ
     http://$IP:${P_NAP:-16099}

  2) 配模型 + 装人格
     http://$IP:${P_AST:-16185}
     人格里粘 persona/persona_lover.md
     ⚠ 记得把 safety_mode 设成 false

  3) 自检
     cd $DIR && ./scripts/healthcheck.sh

  常用命令（QQ 里发）：/心智状态
======================================
TXT
else
  say "已装好但未启动。手动执行：cd $DIR && docker compose up -d"
fi
