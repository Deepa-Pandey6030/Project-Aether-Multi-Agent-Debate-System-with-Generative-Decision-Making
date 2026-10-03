"""
Round Evaluator Agent
Decides after each rebuttal round whether the debate should continue
or move to cross-examination.
"""

from typing import Dict, Any
import json
from app.agents.base import BaseAgent
from app.models.debate import DebateState, AgentRole, RoundEvaluation, DebateRound
from app.core.config import settings


class RoundEvaluatorAgent(BaseAgent):

    def __init__(self):
        super().__init__(AgentRole.ROUND_EVALUATOR)

    async def execute(self, state: DebateState, **kwargs) -> Dict[str, Any]:
        current_round = state.debate_rounds[-1] if state.debate_rounds else None
        if not current_round:
            return {"evaluation": RoundEvaluation(
                round_number=0,
                should_continue=False,
                reason="No rounds completed yet.",
                new_arguments_introduced=False,
                going_in_circles=False
            )}

        # Hard cap
        if state.current_round_number >= settings.MAX_DEBATE_ROUNDS:
            return {"evaluation": RoundEvaluation(
                round_number=state.current_round_number,
                should_continue=False,
                reason=f"Maximum debate rounds ({settings.MAX_DEBATE_ROUNDS}) reached.",
                new_arguments_introduced=False,
                going_in_circles=False
            )}

        # Below minimum — always continue
        if state.current_round_number < settings.MIN_DEBATE_ROUNDS:
            return {"evaluation": RoundEvaluation(
                round_number=state.current_round_number,
                should_continue=True,
                reason=f"Minimum debate rounds ({settings.MIN_DEBATE_ROUNDS}) not yet reached.",
                new_arguments_introduced=True,
                going_in_circles=False
            )}

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(state, current_round)

        response = await self._call_llm(
            system_prompt, user_prompt, max_tokens=1000,
            debate_id=state.debate_id, event_prefix="round_evaluation",
            meta={"round_number": state.current_round_number},
        )

        evaluation = self._parse_evaluation(response, state.current_round_number)
        return {"evaluation": evaluation, "raw_response": response}

    def _build_system_prompt(self) -> str:
        return """You are the Round Evaluator in Project AETHER.

Your role: Assess whether the debate has progressed enough to move on or needs another round.

You are NEUTRAL — you do not favour Pro or Con.

Evaluate based on:
- Were genuinely new arguments or evidence introduced this round?
- Is the debate going in circles (same points repeated)?
- Are there important unresolved conflicts that another round would help resolve?
- Would another round produce meaningful new insight?

Output format (JSON):
{
  "should_continue": true/false,
  "reason": "One sentence explaining your decision",
  "new_arguments_introduced": true/false,
  "going_in_circles": true/false,
  "unresolved_conflicts": ["conflict 1", "conflict 2"],
  "resolved_conflicts": ["conflict that got resolved this round"]
}

Be honest and concise. Don't let the debate drag on unnecessarily."""

    def _build_user_prompt(self, state: DebateState, current_round: DebateRound) -> str:
        prompt = f"Topic: {state.topic}\n"
        prompt += f"Round just completed: {current_round.round_number}\n\n"

        prompt += "FACTORS:\n"
        for f in state.factors:
            prompt += f"- {f.name}: {f.description}\n"

        prompt += "\nOPENING STATEMENTS SUMMARY:\n"
        if state.pro_opening:
            prompt += f"Pro overall: {state.pro_opening.overall_position}\n"
        if state.con_opening:
            prompt += f"Con overall: {state.con_opening.overall_position}\n"

        prompt += f"\nROUND {current_round.round_number} REBUTTALS:\n"

        prompt += "\nPRO rebuttals this round:\n"
        for r in current_round.pro_rebuttals:
            factor = next((f for f in state.factors if f.id == r.factor_id), None)
            fname = factor.name if factor else r.factor_id
            prompt += f"  [{fname}]: {r.content}\n"
            if r.new_points:
                prompt += f"  New points introduced: {', '.join(r.new_points)}\n"

        prompt += "\nCON rebuttals this round:\n"
        for r in current_round.con_rebuttals:
            factor = next((f for f in state.factors if f.id == r.factor_id), None)
            fname = factor.name if factor else r.factor_id
            prompt += f"  [{fname}]: {r.content}\n"
            if r.new_points:
                prompt += f"  New points introduced: {', '.join(r.new_points)}\n"

        if state.unresolved_conflicts:
            prompt += f"\nCurrently unresolved conflicts: {', '.join(state.unresolved_conflicts)}\n"

        prompt += "\nShould the debate continue with another rebuttal round?"
        return prompt

    def _parse_evaluation(self, response: str, round_number: int) -> RoundEvaluation:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(response[start:end])
                return RoundEvaluation(
                    round_number=round_number,
                    should_continue=data.get("should_continue", False),
                    reason=data.get("reason", ""),
                    new_arguments_introduced=data.get("new_arguments_introduced", False),
                    going_in_circles=data.get("going_in_circles", False),
                    unresolved_conflicts=data.get("unresolved_conflicts", []),
                    resolved_conflicts=data.get("resolved_conflicts", []),
                )
        except Exception as e:
            print(f"RoundEvaluator parse error: {e}")

        return RoundEvaluation(
            round_number=round_number,
            should_continue=False,
            reason="Evaluation parsing failed — stopping debate.",
            new_arguments_introduced=False,
            going_in_circles=True,
        )