"""
User and Session store — all MongoDB operations for auth
"""

import uuid
from datetime import datetime
from typing import Optional

from app.core.database import users_col, sessions_col
from app.core.security import hash_password, create_refresh_token
from app.models.user import UserInDB, SessionInDB, UserPublic


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

async def create_user(email: str, username: str, plain_password: str) -> UserInDB:
    user = UserInDB(
        user_id=str(uuid.uuid4()),
        email=email.lower().strip(),
        username=username.strip(),
        hashed_password=hash_password(plain_password),
    )
    await users_col().insert_one(user.model_dump())
    return user


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    doc = await users_col().find_one({"email": email.lower().strip()})
    if doc:
        doc.pop("_id", None)
        return UserInDB(**doc)
    return None


async def get_user_by_username(username: str) -> Optional[UserInDB]:
    doc = await users_col().find_one({"username": username.strip()})
    if doc:
        doc.pop("_id", None)
        return UserInDB(**doc)
    return None


async def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    doc = await users_col().find_one({"user_id": user_id})
    if doc:
        doc.pop("_id", None)
        return UserInDB(**doc)
    return None


async def update_last_login(user_id: str) -> None:
    await users_col().update_one(
        {"user_id": user_id},
        {"$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()}}
    )


async def increment_debate_count(user_id: str) -> None:
    await users_col().update_one(
        {"user_id": user_id},
        {"$inc": {"debates_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
    )


def to_public(user: UserInDB) -> UserPublic:
    return UserPublic(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        plan=user.plan,
        debates_count=user.debates_count,
        created_at=user.created_at,
    )


# ---------------------------------------------------------------------------
# Sessions (refresh tokens)
# ---------------------------------------------------------------------------

async def create_session(
    user_id: str,
    device_info: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> tuple[str, SessionInDB]:
    """Create a new session, return (raw_refresh_token, session)"""
    raw_token, expires_at = create_refresh_token(user_id)
    session = SessionInDB(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        refresh_token=raw_token,
        device_info=device_info,
        ip_address=ip_address,
        expires_at=expires_at,
    )
    await sessions_col().insert_one(session.model_dump())
    return raw_token, session


async def get_session_by_token(token: str) -> Optional[SessionInDB]:
    doc = await sessions_col().find_one({"refresh_token": token, "is_revoked": False})
    if doc:
        doc.pop("_id", None)
        return SessionInDB(**doc)
    return None


async def revoke_session(token: str) -> None:
    await sessions_col().update_one(
        {"refresh_token": token},
        {"$set": {"is_revoked": True}}
    )


async def revoke_all_user_sessions(user_id: str) -> None:
    """Revoke all sessions for a user — useful for logout-all-devices"""
    await sessions_col().update_many(
        {"user_id": user_id},
        {"$set": {"is_revoked": True}}
    )