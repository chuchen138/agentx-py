import asyncio
import pytest
from app.application.session.session_app_service import SessionAppService


@pytest.mark.asyncio
async def test_create_session():
    """测试创建会话"""
    session_app_service = SessionAppService()
    result = await session_app_service.create_session("user1", "agent1")
    
    assert "session_id" in result
    assert result["user_id"] == "user1"
    assert result["agent_id"] == "agent1"
    assert result["status"] == "active"
    assert "created_at" in result


@pytest.mark.asyncio
async def test_get_session():
    """测试获取会话"""
    session_app_service = SessionAppService()
    created_session = await session_app_service.create_session("user1", "agent1")
    
    retrieved_session = await session_app_service.get_session(created_session["session_id"])
    assert retrieved_session is not None
    assert retrieved_session["session_id"] == created_session["session_id"]
    assert retrieved_session["user_id"] == "user1"


@pytest.mark.asyncio
async def test_interrupt_session():
    """测试中断会话"""
    session_app_service = SessionAppService()
    created_session = await session_app_service.create_session("user1", "agent1")
    
    success = await session_app_service.interrupt_session(created_session["session_id"])
    assert success is True
    
    updated_session = await session_app_service.get_session(created_session["session_id"])
    assert updated_session["status"] == "interrupted"


@pytest.mark.asyncio
async def test_add_message():
    """测试添加消息"""
    session_app_service = SessionAppService()
    created_session = await session_app_service.create_session("user1", "agent1")
    
    message = await session_app_service.add_message(
        created_session["session_id"], 
        "user", 
        "Hello, world!"
    )
    
    assert "message_id" in message
    assert message["session_id"] == created_session["session_id"]
    assert message["role"] == "user"
    assert message["content"] == "Hello, world!"
    assert "token_count" in message
    assert "created_at" in message


@pytest.mark.asyncio
async def test_get_messages():
    """测试获取消息"""
    session_app_service = SessionAppService()
    created_session = await session_app_service.create_session("user1", "agent1")
    
    # 添加两条消息
    await session_app_service.add_message(created_session["session_id"], "user", "Hello")
    await session_app_service.add_message(created_session["session_id"], "assistant", "Hi there!")
    
    messages = await session_app_service.get_messages(created_session["session_id"])
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_register_sse_connection():
    """测试注册SSE连接"""
    session_app_service = SessionAppService()
    created_session = await session_app_service.create_session("user1", "agent1")
    
    queue = await session_app_service.register_sse_connection(created_session["session_id"])
    assert queue is not None
    
    # 验证连接是否已注册
    assert created_session["session_id"] in session_app_service.sse_connections


@pytest.mark.asyncio
async def test_unregister_sse_connection():
    """测试注销SSE连接"""
    session_app_service = SessionAppService()
    created_session = await session_app_service.create_session("user1", "agent1")
    
    # 注册连接
    await session_app_service.register_sse_connection(created_session["session_id"])
    assert created_session["session_id"] in session_app_service.sse_connections
    
    # 注销连接
    await session_app_service.unregister_sse_connection(created_session["session_id"])
    assert created_session["session_id"] not in session_app_service.sse_connections


@pytest.mark.asyncio
async def test_cleanup_timeout_sessions():
    """测试清理超时会话"""
    session_app_service = SessionAppService()
    created_session = await session_app_service.create_session("user1", "agent1")
    
    # 注册SSE连接
    await session_app_service.register_sse_connection(created_session["session_id"])
    assert created_session["session_id"] in session_app_service.sse_connections
    
    # 清理超时会话
    await session_app_service.cleanup_timeout_sessions()
    
    # 验证会话是否被清理
    retrieved_session = await session_app_service.get_session(created_session["session_id"])
    assert retrieved_session is None
    assert created_session["session_id"] not in session_app_service.sse_connections


@pytest.mark.asyncio
async def test_get_active_session_count():
    """测试获取活跃会话数量"""
    session_app_service = SessionAppService()
    
    # 创建两个会话
    await session_app_service.create_session("user1", "agent1")
    await session_app_service.create_session("user2", "agent2")
    
    count = await session_app_service.get_active_session_count()
    assert count == 2
    
    # 中断一个会话
    sessions = list(session_app_service.session_service.sessions.values())
    if sessions:
        await session_app_service.interrupt_session(sessions[0].session_id)
        
        # 再次获取活跃会话数量
        count = await session_app_service.get_active_session_count()
        assert count == 1