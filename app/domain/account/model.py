from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    balance = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    credit = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    total_consumed = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    usage_records = relationship("UsageRecord", back_populates="account")
    orders = relationship("Order", back_populates="account")

class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.user_id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    request_id = Column(String(255), unique=True, index=True, nullable=False)
    billing_type = Column(String(50), nullable=False)
    service_id = Column(String(50), nullable=False)
    usage_data = Column(JSON, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    account = relationship("Account", back_populates="usage_records")
    product = relationship("Product", back_populates="usage_records")
    order = relationship("Order", back_populates="usage_records")
    
    __table_args__ = (
        Index('idx_user_id_created_at', 'user_id', 'created_at'),
    )

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.user_id"), nullable=False)
    order_no = Column(String(255), unique=True, index=True, nullable=False)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(10), default="CNY", nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    paid_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    expired_at = Column(DateTime, nullable=True)
    refund_amount = Column(DECIMAL(10, 2), default=0.00, nullable=False)
    payment_platform = Column(String(50), nullable=True)
    payment_type = Column(String(50), nullable=True)
    transaction_id = Column(String(255), nullable=True)
    order_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    account = relationship("Account", back_populates="orders")
    usage_records = relationship("UsageRecord", back_populates="order")
    
    __table_args__ = (
        Index('idx_user_id_status', 'user_id', 'status'),
    )

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    billing_type = Column(String(50), nullable=False)
    service_id = Column(String(50), nullable=False)
    rule_id = Column(String(50), nullable=True)
    price_config = Column(JSON, nullable=False)
    status = Column(String(50), default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    usage_records = relationship("UsageRecord", back_populates="product")
