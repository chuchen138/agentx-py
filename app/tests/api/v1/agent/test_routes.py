from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# 测试智能体创建
def test_create_agent():
    response = client.post("/api/v1/agents", json={
        "name": "测试智能体",
        "description": "这是一个测试智能体",
        "system_prompt": "你是一个测试智能体",
        "welcome_message": "欢迎使用测试智能体"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "测试智能体"
    assert data["description"] == "这是一个测试智能体"

# 测试智能体列表查询
def test_list_agents():
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

# 测试智能体详情查询
def test_get_agent():
    # 先创建一个智能体
    create_response = client.post("/api/v1/agents", json={
        "name": "测试智能体 2",
        "description": "这是第二个测试智能体"
    })
    agent_id = create_response.json()["id"]
    
    # 查询智能体详情
    response = client.get(f"/api/v1/agents/{agent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == agent_id
    assert data["name"] == "测试智能体 2"

# 测试智能体更新
def test_update_agent():
    # 先创建一个智能体
    create_response = client.post("/api/v1/agents", json={
        "name": "测试智能体 3",
        "description": "这是第三个测试智能体"
    })
    agent_id = create_response.json()["id"]
    
    # 更新智能体
    response = client.put(f"/api/v1/agents/{agent_id}", json={
        "name": "更新后的测试智能体",
        "description": "这是更新后的测试智能体"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后的测试智能体"
    assert data["description"] == "这是更新后的测试智能体"

# 测试智能体删除
def test_delete_agent():
    # 先创建一个智能体
    create_response = client.post("/api/v1/agents", json={
        "name": "测试智能体 4",
        "description": "这是第四个测试智能体"
    })
    agent_id = create_response.json()["id"]
    
    # 删除智能体
    response = client.delete(f"/api/v1/agents/{agent_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
