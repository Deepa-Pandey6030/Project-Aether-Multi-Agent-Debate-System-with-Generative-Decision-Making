"""
Synthesizer Agent
Produces the full DebateReport.

Primary LLM: Gemini (neutral, large context window — ideal for synthesis)
Fallback LLM: Groq (if Gemini is unavailable or fails)
"""

from typing import Dict, Any
import json
from app.agents.base import BaseAgent
from app.models.debate import (
    DebateState, AgentRole, DebateReport, ArgumentAssessment, ConcessionPoint
)


class SynthesizerAgent(BaseAgent):

    def __init__(self):
        super().__init__(AgentRole.SYNTHESIZER)

    async def execute(self, state: DebateState, **kwargs) -> Dict[str, Any]:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(state)

        # Use Gemini as primary — large context, neutral tone, no token truncation issues.
        # Groq is the automatic fallback inside _call_gemini_synthesis.
        response = await self._call_gemini_synthesis(
            system_prompt,
            user_prompt,
            debate_id=state.debate_id,
        )

        report = self._parse_report(response, state)
        return {"decision": report, "report": report, "raw_response": response}

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    def _build_system_prompt(self) -> str:
        return """You are the Synthesizer Agent in Project AETHER.

Your role: Read the COMPLETE debate and produce a thorough, neutral debate report in JSON.

Critical rules:
- Do NOT introduce new arguments
- Base your assessment ONLY on what was debated
- Be neutral — assess argument QUALITY, not which side you prefer
- Confidence score: 0.5 = perfectly balanced, >0.5 = Pro made stronger case, <0.5 = Con made stronger case
- Only provide a verdict if the topic clearly has a decidable outcome
- Keep each list item to one sentence maximum
- Output ONLY valid JSON — no markdown fences, no preamble, no explanation outside the JSON

Output format (JSON):
{
  "pro_strongest_arguments": ["Argument 1", "Argument 2"],
  "con_strongest_arguments": ["Argument 1", "Argument 2"],
  "arguments_that_held_up": [
    {"argument_summary": "...", "held_up": true, "reason": "Why it survived scrutiny"}
  ],
  "arguments_that_collapsed": [
    {"argument_summary": "...", "held_up": false, "reason": "Why it failed under scrutiny"}
  ],
  "concession_points": [
    {"agent_role": "pro", "conceded_point": "...", "context": "..."}
  ],
  "debate_quality": "High/Medium/Low",
  "debate_quality_reason": "One sentence explanation",
  "confidence_score": 0.0,
  "confidence_reason": "One sentence explaining the score",
  "verdict": "One sentence verdict or null if not decidable",
  "what_worked": ["One sentence per item"],
  "what_failed": ["One sentence per item"],
  "why_it_happened": "One sentence root cause",
  "how_to_improve": ["One sentence per recommendation"]
}"""

    def _build_user_prompt(self, state: DebateState) -> str:
        prompt = f"Topic: {state.topic}\n"
        prompt += f"Time Budget: {state.time_budget}s | Time Used: {state.time_elapsed}s\n\n"

        prompt += "FACTORS DEBATED:\n"
        for f in state.factors:
            prompt += f"  - {f.name} (importance: {f.importance}): {f.description}\n"

        prompt += "\nOPENING STATEMENTS:\n"
        if state.pro_opening:
            prompt += f"PRO: {state.pro_opening.overall_position[:500]}\n"
        if state.con_opening:
            prompt += f"CON: {state.con_opening.overall_position[:500]}\n"

        if state.debate_rounds:
            prompt += f"\nREBUTTAL ROUNDS ({len(state.debate_rounds)} rounds):\n"
            for dr in state.debate_rounds:
                prompt += f"\n--- Round {dr.round_number} ---\n"
                for r in dr.pro_rebuttals:
                    factor = next((f for f in state.factors if f.id == r.factor_id), None)
                    fname = factor.name if factor else r.factor_id
                    # Prefer summary_fact (Gemini-generated 1-sentence summary) over full content
                    summary = r.summary_fact or r.content[:200]
                    prompt += f"PRO on {fname}: {summary}\n"
                    if r.new_points:
                        prompt += f"  New points: {'; '.join(r.new_points[:2])}\n"
                for r in dr.con_rebuttals:
                    factor = next((f for f in state.factors if f.id == r.factor_id), None)
                    fname = factor.name if factor else r.factor_id
                    summary = r.summary_fact or r.content[:200]
                    prompt += f"CON on {fname}: {summary}\n"
                    if r.new_points:
                        prompt += f"  New points: {'; '.join(r.new_points[:2])}\n"
                if dr.evaluation_reason:
                    prompt += f"  Round evaluation: {dr.evaluation_reason}\n"

        if state.cross_exam_questions:
            prompt += "\nCROSS-EXAMINATION:\n"
            answers_map = {a.question_id: a for a in state.cross_exam_answers}
            for q in state.cross_exam_questions:
                prompt += f"Q (to {q.target_agent.value.upper()}): {q.question}\n"
                a = answers_map.get(q.id)
                if a:
                    prompt += f"A ({a.agent_role.value.upper()}): {a.answer[:200]}\n"
                    if a.concession:
                        prompt += f"  [CONCESSION]: {a.concession}\n"

        if state.pro_closing:
            prompt += f"\nPRO CLOSING: {state.pro_closing.final_position[:300]}\n"
            if state.pro_closing.conceded_points:
                prompt += f"Pro conceded: {', '.join(state.pro_closing.conceded_points)}\n"
        if state.con_closing:
            prompt += f"\nCON CLOSING: {state.con_closing.final_position[:300]}\n"
            if state.con_closing.conceded_points:
                prompt += f"Con conceded: {', '.join(state.con_closing.conceded_points)}\n"

        if state.unresolved_conflicts:
            prompt += f"\nUNRESOLVED CONFLICTS: {', '.join(state.unresolved_conflicts)}\n"

        prompt += "\nProduce the complete debate report as valid JSON only."
        return prompt

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse_report(self, response: str, state: DebateState) -> DebateReport:
        try:
            # Strip markdown fences if model wrapped the JSON anyway
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()

            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1

            if start != -1 and end > start:
                data = json.loads(cleaned[start:end])

                held_up = [ArgumentAssessment(**a) for a in data.get("arguments_that_held_up", [])]
                collapsed = [ArgumentAssessment(**a) for a in data.get("arguments_that_collapsed", [])]

                concessions = []
                for c in data.get("concession_points", []):
                    try:
                        concessions.append(ConcessionPoint(
                            agent_role=AgentRole(c.get("agent_role", "pro")),
                            conceded_point=c.get("conceded_point", ""),
                            context=c.get("context", ""),
                        ))
                    except Exception:
                        pass

                trace = [
                    {
                        "agent": a.agent.value,
                        "action": a.action_type,
                        "timestamp": a.timestamp.isoformat(),
                    }
                    for a in state.action_history
                ]

                return DebateReport(
                    pro_strongest_arguments=data.get("pro_strongest_arguments", []),
                    con_strongest_arguments=data.get("con_strongest_arguments", []),
                    arguments_that_held_up=held_up,
                    arguments_that_collapsed=collapsed,
                    concession_points=concessions,
                    debate_quality=data.get("debate_quality", "Medium"),
                    debate_quality_reason=data.get("debate_quality_reason", ""),
                    confidence_score=float(data.get("confidence_score", 0.5)),
                    confidence_reason=data.get("confidence_reason", ""),
                    verdict=data.get("verdict") or None,
                    what_worked=data.get("what_worked", []),
                    what_failed=data.get("what_failed", []),
                    why_it_happened=data.get("why_it_happened", ""),
                    how_to_improve=data.get("how_to_improve", []),
                    debate_trace=trace,
                )

        except Exception as e:
            print(f"Synthesizer parse error: {e}")
            print(f"Raw response preview: {response[:500]}")

        return DebateReport(
            debate_quality="Low",
            debate_quality_reason="Synthesis parsing failed.",
            confidence_score=0.5,
            confidence_reason="Unable to assess — parsing error.",
            what_failed=["Synthesis encountered a parsing error"],
        )