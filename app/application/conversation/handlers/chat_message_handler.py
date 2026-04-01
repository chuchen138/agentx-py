from typing import AsyncGenerator, Any
from app.application.conversation.handlers.abstract_message_handler import AbstractMessageHandler, Event

class ChatMessageHandler(AbstractMessageHandler):
    async def do_handle(self, chat_context: Any) -> AsyncGenerator[Event, None]:
        yield Event(
            type="start",
            data={
                "session_id": chat_context.session_id,
                "message_id": chat_context.message_id
            }
        )
        
        await self._inject_memory(chat_context)
        
        async for token in self._generate_response(chat_context):
            yield await self.send_token(token)
        
        yield Event(
            type="end",
            data={
                "finish_reason": "stop",
                "token_usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 200,
                    "total_tokens": 300
                }
            }
        )

    async def _inject_memory(self, chat_context: Any) -> None:
        pass

    async def _generate_response(self, chat_context: Any) -> AsyncGenerator[str, None]:
        response = "你好！我是 AgentX 智能助手，很高兴为你服务。"
        for char in response:
            yield char
            import asyncio
            await asyncio.sleep(0.05)