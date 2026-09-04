"""应用配置。敏感信息全部从 .env 读取,不要把密钥写进代码。"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 加载项目根目录的 .env(存在才生效,不存在也不报错)
load_dotenv(BASE_DIR / ".env")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ---------- 腾讯云 COS(图片存储) ----------
COS_SECRET_ID = _env("COS_SECRET_ID")
COS_SECRET_KEY = _env("COS_SECRET_KEY")
COS_REGION = _env("COS_REGION", "ap-guangzhou")
# 桶名完整格式,形如 photoshare-1251234567
COS_BUCKET = _env("COS_BUCKET")
# 自定义 CDN 域名(可选),留空则使用 COS 默认域名
COS_DOMAIN = _env("COS_DOMAIN")

# ---------- 安全 ----------
# 会话签名密钥,上线前务必改成随机长字符串
SECRET_KEY = _env("SECRET_KEY", "please-change-this-to-a-random-string")

# ---------- 存储 ----------
DB_PATH = _env("DB_PATH", str(BASE_DIR / "data" / "app.db"))

# ---------- 上传限制 ----------
MAX_UPLOAD_MB = 10
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
