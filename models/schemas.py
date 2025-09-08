from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String(15), unique=True, nullable=False)
    otp = Column(String(6), nullable=True)  # store OTP temporarily
    is_verified = Column(Boolean, default=False)

    name = Column(String(100), nullable=True)
    alternate_contact = Column(String(15), nullable=True)
    floor_or_office = Column(String(255), nullable=True)

    is_guest = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
