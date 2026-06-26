#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "请使用 root 或具备 sudo 权限的账号运行：sudo bash scripts/init-server.sh"
  exit 1
fi

apt-get update
apt-get install -y ca-certificates curl gnupg lsb-release ufw git

install -m 0755 -d /etc/apt/keyrings
if [[ ! -f /etc/apt/keyrings/docker.gpg ]]; then
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
fi

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker

ufw allow OpenSSH
if [[ -n "${MMN_ALLOWED_CIDR:-}" ]]; then
  ufw allow from "$MMN_ALLOWED_CIDR" to any port "${MMN_HTTP_PORT:-8765}" proto tcp
else
  ufw allow "${MMN_HTTP_PORT:-8765}"/tcp
fi
ufw --force enable

mkdir -p /opt/mmn-perception-engine

echo "服务器初始化完成。请确认阿里云安全组已开放 SSH 22 和测试端口 ${MMN_HTTP_PORT:-8765}。"
