from typing import AsyncGenerator, Any
from app.application.conversation.handlers.agent_message_handler import AgentMessageHandler, Event

class PreviewMessageHandler(AgentMessageHandler):
    async def pre_process(self, chat_context: Any) -> None:
        chat_context.is_preview = True
        chat_context.session_id = f"preview_{chat_context.agent_id}"

    async def post_process(self, chat_context: Any) -> None:
        pass

    async def save_message(self, message: Any) -> None:
        pass

    async def record_usage(self, token_usage: dict) -> None:
        pass