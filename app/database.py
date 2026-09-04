"""SQLite 连接与会话管理。"""
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DB_PATH

# 确保数据库所在目录存在
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖:每个请求一个数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """建表。应用启动时调用一次。"""
    from app import models  # noqa: F401  确保模型被注册到 Base

    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate() -> None:
    """给已存在的表补上新字段(SQLite 的 create_all 不会自动加列)。"""
    with engine.connect() as conn:
        rows = conn.execute(text("PRAGMA table_info(users)")).fetchall()
        cols = {row[1] for row in rows}
        if "is_admin" not in cols:
            conn.execute(
                text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0")
            )
            conn.commit()
