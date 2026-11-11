"""校园AI助手平台 - FastAPI 后端入口"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings
from app.core.database import Base, engine
from app.api import auth_router, courses_router, announcements_router, chat_router, langchain_chat_router
from routers.agent import router as agent_router
from routers.agent_multi import router as agent_multi_router
from routers.knowledge import router as knowledge_router
from routers.rag import router as rag_router
from routers.dify_app import router as dify_app_router
from routers.history import router as history_router
from routers.ai_gateway import router as ai_gateway_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(status_code=500, content={"code": 500, "message": f"DB error: {str(exc)}"})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"code": 500, "message": f"Server error: {str(exc)}"})

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
app.include_router(courses_router)
app.include_router(announcements_router)
app.include_router(chat_router)
app.include_router(langchain_chat_router)
app.include_router(agent_router)
app.include_router(agent_multi_router)
app.include_router(knowledge_router)
app.include_router(rag_router)
app.include_router(dify_app_router)
app.include_router(history_router)
app.include_router(ai_gateway_router)

@app.get("/")
async def root():
    return {"message": "Campus AI API ready"}

@app.get("/hello")
async def hello():
    return {"code": 200, "message": "Hello, Campus AI!", "version": settings.APP_VERSION}

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
