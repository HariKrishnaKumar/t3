from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User as DBUser
from models.user_schema import UserOut, PreferenceUpdateRequest

router = APIRouter()

@router.get("/users")
def get_users():
    return {"users": ["John", "Jane", "Bob"]}

@router.post("/users")
def create_user(name: str, email: str):
    return {"message": f"User {name} created with email {email}"}

@router.put("/preference")
def update_user_preference_by_mobile(
    request: PreferenceUpdateRequest, # ✅ Must use this new schema
    db: Session = Depends(get_db)
):
    # Find the user by their mobile number
    db_user = db.query(DBUser).filter(DBUser.mobile_number == request.mobile_number).first()
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Update the preference column with the new data
    db_user.preference = request.preference
    db.commit()
    db.refresh(db_user)
    return db_user