import pytest
from app.application.conversation.handlers.chat_message_handler import ChatMessageHandler
from app.application.conversation.handlers.agent_message_handler import AgentMessageHandler
from app.application.conversation.handlers.rag_message_handler import RagMessageHandler
from app.application.conversation.handlers.preview_message_handler import PreviewMessageHandler

class MockChatContext:
    def __init__(self):
        self.session_id = "test_session"
        self.message_id = "test_message"
        self.content = "你好"
        self.preview = False
        self.rag_id = None
        self.chat_mode = "standard"
        self.agent_id = "test_agent"

@pytest.mark.asyncio
async def test_chat_message_handler():
    handler = ChatMessageHandler()
    context = MockChatContext()
    events = []
    async for event in handler.handle(context):
        events.append(event)
    assert len(events) > 0
    assert events[0].type == "start"
    assert events[-1].type == "end"

@pytest.mark.asyncio
async def test_agent_message_handler():
    handler = AgentMessageHandler()
    context = MockChatContext()
    context.chat_mode = "agent"
    events = []
    async for event in handler.handle(context):
        events.append(event)
    assert len(events) > 0
    assert any(event.type == "tool_call" for event in events)
    assert any(event.type == "tool_result" for event in events)

@pytest.mark.asyncio
async def test_rag_message_handler():
    handler = RagMessageHandler()
    context = MockChatContext()
    context.rag_id = "test_rag"
    events = []
    async for event in handler.handle(context):
        events.append(event)
    assert len(events) > 0
    assert any(event.type == "retrieval_start" for event in events)
    assert any(event.type == "retrieval_end" for event in events)
    assert any(event.type == "thinking_start" for event in events)
    assert any(event.type == "answer_start" for event in events)

@pytest.mark.asyncio
async def test_preview_message_handler():
    handler = PreviewMessageHandler()
    context = MockChatContext()
    context.preview = True
    events = []
    async for event in handler.handle(context):
        events.append(event)
    assert len(events) > 0
    assert events[0].type == "start"
    assert events[-1].type == "end"