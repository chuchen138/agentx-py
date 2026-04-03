from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from decimal import Decimal
from app.application.account.service import AccountAppService
from app.domain.account.schemas import AccountResponse, RechargeRequest, CreditRequest
from app.infrastructure.dependency_injection import get_account_app_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/accounts", tags=["account"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    # 这里应该从JWT token中获取用户ID
    # 暂时返回固定用户ID作为示例
    return 1

@router.get("/me", response_model=AccountResponse)
async def get_current_account(
    user_id: int = Depends(get_current_user),
    account_app_service: AccountAppService = Depends(get_account_app_service)
):
    account = await account_app_service.get_user_account(user_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/{id}", response_model=AccountResponse)
async def get_account_by_id(
    id: int,
    user_id: int = Depends(get_current_user),
    account_app_service: AccountAppService = Depends(get_account_app_service)
):
    account = await account_app_service.get_account_by_id(id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    # 这里应该添加权限检查，确保用户只能查看自己的账户
    if account.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return account

@router.post("/recharge", response_model=Dict[str, Any])
async def recharge(
    recharge_request: RechargeRequest,
    user_id: int = Depends(get_current_user),
    account_app_service: AccountAppService = Depends(get_account_app_service)
):
    result = await account_app_service.recharge(user_id, recharge_request)
    return result

@router.post("/credit", response_model=Dict[str, Any])
async def add_credit(
    credit_request: CreditRequest,
    user_id: int = Depends(get_current_user),
    account_app_service: AccountAppService = Depends(get_account_app_service)
):
    # 这里应该添加管理员权限检查
    result = await account_app_service.add_credit(user_id, credit_request)
    return result

@router.get("/balance", response_model=Dict[str, Any])
async def get_available_balance(
    user_id: int = Depends(get_current_user),
    account_app_service: AccountAppService = Depends(get_account_app_service)
):
    balance_info = await account_app_service.get_account_balance(user_id)
    return balance_info
