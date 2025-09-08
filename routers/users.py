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

