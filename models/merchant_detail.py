# models/merchant_detail.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base


class MerchantDetail(Base):
    __tablename__ = 'merchant_detail'

    id = Column(Integer, primary_key=True, index=True)
    clover_merchant_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    currency = Column(String(16), nullable=True)
    timezone = Column(String(64), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    # created_at = Column(DateTime, default=datetime.utcnow)
    # updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# class MerchantToken(Base):
#     __tablename__ = 'merchant_tokens'

#     id = Column(Integer, primary_key=True, index=True)
#     merchant_id = Column(Integer, ForeignKey('merchants.id'), nullable=False)
#     token = Column(Text, nullable=False)
#     token_type = Column(String(100), default="api")
#     created_at = Column(DateTime, default=datetime.utcnow)

#     merchant = relationship("Merchant", back_populates="tokens")
