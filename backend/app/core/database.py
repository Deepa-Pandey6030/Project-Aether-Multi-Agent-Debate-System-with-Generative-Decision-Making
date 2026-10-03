"""
MongoDB async client for AETHER using Motor.
Call connect_db() on startup and close_db() on shutdown.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db() -> None:
    global _client, _db
    _client = AsyncIOMotorClient(settings.MONGODB_URI)
    _db = _client[settings.MONGODB_DB_NAME]

    # Create indexes on first connect
    await _ensure_indexes()
    print(f"✅ MongoDB connected → {settings.MONGODB_DB_NAME}")


async def close_db() -> None:
    global _client
    if _client:
        _client.close()
        print("🛑 MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised. Call connect_db() first.")
    return _db


# Convenience accessors for each collection
def users_col():
    return get_db()["users"]

def sessions_col():
    return get_db()["sessions"]

def debates_col():
    return get_db()["debates"]

def events_col():
    return get_db()["events"]

def usage_logs_col():
    return get_db()["usage_logs"]


# ---------------------------------------------------------------------------
# Index creation
# ---------------------------------------------------------------------------

async def _ensure_indexes() -> None:
    db = get_db()

    # users
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("user_id", unique=True)
    await db["users"].create_index("username", unique=True)

    # sessions — TTL index auto-deletes expired sessions
    await db["sessions"].create_index("user_id")
    await db["sessions"].create_index("expires_at", expireAfterSeconds=0)

    # debates
    await db["debates"].create_index("debate_id", unique=True)
    await db["debates"].create_index([("user_id", 1), ("created_at", -1)])
    await db["debates"].create_index([("is_deleted", 1), ("user_id", 1)])

    # events
    await db["events"].create_index("debate_id")
    await db["events"].create_index([("debate_id", 1), ("timestamp", 1)])

    # usage_logs
    await db["usage_logs"].create_index([("user_id", 1), ("timestamp", -1)])

    print("✅ MongoDB indexes ensured")