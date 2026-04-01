from typing import AsyncGenerator, Any
from app.application.conversation.handlers.abstract_message_handler import AbstractMessageHandler, Event

class RagMessageHandler(AbstractMessageHandler):
    async def do_handle(self, chat_context: Any) -> AsyncGenerator[Event, None]:
        yield Event(
            type="start",
            data={
                "session_id": chat_context.session_id,
                "message_id": chat_context.message_id
            }
        )
        
        yield Event(
            type="retrieval_start",
            data={
                "query": "年假政策",
                "datasets": ["员工手册"]
            }
        )
        
        yield Event(
            type="retrieval_progress",
            data={
                "stage": "searching",
                "progress": 0.5
            }
        )
        
        documents = await self._retrieve_documents(chat_context)
        
        yield Event(
            type="retrieval_end",
            data={
                "documents": documents
            }
        )
        
        yield Event(
            type="thinking_start",
            data={}
        )
        
        yield Event(
            type="thinking_progress",
            data={
                "content": "正在分析文档..."
            }
        )
        
        yield Event(
            type="thinking_end",
            data={}
        )
        
        yield Event(
            type="answer_start",
            data={}
        )
        
        async for token in self._generate_response(chat_context, documents):
            yield await self.send_token(token)
        
        yield Event(
            type="answer_end",
            data={
                "token_usage": {
                    "total_tokens": 350
                }
            }
        )

    async def _retrieve_documents(self, chat_context: Any) -> list:
        return [
            {
                "content": "公司年假政策：员工工作满一年可享受5天年假，满三年可享受10天年假。",
                "score": 0.92
            }
        ]

    async def _generate_response(self, chat_context: Any, documents: list) -> AsyncGenerator[str, None]:
        response = "根据员工手册，公司的年假政策是：员工工作满一年可享受5天年假，满三年可享受10天年假。"
        for char in response:
            yield char
            import asyncio
            await asyncio.sleep(0.05)