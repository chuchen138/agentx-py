from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
from app.application.billing.service import BillingService
from app.domain.account.schemas import BillingRequest, BillingResponse
from app.infrastructure.dependency_injection import get_billing_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    # 这里应该从JWT token中获取用户ID
    # 暂时返回固定用户ID作为示例
    return 1

@router.post("/charge", response_model=BillingResponse)
async def charge(
    billing_request: BillingRequest,
    user_id: int = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    # 确保请求的用户ID与当前用户一致
    if billing_request.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await billing_service.charge(billing_request)
    return result

@router.get("/usage-records", response_model=List[Dict[str, Any]])
async def get_usage_records(
    limit: int = 100,
    user_id: int = Depends(get_current_user),
    billing_service: BillingService = Depends(get_billing_service)
):
    records = await billing_service.get_usage_records(user_id, limit)
    # 转换为字典格式返回
    return [{
        "id": record.id,
        "user_id": record.user_id,
        "product_id": record.product_id,
        "order_id": record.order_id,
        "request_id": record.request_id,
        "billing_type": record.billing_type,
        "service_id": record.service_id,
        "usage_data": record.usage_data,
        "amount": record.amount,
        "created_at": record.created_at
    } for record in records]
