"""对话历史 CRUD 接口"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import desc, distinct, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.chat import ChatMessage

router = APIRouter(prefix="/api/history", tags=["对话历史"])


class SessionInfo(BaseModel):
    session_id: str
    message_count: int
    last_message: str
    updated_at: str
    service_type: str


class MessageItem(BaseModel):
    id: int
    role: str
    content: str
    service_type: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/sessions")
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户的对话会话列表（按最后更新时间倒序）"""
    rows = (
        db.query(
            ChatMessage.session_id,
            func.count(ChatMessage.id).label("cnt"),
            func.max(ChatMessage.created_at).label("max_time"),
            func.max(ChatMessage.service_type).label("svc"),
        )
        .filter(ChatMessage.user_id == current_user.id)
        .group_by(ChatMessage.session_id)
        .order_by(desc("max_time"))
        .all()
    )
    sessions = []
    for sid, cnt, max_time, svc in rows:
        # 取该会话的最后一条消息作为预览
        last_msg = (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == sid,
                ChatMessage.user_id == current_user.id,
            )
            .order_by(ChatMessage.id.desc())
            .first()
        )
        preview = last_msg.content[:60] if last_msg else ""
        sessions.append(SessionInfo(
            session_id=sid,
            message_count=cnt,
            last_message=preview,
            updated_at=str(max_time),
            service_type=svc or "langchain",
        ).model_dump())
    return sessions


@router.get("/session/{session_id}")
def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取某个会话的全部消息"""
    msgs = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == current_user.id,
        )
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        MessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            service_type=m.service_type,
            created_at=str(m.created_at),
        ).model_dump()
        for m in msgs
    ]


@router.delete("/session/{session_id}")
def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除整个会话"""
    deleted = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id == current_user.id,
        )
        .delete()
    )
    db.commit()
    return {"deleted": deleted, "session_id": session_id}


class SaveMessageRequest(BaseModel):
    session_id: str
    role: str
    content: str
    service_type: str = "langchain"


@router.post("/save")
def save_message(
    req: SaveMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """保存一条对话消息（前端 fire-and-forget 调用）"""
    msg = ChatMessage(
        user_id=current_user.id,
        session_id=req.session_id,
        role=req.role,
        content=req.content,
        service_type=req.service_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"id": msg.id, "ok": True}
