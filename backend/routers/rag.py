"""RAG Query API with role support"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.core.dependencies import get_current_user
from app.models.user import User
from rag.retriever import get_qa_chain, retrieve_docs
from rag.vector_store import get_store_info

async def _rag_stream_generator(qs, top_k, role):
    try:
        from rag.retriever import get_retriever, RAG_PROMPT
        from lc.llm import get_chat_model
        retriever = get_retriever(k=top_k, role=role)
        docs = retriever.invoke(qs)
        context = "\n\n".join([d.page_content for d in docs])
        llm = get_chat_model(streaming=True, temperature=0.3)
        prompt = RAG_PROMPT.format(context=context, question=qs)
        full_content = ""
        async for chunk in llm.astream(prompt):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                full_content += content
                yield f"data: {json.dumps({"delta": content}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({"delta": "", "done": True, "full_content": full_content, "source_count": len(docs)}, ensure_ascii=False)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({"error": str(e)})}\n\n"

router = APIRouter(prefix="/api/rag", tags=["RAG"])

class RAGQueryRequest(BaseModel):
    question: str = Field(..., description="Question")
    top_k: int = Field(default=4, ge=1, le=10)
    stream: bool = Field(default=False)

class RAGQueryResponse(BaseModel):
    question: str; answer: str; source_count: int

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(req: RAGQueryRequest, current_user: User = Depends(get_current_user)):
    role = current_user.role
    info = get_store_info(role=role)
    if info["document_count"] == 0:
        raise HTTPException(status_code=400, detail="Knowledge base is empty")
    if req.stream:
        return StreamingResponse(_rag_stream_generator(req.question, req.top_k, role),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})
    try:
        qa_chain = get_qa_chain(k=req.top_k, role=role)
        result = qa_chain.invoke({"query": req.question})
        return RAGQueryResponse(question=req.question, answer=result,
            source_count=0)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

@router.get("/search")
async def search_docs(q: str, top_k: int = 4, current_user: User = Depends(get_current_user)):
    role = current_user.role
    docs = retrieve_docs(q, k=top_k, role=role)
    return {"query": q, "results": [{"content": doc.page_content[:300],
        "source": doc.metadata.get("source", "unknown"),
        "score": doc.metadata.get("score", None)} for doc in docs]}
