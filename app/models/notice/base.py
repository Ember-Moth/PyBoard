"""Notice 字段全集，不含 id/关系/系统字段。对应 公告表 `notice`。"""

from sqlmodel import Field, SQLModel


class NoticeBase(SQLModel):
    """所有业务字段定义在此。entity 和 dto 按需继承。"""

    title: str = Field(max_length=255)  # 公告标题
    content: str  # 公告内容
    show: bool = False  # 是否显示
    img_url: str | None = Field(default=None, max_length=255)  # 图片 URL
    tags: str | None = Field(default=None, max_length=255)  # 标签
