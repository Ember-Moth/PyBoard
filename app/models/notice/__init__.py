"""Notice 模型统一出口。"""

from app.models.notice.dto import NoticeCreate, NoticePublic, NoticeRead, NoticeUpdate
from app.models.notice.entity import Notice

__all__ = [
    "Notice",
    "NoticeCreate",
    "NoticePublic",
    "NoticeRead",
    "NoticeUpdate",
]
