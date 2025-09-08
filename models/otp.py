from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OTP(Base):
    __tablename__ = 'otps'

    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String(15), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    is_verified = Column(Boolean, default=False)               # ✅ whether OTP is used
    expires_at = Column(DateTime(timezone=True), nullable=True) # ✅ OTP expiry time
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
