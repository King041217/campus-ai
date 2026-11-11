"""knowledge base document management API"""
import os, uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from app.core.dependencies import get_current_user
from app.models.user import User
from rag.loader import load_document
from rag.splitter import get_text_splitter
from rag.vector_store import add_documents, get_store_info, reset_store

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_SIZE = 20 * 1024 * 1024
class UploadResult(BaseModel):
    success: bool; file_name: str; file_id: str; chunk_count: int; message: str
class StoreInfo(BaseModel):
    collection_name: str; document_count: int; persist_directory: str; role: str = ""
class ResetResult(BaseModel):
    success: bool; message: str
@router.post("/upload", response_model=UploadResult)
async def upload_document(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    role = current_user.role
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not supported: {ext}")
    file_id = uuid.uuid4().hex[:12]
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    try:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 20MB")
        with open(save_path, "wb") as f: f.write(contents)
        docs = load_document(save_path)
        if not docs:
            raise HTTPException(status_code=400, detail="Document is empty")
        splitter = get_text_splitter(chunk_size=500, chunk_overlap=50)
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["file_id"] = file_id
            chunk.metadata["upload_time"] = datetime.now().isoformat()
            chunk.metadata["role"] = role
        count = add_documents(chunks, role=role)
        return UploadResult(success=True, file_name=file.filename or "", file_id=file_id, chunk_count=count, message=f"{count} chunks indexed")
    except HTTPException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/info", response_model=StoreInfo)
async def knowledge_base_info(current_user: User = Depends(get_current_user)):
    role = current_user.role
    info = get_store_info(role=role)
    info["role"] = role
    return StoreInfo(*+info)

@router.delete("/reset", response_model=ResetResult)
async def reset_knowledge_base(current_user: User = Depends(get_current_user)):
    role = current_user.role
    reset_store(role=role)
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            p = os.path.join(UPLOAD_DIR, f)
            if os.path.isfile(p): os.remove(p)
    return ResetResult(success=True, message=f"{role} knowledge base cleared")

@router.delete("/documents/{file_id}", response_model=ResetResult)
async def delete_document(file_id: str, current_user: User = Depends(get_current_user)):
    role = current_user.role
    from rag.vector_store import _get_collection_for_role
    col = _get_collection_for_role(role)
    try:
        col.delete(where={"file_id": file_id})
    except Exception:
        pass
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith(file_id):
                os.remove(os.path.join(UPLOAD_DIR, f))
    return ResetResult(success=True, message=f"Document {file_id} deleted")