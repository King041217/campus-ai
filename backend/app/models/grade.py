from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.core.database import Base


class Grade(Base):
    __tablename__ = "grades"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True, comment="学生ID")
    course_name = Column(String(200), nullable=False, comment="课程名称")
    score = Column(Float, nullable=False, comment="成绩")
    term = Column(String(50), nullable=True, comment="学期")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<Grade(id={self.id}, student_id={self.student_id}, course={self.course_name}, score={self.score})>"
