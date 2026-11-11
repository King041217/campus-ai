"""公告模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False, comment="公告标题")
    content = Column(Text, nullable=True, comment="公告内容")
    author = Column(String(100), nullable=True, comment="发布者")
    priority = Column(String(20), default="normal", comment="优先级: normal/important/urgent")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Announcement(id={self.id}, title={self.title})>"
