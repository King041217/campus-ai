"""Redis 缓存服务 —— 减少重复 LLM 调用，提升响应速度"""
import json
import hashlib
import redis
from app.core.config import settings

# 缓存 Key 前缀
CACHE_PREFIX = "ai:cache"

# 默认 TTL（秒）
DEFAULT_TTL = 3600
EMPTY_TTL = 60  # 空结果短 TTL 防穿透

_redis_client = None


def _get_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    _redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )
    return _redis_client


def _build_key(query: str, service_type: str) -> str:
    h = hashlib.md5(query.encode("utf-8")).hexdigest()[:16]
    return f"{CACHE_PREFIX}:{h}:{service_type}"


def get(query: str, service_type: str):
    try:
        client = _get_client()
        key = _build_key(query, service_type)
        return client.get(key)
    except Exception:
        return None


def set(query: str, service_type: str, value: str, ttl: int = None):
    if ttl is None:
        ttl = EMPTY_TTL if (not value or not value.strip()) else DEFAULT_TTL
    try:
        client = _get_client()
        key = _build_key(query, service_type)
        client.setex(key, ttl, value)
    except Exception:
        pass


def delete(query: str, service_type: str):
    try:
        client = _get_client()
        key = _build_key(query, service_type)
        client.delete(key)
    except Exception:
        pass


def ping() -> bool:
    try:
        return _get_client().ping()
    except Exception:
        return False
