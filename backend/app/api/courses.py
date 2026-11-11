"""课程 CRUD 路由"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_admin_user
from app.models.course import Course
from app.models.user import User
from app.schemas import CourseCreate, CourseUpdate, CourseInfo

router = APIRouter(prefix="/api/courses", tags=["课程管理"])


@router.get("", response_model=List[CourseInfo], summary="获取课程列表")
def list_courses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    courses = db.query(Course).offset(skip).limit(limit).all()
    return [CourseInfo.model_validate(c) for c in courses]


@router.get("/{course_id}", response_model=CourseInfo, summary="获取课程详情")
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return CourseInfo.model_validate(course)


@router.post("", response_model=CourseInfo, summary="创建课程")
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    if db.query(Course).filter(Course.code == data.code).first():
        raise HTTPException(status_code=400, detail="课程代码已存在")
    course = Course(**data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return CourseInfo.model_validate(course)


@router.put("/{course_id}", response_model=CourseInfo, summary="更新课程")
def update_course(
    course_id: int,
    data: CourseUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return CourseInfo.model_validate(course)


@router.delete("/{course_id}", summary="删除课程")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    db.delete(course)
    db.commit()
    return {"message": "课程已删除"}
