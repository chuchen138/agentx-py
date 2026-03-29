from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any
import asyncio
from app.application.session.session_app_service import SessionAppService

router = APIRouter(prefix="/session", tags=["session"])

# 单例模式创建SessionAppService
class SessionServiceSingleton:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SessionAppService()
        return cls._instance

def get_session_service() -> SessionAppService:
    return SessionServiceSingleton.get_instance()

@router.post("/create", response_model=Dict[str, Any])
async def create_session(
    user_id: str,
    agent_id: str,
    session_service: SessionAppService = Depends(get_session_service)
):
    result = await session_service.create_session(user_id, agent_id)
    return result

@router.get("/get/{session_id}", response_model=Dict[str, Any])
async def get_session(
    session_id: str,
    session_service: SessionAppService = Depends(get_session_service)
):
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.post("/interrupt/{session_id}", response_model=Dict[str, bool])
async def interrupt_session(
    session_id: str,
    session_service: SessionAppService = Depends(get_session_service)
):
    success = await session_service.interrupt_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": success}

@router.post("/message", response_model=Dict[str, Any])
async def add_message(
    session_id: str,
    role: str,
    content: str,
    session_service: SessionAppService = Depends(get_session_service)
):
    result = await session_service.add_message(session_id, role, content)
    return result

@router.get("/messages/{session_id}", response_model=List[Dict[str, Any]])
async def get_messages(
    session_id: str,
    limit: int = 100,
    session_service: SessionAppService = Depends(get_session_service)
):
    messages = await session_service.get_messages(session_id, limit)
    return messages

@router.get("/sse/{session_id}")
async def sse_endpoint(
    session_id: str,
    request: Request,
    session_service: SessionAppService = Depends(get_session_service)
):
    # 检查会话是否存在
    session = await session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 注册SSE连接
    queue = await session_service.register_sse_connection(session_id)
    
    async def event_generator():
        try:
            while True:
                # 检查客户端是否断开连接
                if await request.is_disconnected():
                    break
                
                # 从队列获取消息
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    # 发送SSE事件
                    yield f"event: {event['event']}\n"
                    yield f"data: {event['data']}\n"
                    yield f"id: {event['id']}\n"
                    yield "\n"
                except asyncio.TimeoutError:
                    # 发送心跳
                    yield "event: heartbeat\n"
                    yield f"data: {{\"timestamp\": {asyncio.get_event_loop().time() * 1000}}}\n"
                    yield f"id: hb_{session_id}_{asyncio.get_event_loop().time()}\n"
                    yield "\n"
        finally:
            # 清理连接
            await session_service.unregister_sse_connection(session_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )

@router.get("/stats/active", response_model=Dict[str, int])
async def get_active_session_count(
    session_service: SessionAppService = Depends(get_session_service)
):
    count = await session_service.get_active_session_count()
    return {"active_sessions": count}