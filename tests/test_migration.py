import os
import sqlite3

os.environ["DB_PATH"] = "/tmp/mig_test.db"
if os.path.exists("/tmp/mig_test.db"):
    os.remove("/tmp/mig_test.db")

# 模拟“旧版数据库”: users 表没有 is_admin 字段
con = sqlite3.connect("/tmp/mig_test.db")
con.execute(
    "CREATE TABLE users ("
    "id INTEGER PRIMARY KEY, username VARCHAR(32) UNIQUE, "
    "password_hash VARCHAR(128), salt VARCHAR(32), created_at DATETIME)"
)
con.commit()
con.close()

import app.database as dbmod

dbmod.init_db()  # 内部会调用 _migrate 补列

con = sqlite3.connect("/tmp/mig_test.db")
cols = [r[1] for r in con.execute("PRAGMA table_info(users)").fetchall()]
con.close()

assert "is_admin" in cols, f"migration failed, cols={cols}"
print("MIGRATION_OK", cols)
