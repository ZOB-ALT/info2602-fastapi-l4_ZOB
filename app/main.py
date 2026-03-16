from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import select
from .database import create_db_and_tables, get_session, SessionDep
from .models import RegularUser, UserResponse, Token
from .auth import encrypt_password, verify_password, create_access_token, oauth2_scheme, get_current_user, AuthDep
from datetime import timedelta
from typing import List

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"message": "Welcome to Lab 4 - REST Authentication"}

@app.post("/register", response_model=UserResponse)
def register(username: str, email: str, password: str, db: SessionDep):
    existing = db.exec(select(RegularUser).where(
        (RegularUser.username == username) | (RegularUser.email == email)
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    user = RegularUser(
        username=username,
        email=email,
        password=encrypt_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/token", response_model=Token)
def login(username: str, password: str, db: SessionDep):
    user = db.exec(select(RegularUser).where(RegularUser.username == username)).first()
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(minutes=30)
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: AuthDep):
    return current_user

@app.get("/users", response_model=List[UserResponse])
def list_users(db: SessionDep):
    users = db.exec(select(RegularUser)).all()
    return users