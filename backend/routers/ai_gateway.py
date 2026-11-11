"""统一 AI 网关 —— 根据 service_type 分发 + Redis 缓存"""
import json
import asyncio
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from services.cache import get as cache_get, set as cache_set

router = APIRouter(prefix="/api/ai", tags=["AI网关"])


class AIChatRequest(BaseModel):
    query: str = Field(..., description="用户消息")
    service_type: str = Field(default="langchain", description="langchain / langgraph / dify")
    session_id: str = Field(default="default", description="会话 ID")
    stream: bool = Field(default=False, description="是否流式返回")


class AIChatResponse(BaseModel):
    message: str
    service_type: str
    session_id: str
    sources: list = []
    audio_url: str = ""
    metadata: dict = {}


async def _call_langchain(query: str) -> str:
    """调用 LangChain 链（非流式）"""
    from lc.chains import get_simple_chain
    from lc.llm import get_chat_model
    try:
        model = get_chat_model()
        chain = get_simple_chain(model)
        result = chain.invoke({"user_input": query, "history_text": ""})
        return result["text"] if isinstance(result, dict) else str(result)
    except Exception as e:
        return f"[LangChain 错误] {e}"


async def _call_langgraph(query: str) -> str:
    """调用 LangGraph Agent（非流式，后端收集后返回）"""
    from agent.agent import CampusAgent
    from langchain_core.messages import HumanMessage
    try:
        agent = CampusAgent()
        result = await agent.ainvoke([HumanMessage(content=query)])
        return result.get("output", str(result))
    except Exception as e:
        return f"[LangGraph 错误] {e}"


async def _call_dify(query: str) -> str:
    """调用 Dify API（非流式收集）"""
    if not settings.DIFY_API_KEY:
        return "[Dify] API Key 未配置"
    url = f"{settings.DIFY_API_BASE.rstrip('/')}/chat-messages"
    headers = {
        "Authorization": f"Bearer {settings.DIFY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "streaming",
        "conversation_id": "",
        "user": "gateway",
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            full = ""
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        try:
                            d = json.loads(line[5:].strip())
                            if d.get("event") in ("message", "agent_message"):
                                full += d.get("answer", "")
                        except Exception:
                            pass
            return full or "[Dify] 返回空结果"
    except Exception as e:
        return f"[Dify 错误] {e}"


async def _dispatch(service_type: str, query: str) -> str:
    if service_type == "langgraph":
        return await _call_langgraph(query)
    elif service_type == "dify":
        return await _call_dify(query)
    else:  # langchain
        return await _call_langchain(query)


@router.post("/chat", response_model=AIChatResponse)
async def ai_chat(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
):
    """统一 AI 对话入口 —— 先查缓存，未命中则分发到具体服务"""
    # 1. 查 Redis 缓存
    cached = cache_get(req.query, req.service_type)
    if cached:
        return AIChatResponse(
            message=cached,
            service_type=req.service_type,
            session_id=req.session_id,
            metadata={"cached": True},
        )

    # 2. 分发到具体服务
    result = await _dispatch(req.service_type, req.query)

    # 3. 写入缓存
    cache_set(req.query, req.service_type, result)

    return AIChatResponse(
        message=result,
        service_type=req.service_type,
        session_id=req.session_id,
        metadata={"cached": False},
    )


@router.post("/chat/stream")
async def ai_chat_stream(
    req: AIChatRequest,
    current_user: User = Depends(get_current_user),
):
    """统一 AI 对话入口 —— 流式 SSE 模式（不缓存）"""
    req.stream = True

    async def generate():
        result = await _dispatch(req.service_type, req.query)
        # 模拟流式输出：按字拆分
        chunk_size = max(1, len(result) // 30)
        for i in range(0, len(result), chunk_size):
            chunk = result[i:i + chunk_size]
            yield f"data: {json.dumps({'delta': chunk}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'delta': '', 'done': True, 'full_content': result}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/health")
async def ai_gateway_health():
    """网关健康检查（含 Redis 状态）"""
    from services.cache import ping as redis_ping
    redis_ok = redis_ping()
    return {
        "status": "ok",
        "redis": "connected" if redis_ok else "disconnected",
        "services": {
            "langchain": True,
            "langgraph": True,
            "dify": bool(settings.DIFY_API_KEY),
        },
    }
