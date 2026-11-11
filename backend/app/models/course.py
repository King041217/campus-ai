"""课程模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False, comment="课程名称")
    code = Column(String(50), unique=True, nullable=False, index=True, comment="课程代码")
    teacher = Column(String(100), nullable=True, comment="授课教师")
    description = Column(Text, nullable=True, comment="课程描述")
    credits = Column(Integer, default=3, comment="学分")
    schedule = Column(String(200), nullable=True, comment="上课时间地点")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Course(id={self.id}, name={self.name}, code={self.code})>"
