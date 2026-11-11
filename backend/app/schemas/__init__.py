"""Pydantic Schema 定义：请求与响应模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ===== Auth Schemas =====

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    role: str = Field("student", description="角色: student/teacher/admin")


class UserLogin(BaseModel):
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserInfo"


class UserInfo(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Course Schemas =====

class CourseCreate(BaseModel):
    name: str = Field(..., max_length=200, description="课程名称")
    code: str = Field(..., max_length=50, description="课程代码")
    teacher: Optional[str] = Field(None, max_length=100, description="授课教师")
    description: Optional[str] = None
    credits: int = Field(3, ge=1, le=10, description="学分")
    schedule: Optional[str] = Field(None, max_length=200, description="上课时间地点")


class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    teacher: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    credits: Optional[int] = Field(None, ge=1, le=10)
    schedule: Optional[str] = Field(None, max_length=200)


class CourseInfo(BaseModel):
    id: int
    name: str
    code: str
    teacher: Optional[str] = None
    description: Optional[str] = None
    credits: int
    schedule: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===== Announcement Schemas =====

class AnnouncementCreate(BaseModel):
    title: str = Field(..., max_length=200, description="公告标题")
    content: Optional[str] = None
    author: Optional[str] = Field(None, max_length=100, description="发布者")
    priority: str = Field("normal", description="优先级: normal/important/urgent")


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    author: Optional[str] = Field(None, max_length=100)
    priority: Optional[str] = None


class AnnouncementInfo(BaseModel):
    id: int
    title: str
    content: Optional[str] = None
    author: Optional[str] = None
    priority: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 通用响应
class ApiResponse(BaseModel):
    code: int = 200
    message: str = "操作成功"
    data: Optional[dict] = None
