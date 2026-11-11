"""AI Chat 接口 — 支持 SSE 流式和非流式"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.llm import get_llm_client
from app.services.stream import sse_chat_generator
from prompts.templates import get_template, AI_BUDDY


router = APIRouter(prefix="/api/chat", tags=["AI对话"])


class ChatRequest(BaseModel):
    message: str                        # 用户最新消息
    history: list[dict] = []             # 历史消息 [{role, content}, ...]
    stream: bool = True                 # 是否启用流式
    template: str = "ai_buddy"          # 提示词模板名称


class ChatResponse(BaseModel):
    reply: str
    template: str


@router.post("/send", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: User = Depends(get_current_user)):
    """发送消息给 AI（非流式）"""
    template = get_template(req.template)
    role_labels = {"student": "学生", "teacher": "教师", "admin": "管理员", "decision_maker": "决策者"}
    role_label = role_labels.get(current_user.role, current_user.role)
    name = current_user.full_name or current_user.username
    role_hint = f"\n\n【当前用户】{name}（{role_label}）"
    if template is None:
        raise HTTPException(status_code=400, detail=f"未知模板: {req.template}")

    # 构建 messages
    system_msg = {"role": "system", "content": role_hint + "\n\n" + template.to_system_message()}
    history = req.history[-20:] if req.history else []
    messages = [system_msg] + history + [{"role": "user", "content": req.message}]

    if req.stream:
        # 流式：使用 StreamingResponse
        return StreamingResponse(
            sse_chat_generator(messages),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # 非流式
        client = get_llm_client()
        try:
            result = await client.chat(messages=messages)
            reply = result["choices"][0]["message"]["content"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI 调用失败: {str(e)}")
        return ChatResponse(reply=reply, template=req.template)


@router.get("/templates")
async def list_templates():
    """获取所有可用提示词模板"""
    from prompts.templates import TEMPLATES
    return {
        "templates": [
            {"key": k, "name": v.name, "system_prompt": v.to_system_message()}
            for k, v in TEMPLATES.items()
        ]
    }
