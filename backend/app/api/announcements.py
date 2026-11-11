"""公告 CRUD 路由"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_admin_user
from app.models.announcement import Announcement
from app.models.user import User
from app.schemas import AnnouncementCreate, AnnouncementUpdate, AnnouncementInfo

router = APIRouter(prefix="/api/announcements", tags=["公告管理"])


@router.get("", response_model=List[AnnouncementInfo], summary="获取公告列表")
def list_announcements(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(Announcement).order_by(Announcement.created_at.desc()).offset(skip).limit(limit).all()
    return [AnnouncementInfo.model_validate(a) for a in items]


@router.get("/{announcement_id}", response_model=AnnouncementInfo, summary="获取公告详情")
def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="公告不存在")
    return AnnouncementInfo.model_validate(item)


@router.post("", response_model=AnnouncementInfo, summary="创建公告")
def create_announcement(
    data: AnnouncementCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    item = Announcement(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return AnnouncementInfo.model_validate(item)


@router.put("/{announcement_id}", response_model=AnnouncementInfo, summary="更新公告")
def update_announcement(
    announcement_id: int,
    data: AnnouncementUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    item = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="公告不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return AnnouncementInfo.model_validate(item)


@router.delete("/{announcement_id}", summary="删除公告")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    item = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="公告不存在")
    db.delete(item)
    db.commit()
    return {"message": "公告已删除"}
