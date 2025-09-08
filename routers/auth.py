from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import SessionLocal
from models.user import User
from models.user_schema import MobileLogin, OTPVerify, OTPVerifyRequest, RegisterRequest
from models.otp import OTP
from datetime import datetime, timedelta
from dependencies import get_current_user_simple as get_current_user



router = APIRouter()

STATIC_OTP = "123456"  # Static OTP for now

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/send-otp")
# def send_otp(data: MobileLogin):
#     mobile = data.mobile
#     # send a static OTP here or generate one
#     otp = STATIC_OTP
#     # Ideally store OTP in Redis or a temp table with expiry
#     return {"message": f"OTP sent to {mobile}", "otp": otp}
#     if request.otp != STATIC_OTP:
#         raise HTTPException(status_code=400, detail="Invalid OTP")

def send_otp(data: MobileLogin, db: Session = Depends(get_db)):
    otp_entry = OTP(
        mobile_number=data.mobile,
        otp_code=STATIC_OTP,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.add(otp_entry)
    db.commit()
    db.refresh(otp_entry)
    user = db.query(User).filter(User.mobile_number == data.mobile).first()
    if not user:
        user = User(mobile_number=data.mobile, otp=STATIC_OTP)
        db.add(user)
    else:
        # update OTP if user already exists
        user.otp = STATIC_OTP
        db.commit()
        db.refresh(user)
    # Normally, send the OTP using SMS here.
    return {"message": f"OTP sent to {data.mobile}", "otp": STATIC_OTP}  # DEBUG ONLY

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
        # 🟢 Create a new user
        new_user = User(
            mobile_number=request.mobile,
            # Add any other default values (e.g. name, created_at, etc.)
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    return {"message": "OTP verified successfully", "user_created": not user}

# def verify_otp(data: OTPVerify, db: Session = Depends(get_db)):
#     if data.otp != STATIC_OTP:
#         raise HTTPException(status_code=400, detail="Invalid OTP")

#     user = db.query(User).filter(User.mobile_number == data.mobile).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     return {"message": "Login successful", "user_id": user.id}

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

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.token = None   # Clear token
    db.commit()
    return {"message": "Logged out successfully"}
