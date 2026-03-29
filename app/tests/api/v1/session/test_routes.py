import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


@pytest.fixture
async def create_test_session():
    """创建测试会话"""
    response = client.post(
        "/api/v1/session/create",
        json={"user_id": "test_user", "agent_id": "test_agent"}
    )
    assert response.status_code == 200
    return response.json()


async def test_create_session():
    """测试创建会话API"""
    response = client.post(
        "/api/v1/session/create",
        json={"user_id": "test_user", "agent_id": "test_agent"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["user_id"] == "test_user"
    assert data["agent_id"] == "test_agent"
    assert data["status"] == "active"
    assert "created_at" in data


async def test_get_session(create_test_session):
    """测试获取会话API"""
    session = create_test_session
    response = client.get(f"/api/v1/session/get/{session['session_id']}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session["session_id"]
    assert data["user_id"] == "test_user"
    assert data["agent_id"] == "test_agent"


async def test_interrupt_session(create_test_session):
    """测试中断会话API"""
    session = create_test_session
    response = client.post(f"/api/v1/session/interrupt/{session['session_id']}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # 验证会话状态已更新
    response = client.get(f"/api/v1/session/get/{session['session_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "interrupted"


async def test_add_message(create_test_session):
    """测试添加消息API"""
    session = create_test_session
    response = client.post(
        "/api/v1/session/message",
        json={
            "session_id": session["session_id"],
            "role": "user",
            "content": "Hello, world!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "message_id" in data
    assert data["session_id"] == session["session_id"]
    assert data["role"] == "user"
    assert data["content"] == "Hello, world!"
    assert "token_count" in data
    assert "created_at" in data


async def test_get_messages(create_test_session):
    """测试获取消息API"""
    session = create_test_session
    
    # 添加两条消息
    client.post(
        "/api/v1/session/message",
        json={
            "session_id": session["session_id"],
            "role": "user",
            "content": "Hello"
        }
    )
    
    client.post(
        "/api/v1/session/message",
        json={
            "session_id": session["session_id"],
            "role": "assistant",
            "content": "Hi there!"
        }
    )
    
    # 获取消息
    response = client.get(f"/api/v1/session/messages/{session['session_id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["role"] == "user"
    assert data[1]["role"] == "assistant"


async def test_get_active_session_count():
    """测试获取活跃会话数量API"""
    response = client.get("/api/v1/session/stats/active")
    assert response.status_code == 200
    data = response.json()
    assert "active_sessions" in data
    assert isinstance(data["active_sessions"], int)
    assert data["active_sessions"] >= 0


async def test_sse_endpoint(create_test_session):
    """测试SSE端点"""
    session = create_test_session
    response = client.get(
        f"/api/v1/session/sse/{session['session_id']}",
        headers={"Accept": "text/event-stream"}
    )
    
    # SSE连接应该成功建立
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/event-stream"
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["Connection"] == "keep-alive"


async def test_get_nonexistent_session():
    """测试获取不存在的会话"""
    response = client.get("/api/v1/session/get/nonexistent_session_id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


async def test_interrupt_nonexistent_session():
    """测试中断不存在的会话"""
    response = client.post("/api/v1/session/interrupt/nonexistent_session_id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


async def test_sse_nonexistent_session():
    """测试SSE不存在的会话"""
    response = client.get(
        "/api/v1/session/sse/nonexistent_session_id",
        headers={"Accept": "text/event-stream"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"