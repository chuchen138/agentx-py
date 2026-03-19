import pytest
from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


def test_avatar_upload_endpoint():
    """测试头像上传端点"""
    # 生成测试用户ID
    user_id = str(uuid.uuid4())
    
    # 测试上传头像
    response = client.post(
        "/api/v1/files/upload/avatar",
        files={"file": ("avatar.png", b"fake image content", "image/png")},
        data={"user_id": user_id}
    )
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert "file_url" in data
    assert "file_name" in data
    assert "file_size" in data
    assert "mime_type" in data


def test_general_upload_endpoint():
    """测试通用文件上传端点"""
    # 生成测试用户ID
    user_id = str(uuid.uuid4())
    
    # 测试上传通用文件
    response = client.post(
        "/api/v1/files/upload/general",
        files={"file": ("document.txt", b"fake document content", "text/plain")},
        data={"user_id": user_id}
    )
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert "file_url" in data
    assert "file_name" in data
    assert "file_size" in data
    assert "mime_type" in data


def test_rag_upload_endpoint():
    """测试RAG文件上传端点"""
    # 生成测试用户ID和数据集ID
    user_id = str(uuid.uuid4())
    dataset_id = str(uuid.uuid4())
    
    # 测试上传RAG文件
    response = client.post(
        "/api/v1/files/upload/rag",
        files={"file": ("document.pdf", b"fake pdf content", "application/pdf")},
        data={"user_id": user_id, "dataset_id": dataset_id}
    )
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert "file_url" in data
    assert "file_name" in data
    assert "file_size" in data
    assert "mime_type" in data
