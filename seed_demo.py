"""临时演示数据：写入一条示例用户 + 8 张示例照片(远程占位图)。用完可删除。"""
import datetime as dt

from app.database import SessionLocal, init_db
from app.models import Post, User

SAMPLES = [
    ("https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=serene%20mountain%20lake%20at%20sunrise%2C%20snow-capped%20peaks%20reflected%20in%20calm%20water%2C%20professional%20landscape%20photography&image_size=landscape_16_9", "清晨的山湖，倒影如镜。"),
    ("https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cozy%20flat%20lay%20of%20specialty%20coffee%20with%20latte%20art%20on%20wooden%20table%2C%20top-down%2C%20warm%20natural%20light&image_size=square", "午后的一杯拿铁。"),
    ("https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=vibrant%20city%20street%20at%20night%20with%20neon%20lights%20and%20rain%20reflections%2C%20cinematic%20urban%20photography&image_size=portrait_4_3", "雨夜霓虹。"),
    ("https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=golden%20beach%20at%20sunset%20with%20gentle%20waves%20and%20silhouetted%20palm%20trees%2C%20travel%20photography&image_size=landscape_4_3", "棕榈树下的黄昏。"),
    ("https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cute%20orange%20tabby%20cat%20sitting%20by%20a%20sunny%20window%2C%20shallow%20depth%20of%20field%2C%20pet%20portrait%20photography&image_size=square", "晒着太阳的橘猫。"),
    ("https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=colorful%20tulip%20field%20in%20soft%20morning%20light%20with%20bokeh%20background%2C%20flower%20photography&image_size=portrait_4_3", "晨光里的花田。"),
    ("https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=steaming%20ramen%20bowl%20with%20soft%20egg%20and%20green%20onions%2C%20top-down%20view%2C%20food%20photography&image_size=landscape_4_3", "深夜一碗拉面。"),
    ("https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20minimalist%20architecture%20with%20geometric%20lines%20against%20blue%20sky%2C%20architectural%20photography&image_size=portrait_16_9", "几何与天空。"),
]


def main() -> None:
    init_db()
    db = SessionLocal()
    user = db.query(User).filter(User.username == "demo").first()
    if not user:
        user = User(username="demo", password_hash="-", salt="-")
        db.add(user)
        db.commit()

    if db.query(Post).count() > 0:
        print("已有帖子，跳过填充")
        return

    now = dt.datetime.utcnow()
    for i, (url, caption) in enumerate(SAMPLES):
        db.add(Post(user_id=user.id, image_url=url, caption=caption,
                    created_at=now - dt.timedelta(hours=i)))
    db.commit()
    print(f"已插入 {len(SAMPLES)} 条示例照片")


if __name__ == "__main__":
    main()