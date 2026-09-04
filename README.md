# PhotoShare

登录后可以发照片 + 文案、互相评论的小网站。

## 技术栈

| 层 | 选型 |
|---|---|
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | SQLite(单文件,零配置) |
| 图片存储 | 腾讯云 COS(未配置时自动降级存本地) |
| 前端 | Jinja2 模板 + 原生 CSS |
| 部署 | Caddy(自动 HTTPS)+ systemd |

## 本地跑起来

```bash
# 1. 建虚拟环境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate  # Linux / macOS

# 2. 装依赖
pip install -r requirements.txt

# 3. 建配置文件(可选,不配 COS 也能跑)
cp .env.example .env

# 4. 启动
uvicorn app.main:app --reload
```

浏览器打开 **http://127.0.0.1:8000**

首次启动会自动在 `data/` 下创建 `app.db` 并建表。

## 目录结构

```
photoshare/
├── app/
│   ├── main.py        路由(首页/注册/登录/发帖/评论/删帖)
│   ├── models.py      数据表(User / Post / Comment)
│   ├── auth.py        密码哈希 + 登录会话
│   ├── database.py    SQLite 连接
│   ├── cos_client.py  图片上传(COS 或本地)
│   └── config.py      配置读取
├── templates/         Jinja2 页面
├── static/
│   ├── style.css
│   └── uploads/       未配 COS 时图片存这里
├── data/              SQLite 数据库(不进 Git)
└── .env.example       配置模板
```

## 接入腾讯云 COS

默认不配 COS 时图片存本地 `static/uploads`,开发调试够用。

上线前建议接 COS —— 不占服务器磁盘、不耗服务器带宽、几块钱一年:

1. 腾讯云控制台 → 对象存储 → 建桶,**权限选"公有读私有写"**
2. CAM 新建子账号密钥,只授权这个桶(**别用主账号密钥**)
3. 把 `SecretId / SecretKey / 地域 / 桶名` 填进 `.env`

代码会自动切换到 COS,无需改动任何代码。

## 部署到 Lighthouse

1. 服务器装好 Python,把代码传上去
2. 装依赖、配好 `.env`
3. uvicorn 只监听 `127.0.0.1:8000`,由 Caddy 反代
4. Caddyfile 全文就三行:

```
你的域名.com {
    reverse_proxy 127.0.0.1:8000
}
```

5. 用 systemd 守护进程,开机自启、崩了自动拉起

> ⚠️ 国内地域服务器记得**先做 ICP 备案**(7-20 天),否则域名访问 80/443 会被拦截。备案期间可用 `IP:端口` 自测。

## 安全提醒

- `.env` 和 `data/` 已在 `.gitignore` 中,不会被提交
- 上线前务必把 `SECRET_KEY` 换成随机值:
  ```bash
  python -c "import secrets;print(secrets.token_hex(32))"
  ```
- 密钥一旦泄露,立即去腾讯云控制台吊销
