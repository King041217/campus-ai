"""安全模块：JWT 令牌 + 密码哈希"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, secret_key: str, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm="HS256")


def decode_access_token(token: str, secret_key: str) -> dict | None:
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except JWTError:
        return None
"""安全模块：JWT 令牌 + 密码哈希"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pbkdf2_sha256.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def create_access_token(data: dict, secret_key: str, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm="HS256")


def decode_access_token(token: str, secret_key: str) -> dict | None:
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except JWTError:
        return None
