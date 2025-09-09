from pydantic import BaseModel, EmailStr, constr, Field
from typing import Optional, Dict, Any


class MobileLogin(BaseModel):
    mobile: str

class OTPVerify(BaseModel):
    mobile: str
    otp: str

class OTPVerifyRequest(BaseModel):
    mobile: str
    otp: str

class RegisterRequest(BaseModel):
    name: str
    mobile: constr(pattern=r'^[6-9]\d{9}$')  # ✅ Use pattern in Pydantic v2
    email: EmailStr
    password: constr(min_length=6)

# new code
class UpdateProfile(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    address: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    alternate_contact: Optional[str] = None
    floor_or_office: Optional[str] = None
    address: Optional[str] = None

class UserOut(BaseModel):
    id: int
    mobile_number: str
    name: Optional[str] = None
    alternate_contact: Optional[str] = None
    floor_or_office: Optional[str] = None
    address: Optional[str] = None
    preference: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class PreferenceUpdateRequest(BaseModel):
    mobile_number: str
    preference: str = Field(..., description="The selected preference (e.g., 'pickup', 'delivery')")

    # from_attributes