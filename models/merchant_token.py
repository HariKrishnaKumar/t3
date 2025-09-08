# models/merchant_detail.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship
from datetime import datetime
from database.database import Base


class MerchantToken(Base):
    __tablename__ = 'merchant_tokens'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    merchant_id = Column(Integer, ForeignKey('merchants.id'), nullable=False)
    token = Column(Text, nullable=False)
    token_type = Column(String(100), default="api")
    created_at = Column(DateTime, default=datetime.utcnow)

    merchant = relationship("Merchant", back_populates="tokens")
