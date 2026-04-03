import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal
from app.domain.billing.service import BillingDomainService, TokenUsageStrategy, StorageUsageStrategy
from app.domain.account.repository import UsageRecordRepository, ProductRepository
from app.domain.account.model import Product, UsageRecord

@pytest.mark.asyncio
async def test_token_usage_strategy():
    strategy = TokenUsageStrategy()
    product = Product(
        id=1,
        name="Token Product",
        billing_type="token",
        service_id="llm",
        price_config={"price_per_token": "0.001"}
    )
    usage_data = {"token_count": 1000}
    amount = await strategy.calculate(product, usage_data)
    assert amount == Decimal('1.00')

@pytest.mark.asyncio
async def test_storage_usage_strategy():
    strategy = StorageUsageStrategy()
    product = Product(
        id=1,
        name="Storage Product",
        billing_type="storage",
        service_id="storage",
        price_config={"price_per_mb": "0.01"}
    )
    usage_data = {"storage_mb": 500}
    amount = await strategy.calculate(product, usage_data)
    assert amount == Decimal('5.00')

@pytest.mark.asyncio
async def test_calculate_usage():
    # 模拟仓库
    mock_usage_repo = Mock(spec=UsageRecordRepository)
    mock_product_repo = Mock(spec=ProductRepository)
    mock_product_repo.get_by_id = AsyncMock(return_value=Product(
        id=1,
        name="Token Product",
        billing_type="token",
        service_id="llm",
        price_config={"price_per_token": "0.001"}
    ))
    
    service = BillingDomainService(mock_usage_repo, mock_product_repo)
    amount = await service.calculate_usage(1, {"token_count": 1000})
    assert amount == Decimal('1.00')

@pytest.mark.asyncio
async def test_create_usage_record():
    # 模拟仓库
    mock_usage_repo = Mock(spec=UsageRecordRepository)
    mock_usage_repo.get_by_request_id = AsyncMock(return_value=None)
    mock_usage_repo.create = AsyncMock(return_value=UsageRecord(
        id=1,
        user_id=123,
        product_id=1,
        request_id="test-request-id",
        billing_type="token",
        service_id="llm",
        usage_data={"token_count": 1000},
        amount=Decimal('1.00')
    ))
    mock_product_repo = Mock(spec=ProductRepository)
    
    service = BillingDomainService(mock_usage_repo, mock_product_repo)
    record = await service.create_usage_record(
        user_id=123,
        product_id=1,
        order_id=None,
        request_id="test-request-id",
        billing_type="token",
        service_id="llm",
        usage_data={"token_count": 1000},
        amount=Decimal('1.00')
    )
    
    assert record.id == 1
    assert record.user_id == 123
    mock_usage_repo.get_by_request_id.assert_called_once_with("test-request-id")
    mock_usage_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_idempotency_check():
    # 模拟仓库
    mock_usage_repo = Mock(spec=UsageRecordRepository)
    mock_usage_repo.get_by_request_id = AsyncMock(return_value=UsageRecord(
        id=1,
        user_id=123,
        product_id=1,
        request_id="test-request-id",
        billing_type="token",
        service_id="llm",
        usage_data={"token_count": 1000},
        amount=Decimal('1.00')
    ))
    mock_product_repo = Mock(spec=ProductRepository)
    
    service = BillingDomainService(mock_usage_repo, mock_product_repo)
    # 检查幂等性
    assert await service.check_idempotency("test-request-id") is True
    # 检查不存在的请求ID
    mock_usage_repo.get_by_request_id = AsyncMock(return_value=None)
    assert await service.check_idempotency("new-request-id") is False
