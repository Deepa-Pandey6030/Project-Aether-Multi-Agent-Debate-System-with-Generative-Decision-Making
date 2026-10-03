"""
Debate store — all MongoDB operations for debates and events.
Replaces both the in-memory active_debates dict and conversation_store.py
"""

from datetime import datetime
from typing import Optional
import json

from app.core.database import debates_col, events_col, usage_logs_col
from app.models.debate import DebateState, AgentRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialise(state: DebateState) -> dict:
    """Convert DebateState to a plain dict safe for MongoDB."""
    return json.loads(state.model_dump_json())


# ---------------------------------------------------------------------------
# Debate CRUD
# ---------------------------------------------------------------------------

async def save_debate(state: DebateState, user_id: str) -> None:
    """Insert a new debate document."""
    doc = _serialise(state)
    doc["user_id"] = user_id
    doc["is_deleted"] = False
    doc["deleted_at"] = None
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    await debates_col().insert_one(doc)


async def update_debate(state: DebateState) -> None:
    """Overwrite the full debate document with current state."""
    doc = _serialise(state)
    doc["updated_at"] = datetime.utcnow()
    await debates_col().update_one(
        {"debate_id": state.debate_id},
        {"$set": doc}
    )


async def get_debate(debate_id: str) -> Optional[dict]:
    doc = await debates_col().find_one(
        {"debate_id": debate_id, "is_deleted": False},
        {"_id": 0}
    )
    return doc


async def get_debate_by_user(debate_id: str, user_id: str) -> Optional[dict]:
    doc = await debates_col().find_one(
        {"debate_id": debate_id, "user_id": user_id, "is_deleted": False},
        {"_id": 0}
    )
    return doc


async def list_debates_for_user(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
) -> list[dict]:
    cursor = debates_col().find(
        {"user_id": user_id, "is_deleted": False},
        {
            "_id": 0,
            "debate_id": 1,
            "topic": 1,
            "status": 1,
            "phase": 1,
            "current_round_number": 1,
            "time_budget": 1,
            "time_elapsed": 1,
            "created_at": 1,
            "report.debate_quality": 1,
            "report.confidence_score": 1,
            "report.verdict": 1,
        }
    ).sort("created_at", -1).skip(skip).limit(limit)
    return await cursor.to_list(length=limit)


async def soft_delete_debate(debate_id: str, user_id: str) -> bool:
    result = await debates_col().update_one(
        {"debate_id": debate_id, "user_id": user_id, "is_deleted": False},
        {"$set": {"is_deleted": True, "deleted_at": datetime.utcnow()}}
    )
    return result.modified_count == 1


async def get_latest_event(debate_id: str) -> Optional[dict]:
    """Get the most recent event — used by status polling endpoint."""
    cursor = events_col().find(
        {"debate_id": debate_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(1)
    docs = await cursor.to_list(length=1)
    return docs[0] if docs else None
# ---------------------------------------------------------------------------
# Events (replaces conversation_store append_event)
# ---------------------------------------------------------------------------

async def append_event(
    debate_id: str,
    user_id: str,
    agent: AgentRole,
    event_type: str,
    content: dict,
    meta: Optional[dict] = None,
) -> None:
    """Append a single debate event to the events collection."""
    # Skip raw LLM IO
    if event_type.endswith(".prompt") or event_type.endswith(".response"):
        return

    doc = {
        "debate_id": debate_id,
        "user_id": user_id,
        "agent": agent.value,
        "event_type": event_type,
        "meta": meta or {},
        "content": content,
        "timestamp": datetime.utcnow(),
    }
    await events_col().insert_one(doc)


async def get_events_for_debate(debate_id: str) -> list[dict]:
    cursor = events_col().find(
        {"debate_id": debate_id},
        {"_id": 0}
    ).sort("timestamp", 1)
    return await cursor.to_list(length=None)


# ---------------------------------------------------------------------------
# Usage logs
# ---------------------------------------------------------------------------

async def log_usage(
    user_id: str,
    debate_id: str,
    action: str,
    model_used: str = "",
) -> None:
    doc = {
        "user_id": user_id,
        "debate_id": debate_id,
        "action": action,
        "model_used": model_used,
        "timestamp": datetime.utcnow(),
    }
    await usage_logs_col().insert_one(doc)