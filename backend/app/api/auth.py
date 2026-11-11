"""认证路由：注册 / 登录 / 获取当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas import UserRegister, UserLogin, TokenResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["认证管理"])


@router.post("/register", response_model=TokenResponse, summary="用户注册")
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已被注册")
    allowed = ("student", "teacher", "admin", "decision_maker")
    if data.role not in allowed:
        raise HTTPException(status_code=400, detail=f"无效角色，仅支持 {chr(47).join(allowed)}")
    user = User(
        username=data.username, email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name, role=data.role,
    )
    db.add(user); db.commit(); db.refresh(user)
    token = create_access_token(data={"sub": user.username}, secret_key=settings.SECRET_KEY)
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


@router.post("/login", response_model=TokenResponse, summary="JSON登录")
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    token = create_access_token(data={"sub": user.username}, secret_key=settings.SECRET_KEY)
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


@router.post("/token", response_model=TokenResponse, summary="OAuth2表单登录")
def login_form(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已被禁用")
    token = create_access_token(data={"sub": user.username}, secret_key=settings.SECRET_KEY)
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
def get_me(current_user: User = Depends(get_current_user)):
    return UserInfo.model_validate(current_user)


@router.get("/users", summary="获取所有用户(管理员)")
def list_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role not in ("admin", "decision_maker"):
        raise HTTPException(status_code=403, detail="仅管理员可查看")
    users = db.query(User).all()
    return {"total": len(users), "items": [UserInfo.model_validate(u).model_dump() for u in users]}