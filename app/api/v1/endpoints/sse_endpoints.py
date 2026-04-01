from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse
import json
from typing import AsyncGenerator, Dict, Any
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    content: str
    stream: bool = True

class ChatContext:
    def __init__(self, session_id: str, message_id: str, content: str):
        self.session_id = session_id
        self.message_id = message_id
        self.content = content
        self.preview = False
        self.rag_id = None
        self.chat_mode = "standard"

async def event_generator(chat_context: ChatContext) -> AsyncGenerator[Dict[str, Any], None]:
    from app.application.conversation.handlers.message_handler_factory import MessageHandlerFactory
    handler = MessageHandlerFactory.get_handler(chat_context)
    async for event in handler.handle(chat_context):
        yield {
            "event": event.type,
            "data": json.dumps(event.data),
            "id": event.id
        }

@router.post("/sessions/{sessionId}/chat/stream")
async def chat_stream(sessionId: str, request: ChatRequest):
    chat_context = ChatContext(
        session_id=sessionId,
        message_id=f"msg_{sessionId}_1",
        content=request.content
    )
    return EventSourceResponse(
        event_generator(chat_context),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/agents/{agentId}/chat/stream")
async def agent_chat_stream(agentId: str, request: ChatRequest):
    chat_context = ChatContext(
        session_id=f"agent_{agentId}_session",
        message_id=f"msg_agent_{agentId}_1",
        content=request.content
    )
    chat_context.chat_mode = "agent"
    return EventSourceResponse(
        event_generator(chat_context),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/rag/{ragId}/chat/stream")
async def rag_chat_stream(ragId: str, request: ChatRequest):
    chat_context = ChatContext(
        session_id=f"rag_{ragId}_session",
        message_id=f"msg_rag_{ragId}_1",
        content=request.content
    )
    chat_context.rag_id = ragId
    return EventSourceResponse(
        event_generator(chat_context),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )