"""
Debate Orchestration Service
"""

import uuid
from app.models.debate import (
    DebateState, DebatePhase, AgentRole, DebateRequest, DebateReport
)
from app.core.config import settings
from app.services.moderator import Moderator
from app.services.debate_store import (
    save_debate, update_debate, append_event, log_usage
)
from app.services.user_store import increment_debate_count
from app.agents.factor_extraction import FactorExtractionAgent
from app.agents.pro_agent import ProAgent
from app.agents.con_agent import ConAgent
from app.agents.cross_examiner import CrossExaminerAgent
from app.agents.round_evaluator import RoundEvaluatorAgent
from app.agents.synthesizer import SynthesizerAgent


class DebateOrchestrator:

    def __init__(self):
        self.moderator = Moderator()
        self.factor_agent = FactorExtractionAgent()
        self.pro_agent = ProAgent()
        self.con_agent = ConAgent()
        self.cross_examiner = CrossExaminerAgent()
        self.round_evaluator = RoundEvaluatorAgent()
        self.synthesizer = SynthesizerAgent()

    def _print(self, title: str, body: str) -> None:
        if not settings.LOG_AGENT_CONVERSATION:
            return
        print(f"\n{'-' * 72}\n{title}\n{'-' * 72}\n{body}")

    def _phase(self, name: str) -> None:
        if not settings.LOG_AGENT_CONVERSATION:
            return
        print(f"\n{'=' * 72}\nPHASE: {name}\n{'=' * 72}")

    async def run_debate(self, request: DebateRequest, user_id: str, debate_id: str = None) -> DebateState:
        state = self._init_state(request, debate_id)
        # Persist new debate immediately so it exists in DB from the start
        await save_debate(state, user_id)
        await log_usage(user_id, state.debate_id, "debate_started", settings.GROQ_MODEL)

        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.MODERATOR,
            event_type="debate_started",
            content={"topic": state.topic, "time_budget": state.time_budget},
        )

        self.moderator.reset_timer()

        try:
            while self.moderator.should_proceed(state):
                self.moderator.update_time(state)
                action = self.moderator.next_action(state)

                if action == "factor_extraction":
                    await self._do_factor_extraction(state, user_id)
                elif action == "pro_opening":
                    self._phase("OPENING STATEMENTS")
                    state.phase = DebatePhase.OPENING_STATEMENTS
                    await self._do_pro_opening(state, user_id)
                elif action == "con_opening":
                    await self._do_con_opening(state, user_id)
                elif action == "start_rebuttal_round":
                    self._phase(f"REBUTTAL ROUND {state.current_round_number + 1}")
                    state.phase = DebatePhase.REBUTTAL_ROUNDS
                    self.moderator.start_new_round(state)
                elif action == "pro_rebuttal":
                    await self._do_pro_rebuttal(state, user_id)
                elif action == "con_rebuttal":
                    await self._do_con_rebuttal(state, user_id)
                elif action == "evaluate_round":
                    await self._do_evaluate_round(state, user_id)
                elif action == "cross_exam_questions_pro":
                    self._phase("CROSS-EXAMINATION")
                    state.phase = DebatePhase.CROSS_EXAMINATION
                    await self._do_cross_exam_questions_pro(state, user_id)
                elif action == "cross_exam_answers_pro":
                    await self._do_cross_exam_answers_pro(state, user_id)
                elif action == "cross_exam_questions_con":
                    await self._do_cross_exam_questions_con(state, user_id)
                elif action == "cross_exam_answers_con":
                    await self._do_cross_exam_answers_con(state, user_id)
                elif action == "pro_closing":
                    self._phase("CLOSING STATEMENTS")
                    state.phase = DebatePhase.CLOSING_STATEMENTS
                    await self._do_pro_closing(state, user_id)
                elif action == "con_closing":
                    await self._do_con_closing(state, user_id)
                elif action in ("synthesis", "stop"):
                    await self._do_synthesis(state, user_id)
                    break

            if state.phase != DebatePhase.COMPLETED:
                await self._do_synthesis(state, user_id)

        except Exception as e:
            import traceback
            traceback.print_exc()
            state.phase = DebatePhase.COMPLETED
            state.report = DebateReport(
                debate_quality="Low",
                debate_quality_reason=f"Debate failed: {str(e)}",
                confidence_score=0.0,
                confidence_reason="Debate execution failed.",
                what_failed=[f"Error: {str(e)}"],
            )
            await append_event(
                state.debate_id, user_id,
                agent=AgentRole.MODERATOR,
                event_type="error",
                content={"error": str(e)},
            )

        # Final save + usage log
        await update_debate(state)
        await increment_debate_count(user_id)
        await log_usage(user_id, state.debate_id, "debate_completed", settings.GROQ_MODEL)

        return state

    def _init_state(self, request: DebateRequest, debate_id: str = None) -> DebateState:
        return DebateState(
            debate_id=debate_id or str(uuid.uuid4()),
            topic=request.topic,
            time_budget=request.time_budget,
            time_remaining=request.time_budget,
            phase=DebatePhase.INITIALIZATION,
        )

    # ------------------------------------------------------------------
    # Phase handlers
    # ------------------------------------------------------------------

    async def _do_factor_extraction(self, state: DebateState, user_id: str) -> None:
        self._phase("FACTOR EXTRACTION")
        state.phase = DebatePhase.FACTOR_EXTRACTION
        result = await self.factor_agent.execute(state)
        state.factors = result["factors"]
        factors_text = "\n".join(
            f"{i+1}. {f.name} (importance={f.importance})\n   {f.description}"
            for i, f in enumerate(state.factors)
        ) or "(no factors extracted)"
        self._print("[FACTOR EXTRACTION] Factors selected", factors_text)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.FACTOR_EXTRACTION,
            event_type="factor_extraction_result",
            content={"factors": [
                {"id": f.id, "name": f.name, "description": f.description, "importance": f.importance}
                for f in state.factors
            ]},
        )
        self.moderator.record_action(state, "factor_extraction", AgentRole.FACTOR_EXTRACTION,
                                     {"factors": [f.name for f in state.factors]})

    async def _do_pro_opening(self, state: DebateState, user_id: str) -> None:
        result = await self.pro_agent.execute_opening(state)
        state.pro_opening = result["opening"]
        self._print("[PRO] Opening Statement", state.pro_opening.overall_position)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.PRO,
            event_type="pro_opening",
            content={
                "overall_position": state.pro_opening.overall_position,
                "factor_positions": state.pro_opening.factor_positions,
            },
        )
        self.moderator.record_action(state, "pro_opening", AgentRole.PRO,
                                     {"overall": state.pro_opening.overall_position})

    async def _do_con_opening(self, state: DebateState, user_id: str) -> None:
        result = await self.con_agent.execute_opening(state)
        state.con_opening = result["opening"]
        self._print("[CON] Opening Statement", state.con_opening.overall_position)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.CON,
            event_type="con_opening",
            content={
                "overall_position": state.con_opening.overall_position,
                "factor_positions": state.con_opening.factor_positions,
            },
        )
        self.moderator.record_action(state, "con_opening", AgentRole.CON,
                                     {"overall": state.con_opening.overall_position})

    async def _do_pro_rebuttal(self, state: DebateState, user_id: str) -> None:
        factor_id = self.moderator.get_next_factor_for_pro_rebuttal(state)
        if not factor_id:
            return
        factor = next((f for f in state.factors if f.id == factor_id), None)
        if not factor:
            return
        result = await self.pro_agent.execute_rebuttal(state, factor, state.current_round_number)
        rebuttal = result["rebuttal"]
        state.debate_rounds[-1].pro_rebuttals.append(rebuttal)
        self._print(f"[PRO] Round {state.current_round_number} Rebuttal — {factor.name}", rebuttal.content)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.PRO,
            event_type="pro_rebuttal",
            meta={"round": state.current_round_number, "factor_id": factor_id},
            content={
                "content": rebuttal.content,
                "challenged_claims": rebuttal.challenged_claims,
                "new_points": rebuttal.new_points,
            },
        )
        self.moderator.record_action(state, "pro_rebuttal", AgentRole.PRO,
                                     {"round": state.current_round_number, "factor": factor.name})

    async def _do_con_rebuttal(self, state: DebateState, user_id: str) -> None:
        factor_id = self.moderator.get_next_factor_for_con_rebuttal(state)
        if not factor_id:
            return
        factor = next((f for f in state.factors if f.id == factor_id), None)
        if not factor:
            return
        result = await self.con_agent.execute_rebuttal(state, factor, state.current_round_number)
        rebuttal = result["rebuttal"]
        state.debate_rounds[-1].con_rebuttals.append(rebuttal)
        self._print(f"[CON] Round {state.current_round_number} Rebuttal — {factor.name}", rebuttal.content)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.CON,
            event_type="con_rebuttal",
            meta={"round": state.current_round_number, "factor_id": factor_id},
            content={
                "content": rebuttal.content,
                "challenged_claims": rebuttal.challenged_claims,
                "new_points": rebuttal.new_points,
            },
        )
        self.moderator.record_action(state, "con_rebuttal", AgentRole.CON,
                                     {"round": state.current_round_number, "factor": factor.name})

    async def _do_evaluate_round(self, state: DebateState, user_id: str) -> None:
        result = await self.round_evaluator.execute(state)
        evaluation = result["evaluation"]
        current_round = state.debate_rounds[-1]
        current_round.should_continue = evaluation.should_continue
        current_round.evaluation_reason = evaluation.reason
        current_round.new_arguments_introduced = evaluation.new_arguments_introduced
        current_round.conflicts_resolved = evaluation.resolved_conflicts
        current_round.conflicts_remaining = evaluation.unresolved_conflicts
        state.unresolved_conflicts = evaluation.unresolved_conflicts
        state.resolved_conflicts.extend(evaluation.resolved_conflicts)
        self._print(f"[ROUND EVALUATOR] Round {state.current_round_number}",
                    f"Continue: {evaluation.should_continue}\nReason: {evaluation.reason}")
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.ROUND_EVALUATOR,
            event_type="round_evaluation",
            meta={"round": state.current_round_number},
            content={
                "should_continue": evaluation.should_continue,
                "reason": evaluation.reason,
                "new_arguments_introduced": evaluation.new_arguments_introduced,
                "going_in_circles": evaluation.going_in_circles,
                "unresolved_conflicts": evaluation.unresolved_conflicts,
            },
        )
        self.moderator.record_action(state, "evaluate_round", AgentRole.ROUND_EVALUATOR,
                                     {"round": state.current_round_number,
                                      "should_continue": evaluation.should_continue})

    async def _do_cross_exam_questions_pro(self, state: DebateState, user_id: str) -> None:
        result = await self.cross_examiner.generate_questions_for_pro(state)
        questions = result["questions"]
        state.cross_exam_questions.extend(questions)
        q_text = "\n\n".join(f"Q{i+1}: {q.question}\n    Context: {q.context}"
                              for i, q in enumerate(questions))
        self._print("[CROSS-EXAMINER] Questions for Pro", q_text)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.CROSS_EXAMINER,
            event_type="cross_exam_questions_pro",
            content={"questions": [{"id": q.id, "question": q.question, "context": q.context}
                                    for q in questions]},
        )
        self.moderator.record_action(state, "cross_exam_questions_pro",
                                     AgentRole.CROSS_EXAMINER, {"count": len(questions)})

    async def _do_cross_exam_answers_pro(self, state: DebateState, user_id: str) -> None:
        pro_q = [q for q in state.cross_exam_questions if q.target_agent == AgentRole.PRO]
        if not pro_q:
            return
        result = await self.cross_examiner.get_pro_answers(state, pro_q)
        answers = result["answers"]
        state.cross_exam_answers.extend(answers)
        a_text = ""
        for a in answers:
            q = next((q for q in pro_q if q.id == a.question_id), None)
            if q:
                a_text += f"Q: {q.question}\nA: {a.answer}\n\n"
        self._print("[PRO] Cross-Exam Answers", a_text)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.PRO,
            event_type="cross_exam_answers_pro",
            content={"answers": [{"question_id": a.question_id, "answer": a.answer}
                                   for a in answers]},
        )
        self.moderator.record_action(state, "cross_exam_answers_pro",
                                     AgentRole.PRO, {"count": len(answers)})

    async def _do_cross_exam_questions_con(self, state: DebateState, user_id: str) -> None:
        result = await self.cross_examiner.generate_questions_for_con(state)
        questions = result["questions"]
        state.cross_exam_questions.extend(questions)
        q_text = "\n\n".join(f"Q{i+1}: {q.question}\n    Context: {q.context}"
                              for i, q in enumerate(questions))
        self._print("[CROSS-EXAMINER] Questions for Con", q_text)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.CROSS_EXAMINER,
            event_type="cross_exam_questions_con",
            content={"questions": [{"id": q.id, "question": q.question, "context": q.context}
                                    for q in questions]},
        )
        self.moderator.record_action(state, "cross_exam_questions_con",
                                     AgentRole.CROSS_EXAMINER, {"count": len(questions)})

    async def _do_cross_exam_answers_con(self, state: DebateState, user_id: str) -> None:
        con_q = [q for q in state.cross_exam_questions if q.target_agent == AgentRole.CON]
        if not con_q:
            return
        result = await self.cross_examiner.get_con_answers(state, con_q)
        answers = result["answers"]
        state.cross_exam_answers.extend(answers)
        a_text = ""
        for a in answers:
            q = next((q for q in con_q if q.id == a.question_id), None)
            if q:
                a_text += f"Q: {q.question}\nA: {a.answer}\n\n"
        self._print("[CON] Cross-Exam Answers", a_text)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.CON,
            event_type="cross_exam_answers_con",
            content={"answers": [{"question_id": a.question_id, "answer": a.answer}
                                   for a in answers]},
        )
        self.moderator.record_action(state, "cross_exam_answers_con",
                                     AgentRole.CON, {"count": len(answers)})

    async def _do_pro_closing(self, state: DebateState, user_id: str) -> None:
        result = await self.pro_agent.execute_closing(state)
        state.pro_closing = result["closing"]
        self._print("[PRO] Closing Statement", state.pro_closing.final_position)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.PRO,
            event_type="pro_closing",
            content={
                "final_position": state.pro_closing.final_position,
                "strongest_arguments": state.pro_closing.strongest_arguments,
                "conceded_points": state.pro_closing.conceded_points,
            },
        )
        self.moderator.record_action(state, "pro_closing", AgentRole.PRO,
                                     {"final": state.pro_closing.final_position})

    async def _do_con_closing(self, state: DebateState, user_id: str) -> None:
        result = await self.con_agent.execute_closing(state)
        state.con_closing = result["closing"]
        self._print("[CON] Closing Statement", state.con_closing.final_position)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.CON,
            event_type="con_closing",
            content={
                "final_position": state.con_closing.final_position,
                "strongest_arguments": state.con_closing.strongest_arguments,
                "conceded_points": state.con_closing.conceded_points,
            },
        )
        self.moderator.record_action(state, "con_closing", AgentRole.CON,
                                     {"final": state.con_closing.final_position})

    async def _do_synthesis(self, state: DebateState, user_id: str) -> None:
        self._phase("SYNTHESIS")
        state.phase = DebatePhase.SYNTHESIS
        result = await self.synthesizer.execute(state)
        report = result["report"]
        state.report = report
        summary = (
            f"Debate Quality: {report.debate_quality}\n"
            f"Confidence Score: {report.confidence_score}\n"
            f"Verdict: {report.verdict or 'No clear verdict'}\n\n"
            f"What Worked:\n" + "\n".join(f"  - {w}" for w in report.what_worked) + "\n\n"
            f"What Failed:\n" + "\n".join(f"  - {w}" for w in report.what_failed) + "\n\n"
            f"Why It Happened: {report.why_it_happened}\n\n"
            f"How To Improve:\n" + "\n".join(f"  - {h}" for h in report.how_to_improve)
        )
        self._print("[SYNTHESIS] Debate Report", summary)
        await append_event(
            state.debate_id, user_id,
            agent=AgentRole.SYNTHESIZER,
            event_type="synthesis_report",
            content={
                "debate_quality": report.debate_quality,
                "confidence_score": report.confidence_score,
                "verdict": report.verdict,
                "what_worked": report.what_worked,
                "what_failed": report.what_failed,
                "why_it_happened": report.why_it_happened,
                "how_to_improve": report.how_to_improve,
            },
        )
        self.moderator.record_action(state, "synthesis", AgentRole.SYNTHESIZER,
                                     {"quality": report.debate_quality,
                                      "confidence": report.confidence_score})
        state.phase = DebatePhase.COMPLETED