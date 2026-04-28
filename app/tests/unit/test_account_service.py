import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal
from app.domain.account.service import AccountDomainService
from app.domain.account.repository import AccountRepository
from app.domain.account.model import Account

@pytest.mark.asyncio
async def test_create_account():
    # 模拟仓库
    mock_repo = Mock(spec=AccountRepository)
    mock_repo.create = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('0.00'),
        credit=Decimal('0.00'),
        total_consumed=Decimal('0.00'),
        version=0
    ))
    
    service = AccountDomainService(mock_repo)
    account = await service.create_account(123)
    
    assert account.user_id == 123
    assert account.balance == Decimal('0.00')
    assert account.credit == Decimal('0.00')
    mock_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_recharge():
    # 模拟仓库
    mock_repo = Mock(spec=AccountRepository)
    mock_repo.get_by_user_id = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('100.00'),
        credit=Decimal('50.00'),
        total_consumed=Decimal('0.00'),
        version=0
    ))
    mock_repo.update = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('150.00'),
        credit=Decimal('50.00'),
        total_consumed=Decimal('0.00'),
        version=1
    ))
    
    service = AccountDomainService(mock_repo)
    account = await service.recharge(123, Decimal('50.00'))
    
    assert account.balance == Decimal('150.00')
    mock_repo.get_by_user_id.assert_called_once_with(123)
    mock_repo.update.assert_called_once()

@pytest.mark.asyncio
async def test_add_credit():
    # 模拟仓库
    mock_repo = Mock(spec=AccountRepository)
    mock_repo.get_by_user_id = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('100.00'),
        credit=Decimal('50.00'),
        total_consumed=Decimal('0.00'),
        version=0
    ))
    mock_repo.update = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('100.00'),
        credit=Decimal('150.00'),
        total_consumed=Decimal('0.00'),
        version=1
    ))
    
    service = AccountDomainService(mock_repo)
    account = await service.add_credit(123, Decimal('100.00'), "Test credit")
    
    assert account.credit == Decimal('150.00')
    mock_repo.get_by_user_id.assert_called_once_with(123)
    mock_repo.update.assert_called_once()

@pytest.mark.asyncio
async def test_deduct_balance_success():
    # 模拟仓库
    mock_repo = Mock(spec=AccountRepository)
    mock_repo.get_by_user_id = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('100.00'),
        credit=Decimal('50.00'),
        total_consumed=Decimal('0.00'),
        version=0
    ))
    mock_repo.update = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('50.00'),
        credit=Decimal('50.00'),
        total_consumed=Decimal('50.00'),
        version=1
    ))
    
    service = AccountDomainService(mock_repo)
    result = await service.deduct_balance(123, Decimal('50.00'))
    
    assert result is True
    mock_repo.get_by_user_id.assert_called_once_with(123)
    mock_repo.update.assert_called_once()

@pytest.mark.asyncio
async def test_deduct_balance_insufficient():
    # 模拟仓库
    mock_repo = Mock(spec=AccountRepository)
    mock_repo.get_by_user_id = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('10.00'),
        credit=Decimal('5.00'),
        total_consumed=Decimal('0.00'),
        version=0
    ))
    
    service = AccountDomainService(mock_repo)
    result = await service.deduct_balance(123, Decimal('20.00'))
    
    assert result is False
    mock_repo.get_by_user_id.assert_called_once_with(123)
    mock_repo.update.assert_not_called()

@pytest.mark.asyncio
async def test_get_available_balance():
    # 模拟仓库
    mock_repo = Mock(spec=AccountRepository)
    mock_repo.get_by_user_id = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('100.00'),
        credit=Decimal('50.00'),
        total_consumed=Decimal('0.00'),
        version=0
    ))
    
    service = AccountDomainService(mock_repo)
    balance = await service.get_available_balance(123)
    
    assert balance == Decimal('150.00')
    mock_repo.get_by_user_id.assert_called_once_with(123)

@pytest.mark.asyncio
async def test_check_sufficient_balance():
    # 模拟仓库
    mock_repo = Mock(spec=AccountRepository)
    mock_repo.get_by_user_id = AsyncMock(return_value=Account(
        id=1,
        user_id=123,
        balance=Decimal('100.00'),
        credit=Decimal('50.00'),
        total_consumed=Decimal('0.00'),
        version=0
    ))
    
    service = AccountDomainService(mock_repo)
    # 余额充足
    assert await service.check_sufficient_balance(123, Decimal('150.00')) is True
    # 余额不足
    assert await service.check_sufficient_balance(123, Decimal('151.00')) is False
