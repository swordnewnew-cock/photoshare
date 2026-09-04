"""图片上传:优先腾讯云 COS;未配置密钥时自动降级存本地。

降级设计的意义:本地开发时不用先开通 COS 就能跑通全流程,
上线时只要在 .env 里填上 COS 配置,代码一行都不用改。
"""
import uuid
from pathlib import Path

from app.config import (
    BASE_DIR,
    COS_BUCKET,
    COS_DOMAIN,
    COS_REGION,
    COS_SECRET_ID,
    COS_SECRET_KEY,
)

LOCAL_UPLOAD_DIR = BASE_DIR / "static" / "uploads"

_EXT_MAP = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


def cos_enabled() -> bool:
    """四项关键配置齐全才认为启用了 COS。"""
    return bool(COS_SECRET_ID and COS_SECRET_KEY and COS_BUCKET and COS_REGION)


def upload_image(data: bytes, content_type: str) -> str:
    """上传图片并返回可公开访问的 URL。"""
    ext = _EXT_MAP.get(content_type, ".jpg")
    key = f"posts/{uuid.uuid4().hex}{ext}"

    if cos_enabled():
        from qcloud_cos import CosConfig, CosS3Client

        client = CosS3Client(
            CosConfig(
                Region=COS_REGION,
                SecretId=COS_SECRET_ID,
                SecretKey=COS_SECRET_KEY,
            )
        )
        client.put_object(
            Bucket=COS_BUCKET,
            Body=data,
            Key=key,
            ContentType=content_type,
        )
        if COS_DOMAIN:
            return f"https://{COS_DOMAIN}/{key}"
        return f"https://{COS_BUCKET}.cos.{COS_REGION}.myqcloud.com/{key}"

    # 未配置 COS:落到本地 static/uploads,仅供开发调试
    target = LOCAL_UPLOAD_DIR / key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return f"/static/uploads/{key}"
