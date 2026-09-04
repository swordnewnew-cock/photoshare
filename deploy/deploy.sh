#!/usr/bin/env bash
# PhotoShare 一键部署脚本（Ubuntu 24.04 / Lighthouse 2核2G）
# 用法: bash deploy.sh
# 前置: 已放行 80/443 防火墙、域名已解析到本机公网 IP、已 git clone 本仓库到 /opt/photoshare
set -e

DOMAIN="choujubuchou.online"
APP_DIR="/opt/photoshare"
REPO="https://github.com/swordnewnew-cock/photoshare.git"
PORT=8000

echo "== [1/8] 系统依赖 =="
apt-get update -y
apt-get install -y python3-venv python3-pip git curl gnupg

echo "== [2/8] 安装 Caddy =="
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudflare.com/rpm/PHCk3pFIAD2G7jsR/stable/gpg' | gpg --dearmor -o /usr/share/keyrings/caddy-stable.gpg
echo "deb [signed-by=/usr/share/keyrings/caddy-stable.gpg] https://dl.cloudflare.com/rpm/PHCk3pFIAD2G7jsR/stable/debian/ any-version main" >/etc/apt/sources.list.d/caddy-stable.list
apt-get update -y
apt-get install -y caddy

echo "== [3/8] 拉取代码（有则更新，无则克隆）=="
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull
else
  git clone "$REPO" "$APP_DIR"
fi

echo "== [4/8] 虚拟环境 + 依赖 =="
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -U pip -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -q

echo "== [5/8] 生成 .env（仅首次，已存在则保留）=="
if [ ! -f "$APP_DIR/.env" ]; then
  cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=$(python3 -c "import secrets;print(secrets.token_hex(32))")
DB_PATH=$APP_DIR/data/app.db
MAX_UPLOAD_MB=10
EOF
  echo ".env 已生成"
else
  echo ".env 已存在，保留"
fi

echo "== [6/8] Caddy 反代配置 =="
cat > /etc/caddy/Caddyfile <<EOF
$DOMAIN {
    encode gzip
    reverse_proxy 127.0.0.1:$PORT
}
EOF

echo "== [7/8] systemd 服务 =="
cat > /etc/systemd/system/photoshare.service <<EOF
[Unit]
Description=PhotoShare FastAPI
After=network.target

[Service]
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $PORT
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "== [8/8] 启动服务 =="
systemctl daemon-reload
systemctl enable photoshare caddy
systemctl restart photoshare caddy
sleep 3
systemctl is-active photoshare && echo "photoshare: OK" || echo "photoshare: FAIL"
systemctl is-active caddy && echo "caddy: OK" || echo "caddy: FAIL"

echo "== 验证 =="
curl -sk "https://$DOMAIN/" | head -c 200
echo ""
echo "部署完成 -> https://$DOMAIN"
