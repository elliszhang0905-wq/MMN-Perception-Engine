#!/bin/bash
set -euo pipefail

BASE_URL="${1:-${MMN_CLOUD_URL:-}}"

if [[ -z "$BASE_URL" ]]; then
  echo "用法：bash scripts/test_mmn_cloud.sh http://服务器公网IP:8765"
  echo "或：MMN_CLOUD_URL=https://mmnsh.com bash scripts/test_mmn_cloud.sh"
  exit 1
fi

BASE_URL="${BASE_URL%/}"

check_url() {
  local label="$1"
  local url="$2"
  local expected="$3"
  local code
  code=$(curl -k -sS -m 10 -o /tmp/mmn_cloud_check_body.txt -w "%{http_code}" "$url" || true)
  if [[ "$code" == "$expected" ]]; then
    echo "通过：${label} ${url}"
  else
    echo "失败：${label} ${url}，HTTP ${code}"
    cat /tmp/mmn_cloud_check_body.txt 2>/dev/null || true
    exit 1
  fi
}

echo "开始检查 MMN 云端演示地址：${BASE_URL}"
check_url "首页" "${BASE_URL}/" "200"
check_url "健康接口" "${BASE_URL}/api/health" "200"

echo "云端基础可访问性检查通过。"
echo "如手机或客户设备仍打不开，请继续检查：域名解析、安全组 80/443/8765、服务器 Docker 服务、备案与 HTTPS 配置。"
