from pwdlib import PasswordHash
from . import models
from .database import get_session, SessionDep
from sqlmodel import select
from datetime import timedelta, datetime, timezone
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from fastapi import Depends, HTTPException, status
import jwt
from jwt.exceptions import InvalidTokenError

SECRET_KEY = "ThisIsAnExampleOfWhatNotToUseAsTheSecretKeyIRL"
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def encrypt_password(password: str):
    return password_hash.hash(password)

def verify_password(plaintext_password: str, encrypted_password):
    return password_hash.verify(password=plaintext_password, hash=encrypted_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub", None)
        user_role = payload.get("role", None)
        if user_id is None or user_role is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = None
    if user_role == "admin":
        user = db.get(models.Admin, user_id)
    else:
        user = db.get(models.RegularUser, user_id)
    if user is None:
        raise credentials_exception
    return user

AuthDep = Annotated[models.User, Depends(get_current_user)]