import asyncio
import pytest
from app.domain.session.service import SessionService
from app.domain.session.entities import SessionEntity, MessageEntity, ContextEntity


@pytest.mark.asyncio
async def test_create_session():
    """测试创建会话"""
    session_service = SessionService()
    session = await session_service.create_session("user1", "agent1")
    
    assert isinstance(session, SessionEntity)
    assert session.user_id == "user1"
    assert session.agent_id == "agent1"
    assert session.status == "active"


@pytest.mark.asyncio
async def test_get_session():
    """测试获取会话"""
    session_service = SessionService()
    created_session = await session_service.create_session("user1", "agent1")
    
    retrieved_session = await session_service.get_session(created_session.session_id)
    assert retrieved_session is not None
    assert retrieved_session.session_id == created_session.session_id
    assert retrieved_session.user_id == "user1"


@pytest.mark.asyncio
async def test_interrupt_session():
    """测试中断会话"""
    session_service = SessionService()
    session = await session_service.create_session("user1", "agent1")
    
    success = await session_service.interrupt_session(session.session_id)
    assert success is True
    
    updated_session = await session_service.get_session(session.session_id)
    assert updated_session.status == "interrupted"


@pytest.mark.asyncio
async def test_add_message():
    """测试添加消息"""
    session_service = SessionService()
    session = await session_service.create_session("user1", "agent1")
    
    message = await session_service.add_message(session.session_id, "user", "Hello, world!")
    assert isinstance(message, MessageEntity)
    assert message.session_id == session.session_id
    assert message.role == "user"
    assert message.content == "Hello, world!"


@pytest.mark.asyncio
async def test_get_messages():
    """测试获取消息"""
    session_service = SessionService()
    session = await session_service.create_session("user1", "agent1")
    
    # 添加两条消息
    await session_service.add_message(session.session_id, "user", "Hello")
    await session_service.add_message(session.session_id, "assistant", "Hi there!")
    
    messages = await session_service.get_messages(session.session_id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_update_context():
    """测试更新上下文"""
    session_service = SessionService()
    session = await session_service.create_session("user1", "agent1")
    
    # 添加消息
    message1 = await session_service.add_message(session.session_id, "user", "Hello")
    message2 = await session_service.add_message(session.session_id, "assistant", "Hi there!")
    
    # 更新上下文
    context = await session_service.update_context(
        session.session_id,
        [message1.message_id, message2.message_id],
        100
    )
    
    assert isinstance(context, ContextEntity)
    assert context.session_id == session.session_id
    assert len(context.message_ids) == 2
    assert context.total_tokens == 100


@pytest.mark.asyncio
async def test_get_context():
    """测试获取上下文"""
    session_service = SessionService()
    session = await session_service.create_session("user1", "agent1")
    
    # 添加消息并更新上下文
    message = await session_service.add_message(session.session_id, "user", "Hello")
    await session_service.update_context(session.session_id, [message.message_id], 50)
    
    context = await session_service.get_context(session.session_id)
    assert context is not None
    assert context.session_id == session.session_id
    assert context.total_tokens == 50


@pytest.mark.asyncio
async def test_cleanup_timeout_sessions():
    """测试清理超时会话"""
    session_service = SessionService()
    session = await session_service.create_session("user1", "agent1")
    
    # 清理超时会话（设置为0秒，即立即清理）
    await session_service.cleanup_timeout_sessions(0)
    
    # 验证会话是否被清理
    retrieved_session = await session_service.get_session(session.session_id)
    assert retrieved_session is None


@pytest.mark.asyncio
async def test_get_active_session_count():
    """测试获取活跃会话数量"""
    session_service = SessionService()
    
    # 创建两个会话
    await session_service.create_session("user1", "agent1")
    await session_service.create_session("user2", "agent2")
    
    count = await session_service.get_active_session_count()
    assert count == 2
    
    # 中断一个会话
    sessions = list(session_service.sessions.values())
    if sessions:
        await session_service.interrupt_session(sessions[0].session_id)
        
        # 再次获取活跃会话数量
        count = await session_service.get_active_session_count()
        assert count == 1