# from fastapi import APIRouter

# router = APIRouter()

# @router.get("/users")
# def get_users():
#     return {"message": "List of users"}
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User

router = APIRouter()

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users

@router.get("/users/{mobile_number}")
def get_user_by_mobile_number(mobile_number: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.mobile_number == mobile_number).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user  