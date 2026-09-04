# PhotoShare 部署包（Lighthouse / Ubuntu 24.04）

目标服务器：腾讯云 Lighthouse `lhins-8cs8gsar`（广州，2核2G，公网 IP `203.195.197.250`）
域名：`choujubuchou.online`（已解析到上述 IP，防火墙 80/443 已放行）

## 文件说明
- `deploy.sh` — 一键部署脚本（装 Caddy + 拉代码 + 建 venv + 生成 .env + 写配置 + 启动）
- `Caddyfile` — Caddy 反代配置（域名 → 127.0.0.1:8000，自动 HTTPS）
- `photoshare.service` — systemd 守护服务（开机自启、崩溃重启）

## 方式一：让我用 Lighthouse 连接器跑（推荐）
连接器恢复后，我会在服务器上执行：
```
curl -fsSL <本部署包地址> -o /tmp/deploy.sh && bash /tmp/deploy.sh
```
或直接由我分步执行 deploy.sh 里的步骤。

## 方式二：你自己 SSH 上服务器跑
```bash
# 1. 把本目录三个文件传到服务器 /tmp，然后：
bash /tmp/deploy.sh

# 2. 验证
curl -sk https://choujubuchou.online/ | head -c 200
systemctl status photoshare caddy
```

## 部署后必做（合规）
- 在网站底部加备案号：`<a href="https://beian.miit.gov.cn">你的备案号</a>`
  （在 `F:/photoshare/templates/base.html` 的 footer 里加，改完重新部署或 `git pull` 后重启服务）

## 常用运维
```bash
systemctl restart photoshare   # 改代码后重启
journalctl -u photoshare -f    # 看日志
/opt/photoshare/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000  # 手动前台跑
```
