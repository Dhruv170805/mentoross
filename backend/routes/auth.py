"""MentorOS – Auth Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user_id, decode_token,
)
from models.all_models import User, utcnow
import structlog

log = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(req: RegisterRequest):
    existing = await User.find_one({"email": req.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = User(
        email=req.email,
        name=req.name,
        hashed_password=hash_password(req.password),
        last_active=utcnow(),
    )
    await user.insert()

    uid = str(user.id)
    access  = create_access_token({"sub": uid})
    refresh = create_refresh_token(uid)
    log.info("user.registered", email=user.email, user_id=uid)
    return TokenResponse(
        access_token=access, refresh_token=refresh,
        user={"id": uid, "email": user.email, "name": user.name,
              "plan": user.plan, "streak_days": user.streak_days},
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    user = await User.find_one({"email": req.email})
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    today = datetime.now(timezone.utc).date().isoformat()
    last  = user.last_active.date().isoformat() if user.last_active else ""
    if last != today:
        yesterday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        user.streak_days = user.streak_days + 1 if last == yesterday else 1
    user.last_active = utcnow()
    await user.save()

    uid = str(user.id)
    access  = create_access_token({"sub": uid})
    refresh = create_refresh_token(uid)
    log.info("user.login", email=user.email, user_id=uid)
    return TokenResponse(
        access_token=access, refresh_token=refresh,
        user={"id": uid, "email": user.email, "name": user.name, "plan": user.plan,
              "streak_days": user.streak_days, "learning_goal": user.learning_goal},
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    from beanie import PydanticObjectId
    user = await User.get(PydanticObjectId(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    uid = str(user.id)
    access  = create_access_token({"sub": uid})
    refresh = create_refresh_token(uid)
    return TokenResponse(
        access_token=access, refresh_token=refresh,
        user={"id": uid, "email": user.email, "name": user.name,
              "plan": user.plan, "streak_days": user.streak_days},
    )


@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    from beanie import PydanticObjectId
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": str(user.id), "email": user.email, "name": user.name,
            "plan": user.plan, "streak_days": user.streak_days,
            "learning_goal": user.learning_goal, "created_at": user.created_at}


@router.patch("/me")
async def update_me(data: dict, user_id: str = Depends(get_current_user_id)):
    from beanie import PydanticObjectId
    user = await User.get(PydanticObjectId(user_id))
    if not user:
        raise HTTPException(status_code=404)
    for k, v in data.items():
        if k in {"name", "learning_goal", "avatar_url"}:
            setattr(user, k, v)
    user.updated_at = utcnow()
    await user.save()
    return {"message": "Profile updated"}
