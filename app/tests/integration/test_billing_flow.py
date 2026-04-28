import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import Mock, patch
from decimal import Decimal

@pytest.fixture
async def client():
    with TestClient(app) as client:
        yield client

@pytest.mark.asyncio
async def test_account_creation(client):
    """测试账户自动创建"""
    # 模拟用户认证
    with patch('app.api.v1.account.routes.get_current_user', return_value=1):
        response = client.get("/api/accounts/me")
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == 1
        assert data["balance"] == "0.00"
        assert data["credit"] == "0.00"

@pytest.mark.asyncio
async def test_recharge(client):
    """测试账户充值"""
    # 模拟用户认证
    with patch('app.api.v1.account.routes.get_current_user', return_value=1):
        # 模拟订单创建
        with patch('app.application.account.service.OrderRepository.create', return_value=Mock(
            id=1,
            order_no="RECHARGE_TEST",
            amount=Decimal('100.00'),
            status="pending",
            payment_platform="alipay"
        )):
            response = client.post("/api/accounts/recharge", json={
                "amount": "100.00",
                "payment_platform": "alipay",
                "payment_type": "scan"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["amount"] == "100.00"
            assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_billing(client):
    """测试计费流程"""
    # 模拟用户认证
    with patch('app.api.v1.billing.routes.get_current_user', return_value=1):
        # 模拟计费服务
        with patch('app.application.billing.service.BillingService.charge', return_value=Mock(
            success=True,
            amount=Decimal('1.00'),
            usage_record_id=1,
            message="Billing successful"
        )):
            response = client.post("/api/billing/charge", json={
                "user_id": 1,
                "product_id": 1,
                "service_id": "llm",
                "usage_data": {"token_count": 1000},
                "request_id": "test-billing-request"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["amount"] == "1.00"

@pytest.mark.asyncio
async def test_get_usage_records(client):
    """测试获取用量记录"""
    # 模拟用户认证
    with patch('app.api.v1.billing.routes.get_current_user', return_value=1):
        # 模拟获取用量记录
        with patch('app.application.billing.service.BillingService.get_usage_records', return_value=[
            Mock(
                id=1,
                user_id=1,
                product_id=1,
                request_id="test-request-1",
                billing_type="token",
                service_id="llm",
                usage_data={"token_count": 1000},
                amount=Decimal('1.00'),
                created_at="2024-01-01T00:00:00"
            )
        ]):
            response = client.get("/api/billing/usage-records")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["user_id"] == 1
            assert data[0]["amount"] == "1.00"

@pytest.mark.asyncio
async def test_get_orders(client):
    """测试获取订单列表"""
    # 模拟用户认证
    with patch('app.api.v1.orders.routes.get_current_user', return_value=1):
        # 模拟获取订单
        with patch('app.domain.account.repository.OrderRepository.get_by_user_id', return_value=[
            Mock(
                id=1,
                user_id=1,
                order_no="RECHARGE_TEST",
                type="recharge",
                title="账户充值",
                amount=Decimal('100.00'),
                status="pending",
                created_at="2024-01-01T00:00:00"
            )
        ]):
            response = client.get("/api/orders")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["user_id"] == 1
            assert data[0]["amount"] == "100.00"
