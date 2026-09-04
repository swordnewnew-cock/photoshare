import os

os.environ["ADMIN_USERNAME"] = "boss"
os.environ["ADMIN_PASSWORD"] = "bosspass123"
os.environ["DB_PATH"] = "/tmp/admin_test.db"
os.environ["SECRET_KEY"] = "x" * 32
os.environ["MAX_UPLOAD_MB"] = "10"

if os.path.exists("/tmp/admin_test.db"):
    os.remove("/tmp/admin_test.db")

from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.main import app
from app.models import Post, User

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
)


def pid_from(resp):
    return resp.headers["location"].rstrip("/").split("/")[-1]


with TestClient(app) as boss, TestClient(app) as alice:
    # 管理员应已自动创建并可以登录
    r = boss.post("/login", data={"username": "boss", "password": "bosspass123"}, follow_redirects=False)
    assert r.status_code == 303, ("admin login failed", r.status_code, r.text[:200])
    assert boss.get("/").status_code == 200

    # 普通用户注册
    r = alice.post("/register", data={"username": "alice", "password": "alice123"}, follow_redirects=False)
    assert r.status_code == 303, ("alice register failed", r.status_code)

    # 各发一张照片
    r = boss.post("/new", files={"file": ("b.png", PNG, "image/png")},
                  data={"caption": "boss photo"}, follow_redirects=False)
    boss_post = pid_from(r)
    r = alice.post("/new", files={"file": ("a.png", PNG, "image/png")},
                   data={"caption": "alice photo"}, follow_redirects=False)
    alice_post = pid_from(r)

    # 管理员删普通用户的帖子 -> 应成功
    r = boss.post(f"/post/{alice_post}/delete", follow_redirects=False)
    assert r.status_code == 303
    db = SessionLocal()
    assert db.get(Post, int(alice_post)) is None, "admin failed to delete others post"
    assert db.get(Post, int(boss_post)) is not None
    db.close()

    # 普通用户删管理员的帖子 -> 不应删除
    r = alice.post(f"/post/{boss_post}/delete", follow_redirects=False)
    assert r.status_code == 303
    db = SessionLocal()
    assert db.get(Post, int(boss_post)) is not None, "non-admin deleted admin post!"
    db.close()

    # 管理员登录态正确
    db = SessionLocal()
    boss_row = db.query(User).filter(User.username == "boss").first()
    assert boss_row is not None and boss_row.is_admin is True
    db.close()

print("ADMIN_TEST_OK")
