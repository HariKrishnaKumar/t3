# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session
# from database.database import SessionLocal
# from models.user import User
# from models.user_schema import MobileLogin, OTPVerify, OTPVerifyRequest, RegisterRequest
# from models.otp import OTP
# from datetime import datetime, timedelta
# from dependencies import get_current_user_simple as get_current_user
# from typing import Optional

# router = APIRouter()

# STATIC_OTP = "123456"

# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# @router.post("/send-otp")
# def send_otp(data: MobileLogin, db: Session = Depends(get_db)):
#     # Create an OTP entry
#     otp_entry = OTP(
#         mobile_number=data.mobile,
#         otp_code=STATIC_OTP,
#         expires_at=datetime.utcnow() + timedelta(minutes=5)
#     )
#     db.add(otp_entry)
#     db.commit()
#     db.refresh(otp_entry)

#     # Check if user already exists
#     user = db.query(User).filter(User.mobile_number == data.mobile).first()
#     if not user:
#         # If not, create a new user with mobile number and initial is_verified status
#         user = User(mobile_number=data.mobile)
#         db.add(user)
    
#     db.commit()
#     db.refresh(user)

#     # Normally, send the OTP using an SMS service here.
#     return {"message": f"OTP sent to {data.mobile}", "otp": STATIC_OTP}

# @router.post("/verify-otp")
# def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
#     otp_entry = db.query(OTP).filter(
#         OTP.mobile_number == request.mobile,
#         OTP.otp_code == request.otp
#     ).first()

#     if not otp_entry:
#         raise HTTPException(status_code=400, detail="Invalid OTP")

#     # ✅ OTP is valid: now check if user exists
#     user = db.query(User).filter(User.mobile_number == request.mobile).first()

#     if not user:
#         # 🟢 Create a new user if they don't exist
#         new_user = User(
#             mobile_number=request.mobile,
#             is_verified=True,  # ✅ Set to True on successful verification
#         )
#         db.add(new_user)
#         db.commit()
#         db.refresh(new_user)
#         return {"message": "OTP verified successfully", "user_created": True}
#     else:
#         # 🟢 Update existing user
#         user.is_verified = True # ✅ Set to True on successful verification
#         db.commit()
#         db.refresh(user)
#         return {"message": "OTP verified successfully", "user_created": False}

# @router.post("/logout")
# def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     current_user.token = None
#     db.commit()
#     return {"message": "Logged out successfully"}

# def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.mobile_number == data.mobile).first()
#     if user:
#         raise HTTPException(status_code=400, detail="User already exists")

#     user = User(
#         name=data.name,
#         mobile_number=data.mobile,
#         email=data.email
#     )
#     db.add(user)
#     db.commit()
#     db.refresh(user)
#     return {"message": "User registered successfully", "user_id": user.id}
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.user import User
from models.user_schema import MobileLogin, OTPVerify, OTPVerifyRequest, RegisterRequest
from models.otp import OTP
from datetime import datetime, timedelta
from dependencies import get_current_user_simple as get_current_user
from typing import Optional

router = APIRouter()

STATIC_OTP = "123456"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/send-otp")
def send_otp(data: MobileLogin, db: Session = Depends(get_db)):
    # Create an OTP entry
    otp_entry = OTP(
        mobile_number=data.mobile,
        otp_code=STATIC_OTP,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.add(otp_entry)
    db.commit()
    db.refresh(otp_entry)

    # Check if user already exists
    user = db.query(User).filter(User.mobile_number == data.mobile).first()
    if not user:
        # If not, create a new user with mobile number and initial is_verified status
        user = User(mobile_number=data.mobile)
        db.add(user)
    
    db.commit()
    db.refresh(user)

    # Normally, send the OTP using an SMS service here.
    return {"message": f"OTP sent to {data.mobile}", "otp": STATIC_OTP}

@router.post("/verify-otp")
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    otp_entry = db.query(OTP).filter(
        OTP.mobile_number == request.mobile,
        OTP.otp_code == request.otp
    ).first()

    if not otp_entry:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # ✅ OTP is valid: now check if user exists
    user = db.query(User).filter(User.mobile_number == request.mobile).first()

    if not user:
        # 🟢 Create a new user if they don't exist
        new_user = User(
            mobile_number=request.mobile,
            is_verified=True,  # ✅ Set to True on successful verification
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"message": "OTP verified successfully", "user_created": True}
    else:
        # 🟢 Update existing user
        user.is_verified = True # ✅ Set to True on successful verification
        db.commit()
        db.refresh(user)
        return {"message": "OTP verified successfully", "user_created": False}

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.token = None
    db.commit()
    return {"message": "Logged out successfully"}

def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.mobile_number == data.mobile).first()
    if user:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        name=data.name,
        mobile_number=data.mobile,
        email=data.email
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered successfully", "user_id": user.id}