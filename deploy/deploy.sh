#!/usr/bin/env bash
# PhotoShare 部署脚本(国内 Lighthouse 适配版)
# 前置: 代码已在 CodeUp(国内,可达); 域名已解析; 防火墙 80 已开
# 说明: 从 CodeUp 克隆 + Nginx 反代(腾讯 apt 源) + pip 走腾讯镜像 + 先 HTTP 起站
# 用法: sudo bash /opt/photoshare/deploy/deploy.sh
set -e

DOMAIN="choujubuchou.online"
APP_DIR="/opt/photoshare"
REPO="https://codeup.aliyun.com/623be72f56f85235f7dd59c0/swordnewnew-cock/photoshare.git"
PORT=8000
PIP_MIRROR="https://mirrors.tencent.com/pypi/simple/"

echo "== [1/8] 系统依赖(腾讯 apt 源) =="
apt-get update -y
apt-get install -y python3-venv python3-pip nginx

echo "== [2/8] 拉取代码(有则更新,无则克隆) =="
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull
else
  git clone "$REPO" "$APP_DIR"
fi

echo "== [3/8] 虚拟环境 + 依赖(腾讯 pip 镜像) =="
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -U pip -i "$PIP_MIRROR" -q
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt" -i "$PIP_MIRROR" -q

echo "== [4/8] 生成 .env =="
if [ ! -f "$APP_DIR/.env" ]; then
  python3 -c "import secrets;open('$APP_DIR/.env','w').write('SECRET_KEY='+secrets.token_hex(32)+'\nDB_PATH=$APP_DIR/data/app.db\nMAX_UPLOAD_MB=10\n')"
  echo ".env 已生成"
else
  echo ".env 已存在,保留"
fi

echo "== [5/8] Nginx 反代配置 =="
cat > /etc/nginx/sites-available/photoshare <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    client_max_body_size 12m;
    location /static {
        alias $APP_DIR/static;
    }
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
ln -sf /etc/nginx/sites-available/photoshare /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "== [6/8] systemd 服务 =="
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

echo "== [7/8] 启动 =="
systemctl daemon-reload
systemctl enable photoshare nginx
systemctl restart photoshare nginx
sleep 3
systemctl is-active photoshare && echo "photoshare: OK" || echo "photoshare: FAIL"
systemctl is-active nginx && echo "nginx: OK" || echo "nginx: FAIL"

echo "== [8/8] 验证 =="
curl -s "http://$DOMAIN/" | head -c 200
echo ""
echo "部署完成 -> http://$DOMAIN  (HTTPS 后续用腾讯云免费证书开启)"
