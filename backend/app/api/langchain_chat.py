"""LangChain AI Chat 接口"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.core.dependencies import get_current_user
from app.models.user import User
from lc.chains import get_simple_chain
from lc.llm import get_chat_model
from lc.memory import get_session_memory, clear_session_memory, get_session_count

import json

router = APIRouter(prefix="/api/langchain", tags=["LangChain聊天"])

class LangChainChatRequest(BaseModel):
    session_id: str = "default"
    user_input: str
    stream: bool = True
    template: str = "ai_buddy"
    memory_type: str = "buffer"
    memory_k: int = 20
    chain_type: str = "simple"

class LangChainChatResponse(BaseModel):
    reply: str
    session_id: str

def _resolve_chain(chain_type: str):
    model = get_chat_model()
    return get_simple_chain(model)

@router.post("/chat", response_model=LangChainChatResponse)
async def langchain_chat(req: LangChainChatRequest, current_user: User = Depends(get_current_user)):
    enhanced_input = req.user_input
    if req.stream:
        return StreamingResponse(
            _langchain_stream_generator(req.session_id, enhanced_input, req.template, req.memory_type, req.memory_k, req.chain_type),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )
    try:
        chain = _resolve_chain(req.chain_type)
        memory = get_session_memory(req.session_id, memory_type=req.memory_type, k=req.memory_k)
        result = chain.invoke({"user_input": enhanced_input, "history_text": ""})
        reply = result["text"] if isinstance(result, dict) else str(result)
        return LangChainChatResponse(reply=reply, session_id=req.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="LangChain调用失败: " + str(e))

async def _langchain_stream_generator(sid, ui, tmpl, mtype, mk, ctype):
    try:
        chain = _resolve_chain(ctype)
        memory = get_session_memory(sid, memory_type=mtype, k=mk)
        result = chain.invoke({"user_input": ui, "history_text": ""})
        reply = result["text"] if isinstance(result, dict) else str(result)
        chunk_size = max(1, len(reply) // 40)
        for i in range(0, len(reply), chunk_size):
            yield "data: " + json.dumps({"delta": reply[i:i + chunk_size]}, ensure_ascii=False) + chr(10) + chr(10)
        yield "data: " + json.dumps({"delta": "", "done": True, "full_content": reply}, ensure_ascii=False) + chr(10) + chr(10)
    except Exception as e:
        yield "data: " + json.dumps({"error": str(e)}, ensure_ascii=False) + chr(10) + chr(10)

@router.delete("/session/{session_id}")
async def delete_session(session_id: str, current_user: User = Depends(get_current_user)):
    clear_session_memory(session_id)
    return {"message": "Session " + session_id + " cleared", "session_count": get_session_count()}
