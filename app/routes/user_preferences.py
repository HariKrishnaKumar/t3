from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User as DBUser
from models.user_schema import UserUpdate, UserOut
from dependencies import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

@router.put("/{user_id}/preference", response_model=UserOut)
def update_user_preference(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's preference"
        )

    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update the preference column with the new data
    if user_update.preference is not None:
        db_user.preference = user_update.preference

    db.commit()
    db.refresh(db_user)
    return db_user