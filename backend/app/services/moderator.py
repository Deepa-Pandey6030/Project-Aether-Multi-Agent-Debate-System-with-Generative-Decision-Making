"""
Moderator — controls debate flow across all 6 phases
"""

import time
from typing import Optional
from app.models.debate import (
    DebateState, DebatePhase, DebateAction, AgentRole, DebateRound
)
from app.core.config import settings


class Moderator:

    def __init__(self):
        self.start_time: Optional[float] = None

    def should_proceed(self, state: DebateState) -> bool:
        if state.time_remaining <= 0:
            return False
        if state.phase == DebatePhase.COMPLETED:
            return False
        return True

    def next_action(self, state: DebateState) -> str:
        phase = state.phase

        if phase == DebatePhase.INITIALIZATION:
            return "factor_extraction"

        if phase == DebatePhase.FACTOR_EXTRACTION:
            if not state.factors:
                return "factor_extraction"
            return "pro_opening"

        if phase == DebatePhase.OPENING_STATEMENTS:
            if state.pro_opening is None:
                return "pro_opening"
            if state.con_opening is None:
                return "con_opening"
            return "start_rebuttal_round"

        if phase == DebatePhase.REBUTTAL_ROUNDS:
            if not state.debate_rounds:
                return "start_rebuttal_round"
            current_round = state.debate_rounds[-1]
            n_factors = len(state.factors)
            if len(current_round.pro_rebuttals) < n_factors:
                return "pro_rebuttal"
            if len(current_round.con_rebuttals) < n_factors:
                return "con_rebuttal"
            if not current_round.evaluation_reason:
                return "evaluate_round"
            if (current_round.should_continue and
                    state.current_round_number < settings.MAX_DEBATE_ROUNDS):
                return "start_rebuttal_round"
            return "cross_exam_questions_pro"

        if phase == DebatePhase.CROSS_EXAMINATION:
            pro_q = [q for q in state.cross_exam_questions if q.target_agent == AgentRole.PRO]
            con_q = [q for q in state.cross_exam_questions if q.target_agent == AgentRole.CON]
            pro_a = [a for a in state.cross_exam_answers if a.agent_role == AgentRole.PRO]
            con_a = [a for a in state.cross_exam_answers if a.agent_role == AgentRole.CON]
            if not pro_q:
                return "cross_exam_questions_pro"
            if len(pro_a) < len(pro_q):
                return "cross_exam_answers_pro"
            if not con_q:
                return "cross_exam_questions_con"
            if len(con_a) < len(con_q):
                return "cross_exam_answers_con"
            if settings.CLOSING_STATEMENTS_ENABLED and state.time_remaining > settings.CLOSING_STATEMENTS_MIN_TIME:
                return "pro_closing"
            return "synthesis"

        if phase == DebatePhase.CLOSING_STATEMENTS:
            if state.pro_closing is None:
                return "pro_closing"
            if state.con_closing is None:
                return "con_closing"
            return "synthesis"

        if phase == DebatePhase.SYNTHESIS:
            return "synthesis"

        return "synthesis"

    def start_new_round(self, state: DebateState) -> DebateRound:
        state.current_round_number += 1
        new_round = DebateRound(round_number=state.current_round_number)
        state.debate_rounds.append(new_round)
        return new_round

    def get_next_factor_for_pro_rebuttal(self, state: DebateState) -> Optional[str]:
        if not state.debate_rounds:
            return None
        current_round = state.debate_rounds[-1]
        rebutted_ids = {r.factor_id for r in current_round.pro_rebuttals}
        for f in state.factors:
            if f.id not in rebutted_ids:
                return f.id
        return None

    def get_next_factor_for_con_rebuttal(self, state: DebateState) -> Optional[str]:
        if not state.debate_rounds:
            return None
        current_round = state.debate_rounds[-1]
        rebutted_ids = {r.factor_id for r in current_round.con_rebuttals}
        for f in state.factors:
            if f.id not in rebutted_ids:
                return f.id
        return None

    def update_time(self, state: DebateState) -> None:
        if self.start_time is None:
            self.start_time = time.time()
        elapsed = int(time.time() - self.start_time)
        state.time_elapsed = elapsed
        state.time_remaining = max(0, state.time_budget - elapsed)

    def record_action(self, state: DebateState, action_type: str, agent: AgentRole, content) -> None:
        state.action_history.append(DebateAction(
            action_type=action_type,
            agent=agent,
            content=content,
        ))

    def reset_timer(self) -> None:
        self.start_time = None