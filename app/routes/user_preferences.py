from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User as DBUser
from models.user_schema import UserUpdate, UserOut
from dependencies import get_current_user
from models.user_schema import PreferenceUpdateRequest

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.put("/preference")
def update_user_preference_by_mobile(
    request: PreferenceUpdateRequest,
    db: Session = Depends(get_db)
):
    db_user = db.query(DBUser).filter(DBUser.mobile_number == request.mobile_number).first()
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    db_user.preference = request.preference
    db.commit()
    db.refresh(db_user)
    return db_user