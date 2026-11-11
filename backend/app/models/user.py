"""用户模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=False, comment="邮箱")
    hashed_password = Column(String(255), nullable=False, comment="哈希后的密码")
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    role = Column(String(20), default="student", comment="角色: student/teacher/admin/decision_maker")
    is_active = Column(Boolean, default=True, comment="是否激活")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    chat_messages = relationship("ChatMessage", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"
