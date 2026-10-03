"""
Conversation store for AETHER — writes a clean, readable Markdown transcript.
Only stores what agents actually said, not prompts or LLM internals.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings
from app.models.debate import DebateState, AgentRole


def _conversation_dir() -> Path:
    root = Path(__file__).resolve().parents[2]
    folder = getattr(settings, "CONVERSATION_DIR", "conversation")
    d = root / folder
    d.mkdir(parents=True, exist_ok=True)
    return d


def _conversation_path(debate_id: str) -> Path:
    return _conversation_dir() / f"{debate_id}.md"


def _now() -> str:
    return datetime.utcnow().strftime("%H:%M:%S")


def _append(debate_id: str, text: str) -> None:
    """Append a line to the markdown file (no tmp files, no rename — Windows safe)."""
    if not getattr(settings, "SAVE_CONVERSATIONS", False):
        return
    path = _conversation_path(debate_id)
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")


# ---------------------------------------------------------------------------
# Public API (same signatures as before so orchestrator needs no changes)
# ---------------------------------------------------------------------------

def init_conversation(state: DebateState, *, model: Optional[str] = None) -> None:
    if not getattr(settings, "SAVE_CONVERSATIONS", False):
        return
    path = _conversation_path(state.debate_id)
    # Clear/create file
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# AETHER Debate Transcript\n\n")
        f.write(f"**Topic:** {state.topic}\n\n")
        f.write(f"**Model:** {model or 'unknown'}\n\n")
        f.write(f"**Time Budget:** {state.time_budget}s\n\n")
        f.write(f"**Started:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
        f.write("---\n\n")


def append_event(
    debate_id: str,
    *,
    agent: AgentRole,
    event_type: str,
    content: Any,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    if not getattr(settings, "SAVE_CONVERSATIONS", False):
        return

    # Only handle the meaningful debate events — skip prompts/responses/LLM IO
    if event_type.endswith(".prompt") or event_type.endswith(".response"):
        return

    lines = []
    t = _now()

    # ── Factor Extraction ──────────────────────────────────────────────
    if event_type == "factor_extraction_result":
        lines.append("## 📋 Factors Extracted\n")
        for f in content.get("factors", []):
            lines.append(f"- **{f['name']}** (importance: {f['importance']})")
            lines.append(f"  {f['description']}")

    # ── Opening Statements ─────────────────────────────────────────────
    elif event_type == "pro_opening":
        lines.append("## 🟢 PRO — Opening Statement\n")
        lines.append(content.get("overall_position", ""))
        factor_positions = content.get("factor_positions", {})
        if factor_positions:
            lines.append("\n**Per Factor:**")
            for fid, pos in factor_positions.items():
                if pos:
                    lines.append(f"- {pos}")

    elif event_type == "con_opening":
        lines.append("## 🔴 CON — Opening Statement\n")
        lines.append(content.get("overall_position", ""))
        factor_positions = content.get("factor_positions", {})
        if factor_positions:
            lines.append("\n**Per Factor:**")
            for fid, pos in factor_positions.items():
                if pos:
                    lines.append(f"- {pos}")

    # ── Rebuttal Rounds ────────────────────────────────────────────────
    elif event_type == "pro_rebuttal":
        rnd = (meta or {}).get("round", "?")
        lines.append(f"### 🟢 PRO — Round {rnd} Rebuttal\n")
        lines.append(content.get("content", ""))
        if content.get("challenged_claims"):
            lines.append("\n**Challenged:**")
            for c in content["challenged_claims"]:
                lines.append(f"- {c}")
        if content.get("new_points"):
            lines.append("\n**New Points:**")
            for p in content["new_points"]:
                lines.append(f"- {p}")

    elif event_type == "con_rebuttal":
        rnd = (meta or {}).get("round", "?")
        lines.append(f"### 🔴 CON — Round {rnd} Rebuttal\n")
        lines.append(content.get("content", ""))
        if content.get("challenged_claims"):
            lines.append("\n**Challenged:**")
            for c in content["challenged_claims"]:
                lines.append(f"- {c}")
        if content.get("new_points"):
            lines.append("\n**New Points:**")
            for p in content["new_points"]:
                lines.append(f"- {p}")

    # ── Round Evaluation ───────────────────────────────────────────────
    elif event_type == "round_evaluation":
        rnd = (meta or {}).get("round", "?")
        cont = content.get("should_continue", False)
        icon = "🔄 Continue" if cont else "⏹ Stop"
        lines.append(f"### ⚖️ Round {rnd} Evaluation — {icon}\n")
        lines.append(f"> {content.get('reason', '')}")
        if content.get("unresolved_conflicts"):
            lines.append("\n**Unresolved:**")
            for c in content["unresolved_conflicts"]:
                lines.append(f"- {c}")

    # ── Cross Examination ──────────────────────────────────────────────
    elif event_type == "cross_exam_questions_pro":
        lines.append("## 🔍 Cross-Examination — Questions for PRO\n")
        for i, q in enumerate(content.get("questions", []), 1):
            lines.append(f"**Q{i}:** {q['question']}")
            if q.get("context"):
                lines.append(f"*{q['context']}*")
            lines.append("")

    elif event_type == "cross_exam_questions_con":
        lines.append("## 🔍 Cross-Examination — Questions for CON\n")
        for i, q in enumerate(content.get("questions", []), 1):
            lines.append(f"**Q{i}:** {q['question']}")
            if q.get("context"):
                lines.append(f"*{q['context']}*")
            lines.append("")

    elif event_type == "cross_exam_answers_pro":
        lines.append("## 🟢 PRO — Cross-Examination Answers\n")
        for i, a in enumerate(content.get("answers", []), 1):
            lines.append(f"**A{i}:** {a['answer']}")
            if a.get("concession"):
                lines.append(f"⚠️ **Concession:** {a['concession']}")
            lines.append("")

    elif event_type == "cross_exam_answers_con":
        lines.append("## 🔴 CON — Cross-Examination Answers\n")
        for i, a in enumerate(content.get("answers", []), 1):
            lines.append(f"**A{i}:** {a['answer']}")
            if a.get("concession"):
                lines.append(f"⚠️ **Concession:** {a['concession']}")
            lines.append("")

    # ── Closing Statements ─────────────────────────────────────────────
    elif event_type == "pro_closing":
        lines.append("## 🟢 PRO — Closing Statement\n")
        lines.append(content.get("final_position", ""))
        if content.get("strongest_arguments"):
            lines.append("\n**Strongest Arguments:**")
            for a in content["strongest_arguments"]:
                lines.append(f"- {a}")
        if content.get("conceded_points"):
            lines.append("\n**Conceded:**")
            for c in content["conceded_points"]:
                lines.append(f"- {c}")

    elif event_type == "con_closing":
        lines.append("## 🔴 CON — Closing Statement\n")
        lines.append(content.get("final_position", ""))
        if content.get("strongest_arguments"):
            lines.append("\n**Strongest Arguments:**")
            for a in content["strongest_arguments"]:
                lines.append(f"- {a}")
        if content.get("conceded_points"):
            lines.append("\n**Conceded:**")
            for c in content["conceded_points"]:
                lines.append(f"- {c}")

    # ── Final Report ───────────────────────────────────────────────────
    elif event_type == "synthesis_report":
        lines.append("---\n")
        lines.append("# 📊 Debate Report\n")
        lines.append(f"**Debate Quality:** {content.get('debate_quality', 'N/A')}\n")
        lines.append(f"**Confidence Score:** {content.get('confidence_score', 0.5):.0%}\n")
        lines.append(f"**Verdict:** {content.get('verdict') or 'No clear verdict'}\n")

        if content.get("what_worked"):
            lines.append("\n### ✅ What Worked")
            for w in content["what_worked"]:
                lines.append(f"- {w}")

        if content.get("what_failed"):
            lines.append("\n### ❌ What Failed")
            for w in content["what_failed"]:
                lines.append(f"- {w}")

        if content.get("why_it_happened"):
            lines.append(f"\n### 🔎 Why It Happened\n{content['why_it_happened']}")

        if content.get("how_to_improve"):
            lines.append("\n### 💡 How To Improve")
            for h in content["how_to_improve"]:
                lines.append(f"- {h}")

    elif event_type == "final_state":
        lines.append("\n---\n")
        lines.append(f"**Rounds Completed:** {content.get('rounds_completed', 0)}")
        lines.append(f"**Factors Debated:** {content.get('factors_debated', 0)}")
        if content.get("unresolved_conflicts"):
            lines.append("\n**Unresolved Conflicts:**")
            for c in content["unresolved_conflicts"]:
                lines.append(f"- {c}")

    elif event_type == "error":
        lines.append(f"\n> ⚠️ **Error:** {content.get('error', 'Unknown error')}\n")

    elif event_type == "debate_started":
        return  # already written in init_conversation

    else:
        return  # silently skip anything unrecognised

    # Write all lines
    if lines:
        _append(debate_id, "\n".join(lines) + "\n")


def finalize_conversation(state: DebateState) -> None:
    """Write the final summary footer."""
    if not getattr(settings, "SAVE_CONVERSATIONS", False):
        return

    lines = [
        "\n---\n",
        f"*Debate ended at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*",
        f"*Debate ID: {state.debate_id}*",
    ]
    _append(state.debate_id, "\n".join(lines))
    
    
    
    
# ```

# ---

# The output is now a clean `.md` file that looks like this when you open it:
# ```
# # AETHER Debate Transcript

# **Topic:** Is social media responsible for mental health issues
# **Model:** llama-3.1-8b-instant

# ---

# ## 📋 Factors Extracted
# - **Correlation vs. Causation** (importance: 0.9)
#   Whether social media use is correlated...

# ## 🟢 PRO — Opening Statement
# I firmly believe that social media is...

# ## 🔴 CON — Opening Statement
# As Con Agent, I firmly stand in opposition...

# ### 🟢 PRO — Round 1 Rebuttal
# Con's argument relies heavily on...

# ### ⚖️ Round 1 Evaluation — 🔄 Continue
# > Both sides introduced new arguments...

# ## 📊 Debate Report
# **Debate Quality:** High
# **Confidence Score:** 62%
# **Verdict:** Pro made the stronger case...