from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User
# import jwt
from typing import Optional

# Security scheme for JWT tokens
security = HTTPBearer()

# Secret key for JWT - In production, use environment variables
SECRET_KEY = "your-secret-key-here"  # Change this to a secure random key
ALGORITHM = "HS256"

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token
    """
    try:
        # Extract token from credentials
        token = credentials.credentials

        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to get the current active user (if you have user status tracking)
    """
    if not getattr(current_user, 'is_active', True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Optional: Simple version without JWT (for development/testing)
def get_current_user_simple(db: Session = Depends(get_db)) -> User:
    """
    Simplified version that returns the first user (for development only)
    Remove this in production!
    """
    user = db.query(User).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found"
        )
    return user
