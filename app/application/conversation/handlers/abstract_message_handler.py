from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any
from dataclasses import dataclass

@dataclass
class Event:
    type: str
    data: Dict[str, Any]
    id: str = None

class AbstractMessageHandler(ABC):
    @abstractmethod
    async def do_handle(self, chat_context: Any) -> AsyncGenerator[Event, None]:
        pass

    async def handle(self, chat_context: Any) -> AsyncGenerator[Event, None]:
        await self.pre_process(chat_context)
        async for event in self.do_handle(chat_context):
            yield event
        await self.post_process(chat_context)

    async def pre_process(self, chat_context: Any) -> None:
        pass

    async def post_process(self, chat_context: Any) -> None:
        pass

    async def send_token(self, content: str) -> Event:
        return Event(
            type="token",
            data={"content": content}
        )

    async def send_event(self, event_type: str, data: Dict[str, Any]) -> Event:
        return Event(
            type=event_type,
            data=data
        )

    async def save_message(self, message: Any) -> None:
        pass

    async def record_usage(self, token_usage: Dict[str, int]) -> None:
        pass