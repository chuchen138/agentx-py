from typing import AsyncGenerator, Any, Dict
from app.application.conversation.handlers.abstract_message_handler import AbstractMessageHandler, Event

class AgentMessageHandler(AbstractMessageHandler):
    async def do_handle(self, chat_context: Any) -> AsyncGenerator[Event, None]:
        yield Event(
            type="start",
            data={
                "session_id": chat_context.session_id,
                "message_id": chat_context.message_id
            }
        )
        
        yield Event(
            type="thought",
            data={
                "type": "analysis",
                "content": "正在分析用户请求..."
            }
        )
        
        tool_result = await self._execute_tool(chat_context)
        
        yield Event(
            type="tool_call",
            data={
                "tool_name": "weather_query",
                "arguments": {"city": "北京"}
            }
        )
        
        yield Event(
            type="tool_result",
            data={
                "tool_name": "weather_query",
                "result": tool_result
            }
        )
        
        async for token in self._generate_response(chat_context, tool_result):
            yield await self.send_token(token)
        
        yield Event(
            type="end",
            data={
                "finish_reason": "stop",
                "token_usage": {
                    "prompt_tokens": 150,
                    "completion_tokens": 250,
                    "total_tokens": 400
                }
            }
        )

    async def _execute_tool(self, chat_context: Any) -> str:
        return "晴，25°C"

    async def _generate_response(self, chat_context: Any, tool_result: str) -> AsyncGenerator[str, None]:
        response = f"今天天气{tool_result}，适合户外活动。"
        for char in response:
            yield char
            import asyncio
            await asyncio.sleep(0.05)