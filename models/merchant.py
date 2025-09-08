# models/merchant.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base


class Merchant(Base):
    __tablename__ = 'merchants'

    id = Column(Integer, primary_key=True, index=True)
    clover_merchant_id = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    email = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    tokens = relationship("MerchantToken", back_populates="merchant")

# class MerchantToken(Base):
#     __tablename__ = 'merchant_tokens'

#     id = Column(Integer, primary_key=True, index=True)
#     merchant_id = Column(Integer, ForeignKey('merchants.id'), nullable=False)
#     token = Column(Text, nullable=False)
#     token_type = Column(String(100), default="api")
#     created_at = Column(DateTime, default=datetime.utcnow)

#     merchant = relationship("Merchant", back_populates="tokens")
