"""
Pro Agent
- Delivers opening statement covering all factors
- Delivers rebuttals directly responding to Con's arguments
- Delivers closing statement
"""

from typing import Dict, Any
import json
import uuid
from app.agents.base import BaseAgent
from app.models.debate import (
    DebateState, AgentRole, OpeningStatement,
    RebuttalArgument, ClosingStatement, Factor
)


class ProAgent(BaseAgent):

    def __init__(self):
        super().__init__(AgentRole.PRO)

    # ------------------------------------------------------------------
    # Opening Statement
    # ------------------------------------------------------------------

    async def execute_opening(self, state: DebateState) -> Dict[str, Any]:
        system_prompt = self._opening_system_prompt()
        user_prompt = self._opening_user_prompt(state)
        response = await self._call_llm(
            system_prompt, user_prompt, max_tokens=2000,
            debate_id=state.debate_id, event_prefix="pro_opening"
        )
        opening = self._parse_opening(response, state)
        return {"opening": opening, "raw_response": response}

    def _opening_system_prompt(self) -> str:
        return """You are the Pro Agent in a formal debate (Project AETHER).

This is your OPENING STATEMENT — your first chance to lay out your complete position.

Rules:
- Address EVERY factor provided
- State your position on each factor clearly and confidently
- Do NOT respond to the opponent yet (they haven't spoken)
- Make strong, direct claims — no hedging
- Expose your key assumptions honestly

Output format (JSON):
{
  "overall_position": "Your 2-3 sentence overall stance on the topic",
  "factor_positions": {
    "<factor_id>": "Your position on this specific factor in 2-3 sentences"
  },
  "key_assumptions": ["assumption 1", "assumption 2"]
}"""

    def _opening_user_prompt(self, state: DebateState) -> str:
        prompt = f"Topic: {state.topic}\n\n"
        prompt += "Factors to address in your opening statement:\n"
        for f in state.factors:
            prompt += f"\nFactor ID: {f.id}\n"
            prompt += f"Name: {f.name}\n"
            prompt += f"Description: {f.description}\n"
            prompt += f"Importance: {f.importance}\n"
        prompt += "\nDeliver your opening statement arguing IN FAVOUR of the topic."
        return prompt

    def _parse_opening(self, response: str, state: DebateState) -> OpeningStatement:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(response[start:end])
                return OpeningStatement(
                    id=str(uuid.uuid4()),
                    agent_role=self.role,
                    stance="pro",
                    overall_position=data.get("overall_position", ""),
                    factor_positions=data.get("factor_positions", {}),
                )
        except Exception as e:
            print(f"Pro opening parse error: {e}")
        return OpeningStatement(
            id=str(uuid.uuid4()),
            agent_role=self.role,
            stance="pro",
            overall_position=response[:500],
            factor_positions={f.id: "" for f in state.factors},
        )

    # ------------------------------------------------------------------
    # Rebuttal
    # ------------------------------------------------------------------

    async def execute_rebuttal(
        self, state: DebateState, factor: Factor, round_number: int
    ) -> Dict[str, Any]:
        system_prompt = self._rebuttal_system_prompt(round_number)
        user_prompt = self._rebuttal_user_prompt(state, factor, round_number)
        response = await self._call_llm(
            system_prompt, user_prompt, max_tokens=1500,
            debate_id=state.debate_id, event_prefix="pro_rebuttal",
            meta={"round": round_number, "factor_id": factor.id}
        )
        rebuttal = self._parse_rebuttal(response, factor.id, round_number)
        return {"rebuttal": rebuttal, "raw_response": response}

    def _rebuttal_system_prompt(self, round_number: int) -> str:
        return f"""You are the Pro Agent in a formal debate (Project AETHER).

This is REBUTTAL ROUND {round_number} — you are directly responding to Con's arguments.

Rules:
- Directly challenge Con's specific claims (quote or reference them)
- Defend your original position with new evidence or reasoning
- Introduce new supporting points if relevant
- Do NOT repeat arguments you've already made without adding new value
- Be direct and aggressive in challenging weak arguments

Output format (JSON):
{{
  "content": "Your full rebuttal in 3-4 sentences",
  "summary_fact": "1 sentence core claim of this rebuttal",
  "challenged_claims": ["Specific claim from Con that you are challenging", ...],
  "new_points": ["New point you are introducing", ...]
}}"""

    def _rebuttal_user_prompt(self, state: DebateState, factor: Factor, round_number: int) -> str:
        prompt = f"Topic: {state.topic}\n"
        prompt += f"Factor: {factor.name} — {factor.description}\n\n"

        if state.pro_opening and factor.id in state.pro_opening.factor_positions:
            prompt += f"YOUR OPENING POSITION:\n{state.pro_opening.factor_positions[factor.id]}\n\n"

        if state.con_opening and factor.id in state.con_opening.factor_positions:
            prompt += f"CON'S OPENING POSITION:\n{state.con_opening.factor_positions[factor.id]}\n\n"

        for dr in state.debate_rounds:
            if dr.round_number < round_number:
                pro_r = [r for r in dr.pro_rebuttals if r.factor_id == factor.id]
                con_r = [r for r in dr.con_rebuttals if r.factor_id == factor.id]
                if pro_r or con_r:
                    prompt += f"--- Round {dr.round_number} ---\n"
                    for r in pro_r:
                        prompt += f"YOUR round {dr.round_number} rebuttal: {r.content}\n"
                    for r in con_r:
                        prompt += f"CON's round {dr.round_number} rebuttal: {r.content}\n"
                    prompt += "\n"

        if state.debate_rounds:
            latest = state.debate_rounds[-1]
            con_latest = [r for r in latest.con_rebuttals if r.factor_id == factor.id]
            if con_latest:
                prompt += f"CON'S LATEST REBUTTAL (respond to this):\n{con_latest[0].content}\n\n"

        prompt += f"Deliver your Round {round_number} rebuttal for this factor."
        return prompt

    def _parse_rebuttal(self, response: str, factor_id: str, round_number: int) -> RebuttalArgument:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(response[start:end])
                return RebuttalArgument(
                    id=str(uuid.uuid4()),
                    round_number=round_number,
                    agent_role=self.role,
                    stance="pro",
                    factor_id=factor_id,
                    content=data.get("content", ""),
                    summary_fact=data.get("summary_fact", ""),
                    challenged_claims=data.get("challenged_claims", []),
                    new_points=data.get("new_points", []),
                )
        except Exception as e:
            print(f"Pro rebuttal parse error: {e}")
        return RebuttalArgument(
            id=str(uuid.uuid4()),
            round_number=round_number,
            agent_role=self.role,
            stance="pro",
            factor_id=factor_id,
            content=response[:500],
        )

    # ------------------------------------------------------------------
    # Closing Statement
    # ------------------------------------------------------------------

    async def execute_closing(self, state: DebateState) -> Dict[str, Any]:
        system_prompt = self._closing_system_prompt()
        user_prompt = self._closing_user_prompt(state)
        response = await self._call_llm(
            system_prompt, user_prompt, max_tokens=1500,
            debate_id=state.debate_id, event_prefix="pro_closing"
        )
        closing = self._parse_closing(response)
        return {"closing": closing, "raw_response": response}

    def _closing_system_prompt(self) -> str:
        return """You are the Pro Agent delivering your CLOSING STATEMENT in Project AETHER.

Rules:
- Summarise your strongest arguments that survived the debate
- Acknowledge any valid points from Con (shows intellectual honesty)
- Reinforce your overall position powerfully
- Keep it concise and impactful

Output format (JSON):
{
  "final_position": "Your 2-3 sentence closing stance",
  "strongest_arguments": ["Argument 1 that held up", "Argument 2", ...],
  "conceded_points": ["Point from Con you acknowledge as valid", ...]
}"""

    def _closing_user_prompt(self, state: DebateState) -> str:
        prompt = f"Topic: {state.topic}\n\n"
        if state.pro_opening:
            prompt += f"YOUR OPENING POSITION:\n{state.pro_opening.overall_position}\n\n"
        prompt += "DEBATE SUMMARY:\n"
        for dr in state.debate_rounds:
            prompt += f"\nRound {dr.round_number}:\n"
            for r in dr.pro_rebuttals:
                factor = next((f for f in state.factors if f.id == r.factor_id), None)
                fname = factor.name if factor else r.factor_id
                prompt += f"  Your rebuttal on {fname}: {r.content}\n"
            for r in dr.con_rebuttals:
                factor = next((f for f in state.factors if f.id == r.factor_id), None)
                fname = factor.name if factor else r.factor_id
                prompt += f"  Con's rebuttal on {fname}: {r.content}\n"
        if state.cross_exam_answers:
            prompt += "\nCROSS-EXAM ANSWERS (yours):\n"
            pro_answers = [a for a in state.cross_exam_answers if a.agent_role == AgentRole.PRO]
            for a in pro_answers:
                q = next((q for q in state.cross_exam_questions if q.id == a.question_id), None)
                if q:
                    prompt += f"  Q: {q.question}\n  A: {a.answer}\n"
        prompt += "\nDeliver your closing statement."
        return prompt

    def _parse_closing(self, response: str) -> ClosingStatement:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(response[start:end])
                return ClosingStatement(
                    id=str(uuid.uuid4()),
                    agent_role=self.role,
                    stance="pro",
                    final_position=data.get("final_position", ""),
                    strongest_arguments=data.get("strongest_arguments", []),
                    conceded_points=data.get("conceded_points", []),
                )
        except Exception as e:
            print(f"Pro closing parse error: {e}")
        return ClosingStatement(
            id=str(uuid.uuid4()),
            agent_role=self.role,
            stance="pro",
            final_position=response[:500],
        )

    async def execute(self, state: DebateState, factor_id: str = None, **kwargs):
        if factor_id:
            factor = next((f for f in state.factors if f.id == factor_id), None)
            if factor:
                return await self.execute_rebuttal(state, factor, 1)
        return await self.execute_opening(state)