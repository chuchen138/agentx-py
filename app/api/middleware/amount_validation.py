from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from decimal import Decimal, InvalidOperation
import json
import logging

logger = logging.getLogger(__name__)

class AmountValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 只处理POST和PUT请求
        if request.method in ["POST", "PUT"]:
            try:
                # 读取请求体
                body = await request.body()
                if body:
                    # 解析JSON
                    data = json.loads(body.decode("utf-8"))
                    # 验证金额字段
                    self._validate_amounts(data)
                    # 将验证后的数据重新设置到请求中
                    # 注意：在FastAPI中，修改请求体需要特殊处理
                    # 这里我们只是验证，不修改数据
            except json.JSONDecodeError:
                # 如果不是JSON格式，跳过验证
                pass
            except Exception as e:
                logger.error(f"Amount validation error: {e}")
                raise HTTPException(status_code=400, detail=str(e))
        
        # 继续处理请求
        response = await call_next(request)
        return response
    
    def _validate_amounts(self, data: dict):
        """验证数据中的金额字段"""
        amount_fields = ["amount", "credit", "refund_amount"]
        
        for field in amount_fields:
            if field in data:
                self._validate_amount(data[field], field)
        
        # 递归检查嵌套结构
        for key, value in data.items():
            if isinstance(value, dict):
                self._validate_amounts(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._validate_amounts(item)
    
    def _validate_amount(self, amount, field_name):
        """验证单个金额值"""
        try:
            # 转换为Decimal
            if isinstance(amount, str):
                amount_decimal = Decimal(amount)
            elif isinstance(amount, (int, float)):
                amount_decimal = Decimal(str(amount))
            else:
                raise ValueError(f"Invalid amount type for {field_name}")
            
            # 验证金额必须大于0
            if amount_decimal <= 0:
                raise ValueError(f"{field_name} must be positive")
            
            # 验证金额精度（最多2位小数）
            if amount_decimal.as_tuple().exponent < -2:
                raise ValueError(f"{field_name} must have at most 2 decimal places")
            
            # 验证金额大小（防止溢出）
            if amount_decimal > Decimal("100000000"):  # 10^8
                raise ValueError(f"{field_name} must be less than 100,000,000")
                
        except InvalidOperation:
            raise ValueError(f"Invalid amount format for {field_name}")
