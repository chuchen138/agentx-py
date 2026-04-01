from typing import Dict, Any
from app.application.conversation.handlers.chat_message_handler import ChatMessageHandler
from app.application.conversation.handlers.agent_message_handler import AgentMessageHandler
from app.application.conversation.handlers.rag_message_handler import RagMessageHandler
from app.application.conversation.handlers.preview_message_handler import PreviewMessageHandler

class MessageHandlerFactory:
    _handlers: Dict[str, Any] = {}
    _instances: Dict[str, Any] = {}
    _priority = {
        "preview": 1,
        "rag": 2,
        "agent": 3,
        "standard": 4
    }

    @classmethod
    def register(cls, chat_mode: str, handler_class: Any) -> None:
        cls._handlers[chat_mode] = handler_class

    @classmethod
    def get_handler(cls, chat_context: Any) -> Any:
        handler_type = cls._determine_handler_type(chat_context)
        if handler_type not in cls._instances:
            cls._instances[handler_type] = cls._handlers.get(handler_type, ChatMessageHandler)()
        return cls._instances[handler_type]

    @classmethod
    def _determine_handler_type(cls, chat_context: Any) -> str:
        if hasattr(chat_context, 'preview') and chat_context.preview:
            return "preview"
        if hasattr(chat_context, 'rag_id') and chat_context.rag_id:
            return "rag"
        if hasattr(chat_context, 'chat_mode') and chat_context.chat_mode == "agent":
            return "agent"
        return "standard"

MessageHandlerFactory.register("standard", ChatMessageHandler)
MessageHandlerFactory.register("agent", AgentMessageHandler)
MessageHandlerFactory.register("rag", RagMessageHandler)
MessageHandlerFactory.register("preview", PreviewMessageHandler)