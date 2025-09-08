from pydantic import BaseModel, EmailStr, constr
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

class UserUpdate(UserBase):
    password: Optional[str] = None
    # Add the preference field for updating user preferences
    preference: Optional[Dict[str, Any]] = None

class UserOut(UserBase):
    id: int
    is_active: bool
    preference: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes= True

class PreferenceUpdateRequest(BaseModel):
    mobile_number: str
    preference: Dict[str, Any]