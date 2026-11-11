from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.core.database import Base


class StudyRoom(Base):
    __tablename__ = "study_rooms"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="自习室名称")
    location = Column(String(200), nullable=True, comment="位置")
    capacity = Column(Integer, default=30, comment="总座位数")
    occupied = Column(Integer, default=0, comment="已占用座位数")
    is_open = Column(Boolean, default=True, comment="是否开放")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")

    @property
    def available(self) -> int:
        return self.capacity - self.occupied

    def __repr__(self):
        return f"<StudyRoom(id={self.id}, name={self.name}, available={self.available})>"
