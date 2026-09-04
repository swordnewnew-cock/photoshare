"""密码哈希与登录会话。

密码:PBKDF2-HMAC-SHA256 + 随机盐(用标准库实现,不需要装 bcrypt,避免踩版本坑)
会话:itsdangerous 签名 Cookie,服务端无状态
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.config import SECRET_KEY
from app.database import get_db
from app.models import User

serializer = URLSafeTimedSerializer(SECRET_KEY)

SESSION_COOKIE = "session"
SESSION_MAX_AGE = 7 * 24 * 3600  # 登录状态保持 7 天
PBKDF2_ROUNDS = 100_000


# ---------------- 密码 ----------------
def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    """返回 (哈希值, 盐)。"""
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ROUNDS)
    return dk.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    dk, _ = hash_password(password, salt)
    return hmac.compare_digest(dk, password_hash)


# ---------------- 会话 ----------------
def create_session(response: Response, user_id: int) -> None:
    """下发登录 Cookie。浏览器关闭再打开仍有效(持久化 7 天)。"""
    token = serializer.dumps({"uid": user_id})
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=SESSION_MAX_AGE)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_MAX_AGE,        # 相对秒数,主流浏览器
        expires=expires_at,             # 绝对过期时间,某些代理/老浏览器只认这个
        path="/",                       # 全站都带
        httponly=True,                  # 防 XSS 偷 cookie
        samesite="lax",                 # 防 CSRF,允许链接跳转
    )


def destroy_session(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE)


def current_user(request: Request, db: Session) -> User | None:
    """取当前登录用户,未登录返回 None。"""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
    return db.get(User, data.get("uid"))


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    """需要登录:未登录时 303 重定向到登录页(303 会强制转成 GET)。"""
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """需要管理员:未登录跳登录,已登录但非管理员跳首页。"""
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    if not user.is_admin:
        raise HTTPException(status_code=303, headers={"Location": "/"})
    return user
