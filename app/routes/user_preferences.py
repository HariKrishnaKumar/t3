from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User as DBUser
from models.user_schema import PreferenceUpdateRequest

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.put("/preference")
def update_user_preference_by_id(
    request: PreferenceUpdateRequest,
    db: Session = Depends(get_db)
):
    db_user = db.query(DBUser).filter(DBUser.id == request.id).first()
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Define all possible preferences
    all_preferences = ["pickup", "delivery", "reservation", "catering", "events"]

    # Set the selected preference to True
    if request.preference not in all_preferences:
        raise HTTPException(
            status_code=400,
            detail="Invalid preference option"
        )

    db_user.preference = request.preference
    db.commit()
    db.refresh(db_user)
    return db_user