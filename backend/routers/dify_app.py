"""Dify API proxy - chat, TTS, STT, image gen"""
import json
import httpx
import re
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User
from services.tts import segment_text, list_voice_styles
from services.stt import get_hot_words, list_categories, add_hot_word
from services.image_gen import ImageGenClient, ImageGenRequest, ImageGenResult, get_image_gen_client, get_scene_templates

router = APIRouter(prefix="/api/dify", tags=["Dify智能助手"])


import re

def _strip_thinking(text: str) -> str:
    if not text or len(text) < 10:
        return text
    # Remove <think>...</think> tags (DeepSeek reasoning)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    if not text:
        return ''
    # Remove plain text thinking preamble
    text = text.replace('\r\n', '\n')
    parts = text.split(chr(10), 1)
    if len(parts) == 2:
        first, rest = parts
        if (re.match(r'^(嗯|好的|哦)[，,]', first.strip()) or chr(29992)+chr(25143) in first) and len(first) > 10:
            return rest.strip()
    return text.strip()

class DifyChatRequest(BaseModel):
    query: str = Field(..., description="用户消息")
    conversation_id: str = Field(default="", description="会话ID")
    user: str = Field(default="anonymous")


class DifyChatResponse(BaseModel):
    answer: str
    conversation_id: str


@router.post("/agent/chat")
async def dify_agent_chat(req: DifyChatRequest, current_user: User = Depends(get_current_user)):
    if not settings.DIFY_API_KEY:
        raise HTTPException(status_code=500, detail="DIFY_API_KEY not configured")
    url = f"{settings.DIFY_API_BASE.rstrip('/')}/chat-messages"
    headers = {"Authorization": f"Bearer {settings.DIFY_API_KEY}", "Content-Type": "application/json"}
    payload = {"inputs": {}, "query": req.query, "response_mode": "streaming", "conversation_id": req.conversation_id, "user": req.user}
    conversation_id = req.conversation_id
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            full_answer = ""
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line and line.startswith("data:"):
                        try:
                            d = json.loads(line[5:].strip())
                            evt = d.get("event", "")
                            if evt in ("message", "agent_message"):
                                full_answer += d.get("answer", "")
                            if evt == "message_end":
                                cid = d.get("conversation_id", "")
                                if cid:
                                    conversation_id = cid
                        except Exception:
                            pass
        clean_answer = _strip_thinking(full_answer)
        return DifyChatResponse(answer=clean_answer, conversation_id=conversation_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Dify API error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dify request failed: {str(e)}")


@router.post("/agent/chat/stream")
async def dify_agent_chat_streaming(req: DifyChatRequest, current_user: User = Depends(get_current_user)):
    if not settings.DIFY_API_KEY:
        raise HTTPException(status_code=500, detail="DIFY_API_KEY not configured")
    url = f"{settings.DIFY_API_BASE.rstrip('/')}/chat-messages"
    headers = {"Authorization": f"Bearer {settings.DIFY_API_KEY}", "Content-Type": "application/json"}
    payload = {"inputs": {}, "query": req.query, "response_mode": "streaming", "conversation_id": req.conversation_id, "user": req.user}
    async def stream_generator():
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line and not line.startswith(":"):
                        yield line + "\n\n"
    return StreamingResponse(stream_generator(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


class WorkflowRunRequest(BaseModel):
    inputs: dict = Field(default_factory=dict)
    user: str = Field(default="anonymous")


class WorkflowRunResponse(BaseModel):
    task_id: str
    status: str


@router.post("/workflow/run", response_model=WorkflowRunResponse)
async def run_workflow(req: WorkflowRunRequest, current_user: User = Depends(get_current_user)):
    if not settings.DIFY_API_KEY:
        raise HTTPException(status_code=500, detail="DIFY_API_KEY not configured")
    url = f"{settings.DIFY_API_BASE.rstrip('/')}/workflows/run"
    headers = {"Authorization": f"Bearer {settings.DIFY_API_KEY}", "Content-Type": "application/json"}
    payload = {"inputs": req.inputs, "response_mode": "blocking", "user": req.user}
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return WorkflowRunResponse(task_id=data.get("workflow_run_id", ""), status=data.get("data", {}).get("status", "unknown"))
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Dify workflow error: {e.response.status_code}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Workflow request failed: {str(e)}")


@router.get("/workflow/status/{task_id}")
async def workflow_status(task_id: str, current_user: User = Depends(get_current_user)):
    raise HTTPException(status_code=501, detail="Not implemented")


class TTSSegmentRequest(BaseModel):
    text: str
    style: str = Field(default="friendly")


@router.post("/tts/segment")
async def tts_segment(req: TTSSegmentRequest):
    return segment_text(req.text, req.style).model_dump()


@router.get("/tts/styles")
async def tts_styles():
    return list_voice_styles()


@router.get("/stt/hotwords")
async def stt_hotwords(category: str = None):
    return get_hot_words(category)


@router.get("/stt/categories")
async def stt_categories():
    return list_categories()


class HotWordRequest(BaseModel):
    category: str
    word: str


@router.post("/stt/hotwords")
async def stt_add_hotword(req: HotWordRequest):
    return add_hot_word(req.category, req.word)


class ImageGenAPIRequest(BaseModel):
    prompt: str
    negative_prompt: str = Field(default="low quality, blurry, watermark, text, signature")
    style: str = Field(default="default")
    size: str = Field(default="1024x1024")
    n: int = Field(default=1, ge=1, le=4)


@router.post("/image/generate")
async def generate_image(req: ImageGenAPIRequest):
    client = get_image_gen_client()
    gen_req = ImageGenRequest(prompt=req.prompt, negative_prompt=req.negative_prompt, style=req.style, size=req.size, n=req.n)
    return await client.generate(gen_req)


@router.get("/image/templates")
async def image_templates():
    return get_scene_templates()