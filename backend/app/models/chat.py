"""对话历史数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    role = Column(String(16), nullable=False, default="user")  # user / assistant
    content = Column(Text, nullable=False)
    service_type = Column(String(32), default="langchain")  # langchain / langgraph / dify
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="chat_messages")
