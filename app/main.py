"""FastAPI 应用入口与全部路由。"""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import auth, cos_client
from app.config import ALLOWED_IMAGE_TYPES, BASE_DIR, MAX_UPLOAD_MB
from app.database import SessionLocal, get_db, init_db
from app.models import Comment, Post, User


@asynccontextmanager
async def lifespan(_: FastAPI):
    """启动时建表,并自动创建管理员账号(若已配置)。"""
    init_db()
    _bootstrap_admin()
    yield


def _bootstrap_admin() -> None:
    """根据 .env 的 ADMIN_USERNAME / ADMIN_PASSWORD 创建管理员(幂等)。"""
    from app.auth import hash_password
    from app.config import ADMIN_PASSWORD, ADMIN_USERNAME
    from app.models import User

    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == ADMIN_USERNAME).first():
            pwd_hash, salt = hash_password(ADMIN_PASSWORD)
            db.add(
                User(
                    username=ADMIN_USERNAME,
                    password_hash=pwd_hash,
                    salt=salt,
                    is_admin=True,
                )
            )
            db.commit()
    finally:
        db.close()


app = FastAPI(title="PhotoShare", lifespan=lifespan)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def _render(name: str, request: Request, db: Session, **ctx) -> HTMLResponse:
    """渲染模板,统一注入当前登录用户。"""
    ctx.setdefault("user", auth.current_user(request, db))
    return templates.TemplateResponse(request=request, name=name, context=ctx)


# ==================== 首页:图片流 ====================
@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    posts = db.query(Post).order_by(Post.created_at.desc()).all()
    user = auth.current_user(request, db)
    return templates.TemplateResponse(
        request=request, name="index.html", context={"posts": posts, "user": user}
    )


# ==================== 注册 ====================
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, db: Session = Depends(get_db)):
    return _render("register.html", request, db, error=None)


@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip()
    if not username or not password:
        return _render("register.html", request, db, error="用户名和密码不能为空")
    if len(password) < 6:
        return _render("register.html", request, db, error="密码至少 6 位")
    if db.query(User).filter(User.username == username).first():
        return _render("register.html", request, db, error="用户名已被占用")

    pwd_hash, salt = auth.hash_password(password)
    user = User(username=username, password_hash=pwd_hash, salt=salt)
    db.add(user)
    db.commit()

    resp = RedirectResponse("/", status_code=303)
    auth.create_session(resp, user.id)
    return resp


# ==================== 登录 / 登出 ====================
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    return _render("login.html", request, db, error=None)


@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user or not auth.verify_password(password, user.password_hash, user.salt):
        return _render("login.html", request, db, error="用户名或密码错误")

    resp = RedirectResponse("/", status_code=303)
    auth.create_session(resp, user.id)
    return resp


@app.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=303)
    auth.destroy_session(resp)
    return resp


# ==================== 发帖 ====================
@app.get("/new", response_class=HTMLResponse)
def new_post_page(request: Request, db: Session = Depends(get_db),
                  user: User = Depends(auth.require_user)):
    return _render("new.html", request, db, error=None)


@app.post("/new", response_class=HTMLResponse)
async def create_post(
    request: Request,
    caption: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(auth.require_user),
):
    content_type = file.content_type or ""
    if content_type not in ALLOWED_IMAGE_TYPES:
        return _render("new.html", request, db, error="只支持 JPG / PNG / GIF / WebP")

    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        return _render("new.html", request, db, error=f"图片不能超过 {MAX_UPLOAD_MB} MB")

    image_url = cos_client.upload_image(data, content_type)
    post = Post(user_id=user.id, image_url=image_url, caption=caption.strip())
    db.add(post)
    db.commit()
    return RedirectResponse(f"/post/{post.id}", status_code=303)


# ==================== 帖子详情 + 评论 ====================
@app.get("/post/{post_id}", response_class=HTMLResponse)
def post_detail(post_id: int, request: Request, db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post:
        return RedirectResponse("/", status_code=303)
    user = auth.current_user(request, db)
    return templates.TemplateResponse(
        request=request, name="post.html", context={"post": post, "user": user}
    )


@app.post("/post/{post_id}/comment")
def add_comment(
    post_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(auth.require_user),
):
    post = db.get(Post, post_id)
    if post and content.strip():
        db.add(Comment(post_id=post_id, user_id=user.id, content=content.strip()))
        db.commit()
    return RedirectResponse(f"/post/{post_id}", status_code=303)


# ==================== 删帖(仅作者本人) ====================
@app.post("/post/{post_id}/delete")
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(auth.require_user),
):
    post = db.get(Post, post_id)
    # 作者本人或管理员均可删除
    if post and (post.user_id == user.id or user.is_admin):
        db.delete(post)
        db.commit()
    return RedirectResponse("/", status_code=303)
