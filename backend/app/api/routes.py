"""
API Routes for AETHER Debate System
All endpoints require authentication.
"""

import uuid
import asyncio
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from app.models.debate import DebateRequest, DebateResponse, DebateState, DebatePhase
from app.models.user import UserInDB
from app.services.orchestrator import DebateOrchestrator
from app.services.debate_store import (
    get_debate_by_user, list_debates_for_user,
    soft_delete_debate, get_events_for_debate,
    get_latest_event, save_debate
)
from app.models.debate import DebateState, DebatePhase
from app.api.dependencies import get_current_user

debate_router = APIRouter()


# ---------------------------------------------------------------------------
# Background runner
# ---------------------------------------------------------------------------

async def _run_debate_background(
    debate_id: str,
    request: DebateRequest,
    user_id: str,
) -> None:
    try:
        orchestrator = DebateOrchestrator()
        await orchestrator.run_debate(request, user_id=user_id, debate_id=debate_id)
    except Exception as e:
        print(f"Background debate error ({debate_id}): {e}")


# ---------------------------------------------------------------------------
# Start debate — returns instantly, runs in background
# ---------------------------------------------------------------------------

@debate_router.post("/debate/start")
async def start_debate(
    request: DebateRequest,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_user),
):
    debate_id = str(uuid.uuid4())
    background_tasks.add_task(
        _run_debate_background,
        debate_id,
        request,
        current_user.user_id,
    )
    return {
        "debate_id": debate_id,
        "status": "in_progress",
        "topic": request.topic,
        "time_budget": request.time_budget,
        "message": "Debate started. Poll /debate/{id}/status for live updates.",
    }


# ---------------------------------------------------------------------------
# Status — lightweight polling endpoint for Live Theater
# ---------------------------------------------------------------------------

@debate_router.get("/debate/{debate_id}/status")
async def get_debate_status(
    debate_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    doc = await get_debate_by_user(debate_id, current_user.user_id)

    # Debate not saved yet (background task just started)
    if not doc:
        return {
            "debate_id": debate_id,
            "status": "in_progress",
            "phase": "initialization",
            "current_round_number": 0,
            "time_elapsed": 0,
            "time_budget": 0,
            "latest_event": None,
        }

    latest = await get_latest_event(debate_id)

    # Serialize latest event safely
    latest_event = None
    if latest:
        latest_event = {
            "agent": latest.get("agent"),
            "event_type": latest.get("event_type"),
            "content": latest.get("content", {}),
            "timestamp": latest["timestamp"].isoformat() if hasattr(latest.get("timestamp"), "isoformat") else str(latest.get("timestamp")),
        }

    phase = doc.get("phase", "initialization")
    status = "completed" if phase == "completed" else "in_progress"

    return {
        "debate_id": debate_id,
        "status": status,
        "phase": phase,
        "current_round_number": doc.get("current_round_number", 0),
        "time_elapsed": doc.get("time_elapsed", 0),
        "time_budget": doc.get("time_budget", 0),
        "time_remaining": doc.get("time_remaining", 0),
        "latest_event": latest_event,
    }


# ---------------------------------------------------------------------------
# Get full debate state
# ---------------------------------------------------------------------------

@debate_router.get("/debate/{debate_id}", response_model=DebateResponse)
async def get_debate(
    debate_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    doc = await get_debate_by_user(debate_id, current_user.user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Debate not found")

    state = DebateState(**doc)
    status = "completed" if state.phase.value == "completed" else "in_progress"
    return DebateResponse(
        debate_id=state.debate_id,
        status=status,
        current_phase=state.phase,
        state=state,
    )


# ---------------------------------------------------------------------------
# Get final report
# ---------------------------------------------------------------------------

@debate_router.get("/debate/{debate_id}/report")
async def get_report(
    debate_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    doc = await get_debate_by_user(debate_id, current_user.user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Debate not found")

    report = doc.get("report")
    if not report:
        raise HTTPException(status_code=400, detail="Debate not yet completed")

    return {
        "debate_id": debate_id,
        "topic": doc.get("topic"),
        "debate_quality": report.get("debate_quality"),
        "debate_quality_reason": report.get("debate_quality_reason"),
        "confidence_score": report.get("confidence_score"),
        "confidence_reason": report.get("confidence_reason"),
        "verdict": report.get("verdict"),
        "pro_strongest_arguments": report.get("pro_strongest_arguments", []),
        "con_strongest_arguments": report.get("con_strongest_arguments", []),
        "arguments_that_held_up": report.get("arguments_that_held_up", []),
        "arguments_that_collapsed": report.get("arguments_that_collapsed", []),
        "concession_points": report.get("concession_points", []),
        "what_worked": report.get("what_worked", []),
        "what_failed": report.get("what_failed", []),
        "why_it_happened": report.get("why_it_happened"),
        "how_to_improve": report.get("how_to_improve", []),
        "rounds_completed": doc.get("current_round_number", 0),
        "factors_debated": len(doc.get("factors", [])),
        "time_used": doc.get("time_elapsed", 0),
    }


# ---------------------------------------------------------------------------
# Get event trace
# ---------------------------------------------------------------------------

@debate_router.get("/debate/{debate_id}/trace")
async def get_trace(
    debate_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    doc = await get_debate_by_user(debate_id, current_user.user_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Debate not found")

    events = await get_events_for_debate(debate_id)
    trace = [
        {
            "timestamp": e["timestamp"].isoformat() if hasattr(e["timestamp"], "isoformat") else str(e["timestamp"]),
            "agent": e["agent"],
            "event_type": e["event_type"],
            "content": e["content"],
        }
        for e in events
    ]
    return {"debate_id": debate_id, "topic": doc.get("topic"), "trace": trace}


# ---------------------------------------------------------------------------
# Soft delete
# ---------------------------------------------------------------------------

@debate_router.delete("/debate/{debate_id}")
async def delete_debate(
    debate_id: str,
    current_user: UserInDB = Depends(get_current_user),
):
    deleted = await soft_delete_debate(debate_id, current_user.user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Debate not found")
    return {"status": "deleted", "debate_id": debate_id}


# ---------------------------------------------------------------------------
# List all debates for current user
# ---------------------------------------------------------------------------

@debate_router.get("/debates")
async def list_my_debates(
    skip: int = 0,
    limit: int = 20,
    current_user: UserInDB = Depends(get_current_user),
):
    debates = await list_debates_for_user(current_user.user_id, skip=skip, limit=limit)
    return {"debates": debates, "count": len(debates), "skip": skip, "limit": limit}