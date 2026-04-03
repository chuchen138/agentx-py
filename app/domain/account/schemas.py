from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any, List

class PositiveDecimal(Decimal):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not isinstance(v, Decimal):
            v = Decimal(str(v))
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v.as_tuple().exponent < -2:
            raise ValueError('Amount must have at most 2 decimal places')
        if v > Decimal('100000000'):
            raise ValueError('Amount must be less than 100,000,000')
        return v

class AccountBase(BaseModel):
    user_id: int

class AccountCreate(AccountBase):
    pass

class AccountResponse(AccountBase):
    id: int
    balance: Decimal
    credit: Decimal
    total_consumed: Decimal
    version: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AccountUpdate(BaseModel):
    balance: Optional[Decimal] = None
    credit: Optional[Decimal] = None

class RechargeRequest(BaseModel):
    amount: PositiveDecimal
    payment_platform: str
    payment_type: str

class CreditRequest(BaseModel):
    amount: PositiveDecimal
    reason: str

class OrderBase(BaseModel):
    user_id: int
    type: str
    title: str
    description: Optional[str] = None
    amount: Decimal
    currency: str = "CNY"

class OrderCreate(OrderBase):
    payment_platform: str
    payment_type: str

class OrderResponse(OrderBase):
    id: int
    order_no: str
    status: str
    paid_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None
    refund_amount: Decimal
    transaction_id: Optional[str] = None
    order_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UsageRecordBase(BaseModel):
    user_id: int
    product_id: int
    billing_type: str
    service_id: str
    usage_data: Dict[str, Any]
    amount: Decimal

class UsageRecordCreate(UsageRecordBase):
    request_id: str
    order_id: Optional[int] = None

class UsageRecordResponse(UsageRecordBase):
    id: int
    request_id: str
    order_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    billing_type: str
    service_id: str
    rule_id: Optional[str] = None
    price_config: Dict[str, Any]

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BillingRequest(BaseModel):
    user_id: int
    product_id: int
    service_id: str
    usage_data: Dict[str, Any]
    request_id: str

class BillingResponse(BaseModel):
    success: bool
    amount: Decimal
    usage_record_id: Optional[int] = None
    message: Optional[str] = None

class RefundRequest(BaseModel):
    order_id: int
    amount: PositiveDecimal
    reason: str

class RefundResponse(BaseModel):
    success: bool
    refund_amount: Decimal
    message: Optional[str] = None
