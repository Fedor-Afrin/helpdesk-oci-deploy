from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login", response_model=schemas.UserResponse)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, login_data.username)
    if not user or not crud.verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return user

@router.post("/users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)
