"""Multi-Agent Collaboration API"""
import json, re, asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.core.dependencies import get_current_user
from app.models.user import User
from agent_multi.graph import compiled_multi_graph
from agent.tools import set_user_context

router = APIRouter(prefix="/api/agent/multi", tags=["multi-agent"])

class MultiChatRequest(BaseModel):
    message: str = Field(..., min_length=1)

@router.post("/chat")
async def multi_agent_chat(req: MultiChatRequest, current_user: User = Depends(get_current_user)):
    set_user_context(current_user.id, current_user.username, getattr(current_user, "role", "student"))

    async def event_stream():
        try:
            inputs = {
                "user_question": req.message,
                "user_role": getattr(current_user, "role", "student"),
                "user_name": current_user.username,
            }
            async for event in compiled_multi_graph.astream(inputs):
                for node_name, state in event.items():
                    if node_name == "classifier":
                        obj = {"stage": "classified", "category": state.get("category", "unknown"), "reasoning": state.get("reasoning", "")}
                        yield "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"
                    elif node_name == "retriever":
                        results = state.get("search_results", "")
                        obj = {"stage": "retrieved", "summary": results[:300] if results else ""}
                        yield "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"
                    elif node_name == "responder":
                        content = state.get("final_response", "")
                        if content:
                            obj = {"delta": content}
                            yield "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"
                    elif node_name == "quality":
                        full = state.get("final_response", "")
                        obj = {"done": True, "full_content": full, "quality_score": state.get("quality_score", 0)}
                        yield "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"
        except Exception as e:
            yield "data: " + json.dumps({"error": str(e)}, ensure_ascii=False) + "\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
