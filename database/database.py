# database/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Generator


DATABASE_URL = "mysql+mysqlconnector://root:dev2003@localhost:3306/bitewise_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    This is what should be used with Depends(get_db) in your routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
