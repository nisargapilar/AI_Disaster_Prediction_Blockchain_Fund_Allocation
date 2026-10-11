import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select

from db import async_session  # importing db also loads the .env file
from models import OperatorModel

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing from your .env file")

JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME_HOURS = 8

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


# ------------------------------------------------------------
# Password helpers
# ------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


# ------------------------------------------------------------
# Token helper
# ------------------------------------------------------------

def create_access_token(operator: OperatorModel) -> str:
    payload = {
        "sub": str(operator.operator_id),
        "username": operator.username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_LIFETIME_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# ------------------------------------------------------------
# Dependency: protects any route that includes it
# ------------------------------------------------------------

async def get_current_operator(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> OperatorModel:
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    async with async_session() as session:
        result = await session.execute(
            select(OperatorModel).where(
                OperatorModel.operator_id == uuid.UUID(payload["sub"])
            )
        )
        operator = result.scalar_one_or_none()

    if operator is None or not operator.is_active:
        raise HTTPException(status_code=401, detail="Operator not found or disabled")

    return operator


# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(payload: LoginRequest):
    async with async_session() as session:
        result = await session.execute(
            select(OperatorModel).where(OperatorModel.username == payload.username)
        )
        operator = result.scalar_one_or_none()

    if (
        operator is None
        or not operator.is_active
        or not check_password(payload.password, operator.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "access_token": create_access_token(operator),
        "token_type": "bearer",
        "username": operator.username,
    }


@router.get("/me")
async def me(operator: OperatorModel = Depends(get_current_operator)):
    return {"username": operator.username}