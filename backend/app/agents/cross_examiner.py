"""
Cross-Examiner Agent
Runs after all rebuttal rounds are complete.
Has full visibility of: opening statements, all rebuttal rounds, and their evaluations.
"""

from typing import Dict, Any, List
import json
import uuid
from app.agents.base import BaseAgent
from app.models.debate import (
    DebateState, AgentRole, CrossExamQuestion, CrossExamAnswer
)


class CrossExaminerAgent(BaseAgent):

    def __init__(self):
        super().__init__(AgentRole.CROSS_EXAMINER)

    async def generate_questions_for_pro(self, state: DebateState, **kwargs) -> Dict[str, Any]:
        system_prompt = self._system_prompt_questions("PRO")
        user_prompt = self._user_prompt_questions(state, "PRO")
        response = await self._call_llm(
            system_prompt, user_prompt, max_tokens=2000,
            debate_id=state.debate_id, event_prefix="cross_exam_questions_pro"
        )
        questions = self._parse_questions(response, AgentRole.PRO)
        return {"questions": questions, "raw_response": response}

    async def generate_questions_for_con(self, state: DebateState, **kwargs) -> Dict[str, Any]:
        system_prompt = self._system_prompt_questions("CON")
        user_prompt = self._user_prompt_questions(state, "CON")
        response = await self._call_llm(
            system_prompt, user_prompt, max_tokens=2000,
            debate_id=state.debate_id, event_prefix="cross_exam_questions_con"
        )
        questions = self._parse_questions(response, AgentRole.CON)
        return {"questions": questions, "raw_response": response}

    async def get_pro_answers(
        self, state: DebateState, questions: List[CrossExamQuestion], **kwargs
    ) -> Dict[str, Any]:
        system_prompt = self._system_prompt_answers("PRO")
        user_prompt = self._user_prompt_answers(state, questions, "PRO")
        response = await self._call_llm(
            system_prompt, user_prompt, max_tokens=2500,
            debate_id=state.debate_id, event_prefix="cross_exam_answers_pro"
        )
        answers = self._parse_answers(response, questions, AgentRole.PRO)
        return {"answers": answers, "raw_response": response}

    async def get_con_answers(
        self, state: DebateState, questions: List[CrossExamQuestion], **kwargs
    ) -> Dict[str, Any]:
        system_prompt = self._system_prompt_answers("CON")
        user_prompt = self._user_prompt_answers(state, questions, "CON")
        response = await self._call_llm(
            system_prompt, user_prompt, max_tokens=2500,
            debate_id=state.debate_id, event_prefix="cross_exam_answers_con"
        )
        answers = self._parse_answers(response, questions, AgentRole.CON)
        return {"answers": answers, "raw_response": response}

    def _system_prompt_questions(self, target: str) -> str:
        return f"""You are the Cross-Examiner Agent in Project AETHER.

You have reviewed the COMPLETE debate — opening statements and all rebuttal rounds.
Now generate 3-5 sharp, strategic questions for the {target} agent.

Principles:
- Look for contradictions ACROSS rebuttal rounds (did they shift position?)
- Probe assumptions that were never challenged
- Ask about points the opponent raised that {target} never addressed
- Look for gaps between what they claimed and what they actually proved
- Ask questions that could reveal concessions

Output format (JSON):
{{
  "questions": [
    {{
      "question": "Your precise question",
      "context": "Why this matters — what weakness or gap you are probing"
    }}
  ]
}}"""

    def _user_prompt_questions(self, state: DebateState, target: str) -> str:
        prompt = f"Topic: {state.topic}\n\n"
        prompt += "FACTORS:\n"
        for f in state.factors:
            prompt += f"  - {f.name} (importance: {f.importance}): {f.description}\n"

        prompt += "\nOPENING STATEMENTS:\n"
        if state.pro_opening:
            prompt += f"PRO overall: {state.pro_opening.overall_position}\n"
            for fid, pos in state.pro_opening.factor_positions.items():
                factor = next((f for f in state.factors if f.id == fid), None)
                fname = factor.name if factor else fid
                prompt += f"  PRO on {fname}: {pos}\n"
        if state.con_opening:
            prompt += f"CON overall: {state.con_opening.overall_position}\n"
            for fid, pos in state.con_opening.factor_positions.items():
                factor = next((f for f in state.factors if f.id == fid), None)
                fname = factor.name if factor else fid
                prompt += f"  CON on {fname}: {pos}\n"

        prompt += f"\nREBUTTAL ROUNDS ({len(state.debate_rounds)} completed):\n"
        for dr in state.debate_rounds:
            prompt += f"\n--- Round {dr.round_number} ---\n"
            for r in dr.pro_rebuttals:
                factor = next((f for f in state.factors if f.id == r.factor_id), None)
                fname = factor.name if factor else r.factor_id
                prompt += f"PRO on {fname}: {r.summary_fact or r.content}\n"
                if r.new_points:
                    prompt += f"  New points: {', '.join(r.new_points)}\n"
            for r in dr.con_rebuttals:
                factor = next((f for f in state.factors if f.id == r.factor_id), None)
                fname = factor.name if factor else r.factor_id
                prompt += f"CON on {fname}: {r.summary_fact or r.content}\n"
                if r.new_points:
                    prompt += f"  New points: {', '.join(r.new_points)}\n"
            if dr.evaluation_reason:
                prompt += f"  Evaluator: {dr.evaluation_reason}\n"

        if state.unresolved_conflicts:
            prompt += f"\nUnresolved conflicts: {', '.join(state.unresolved_conflicts)}\n"

        prompt += f"\nGenerate 3-5 strategic questions for the {target} agent."
        return prompt

    def _system_prompt_answers(self, agent_type: str) -> str:
        return f"""You are the {agent_type} Agent answering cross-examination questions in Project AETHER.

Rules:
- Answer each question directly — do not dodge
- If you need to concede a point, do so honestly
- Stay consistent with your earlier arguments
- Provide reasoning, not just assertions

Output format (JSON):
{{
  "answers": [
    {{
      "question_id": "use the index number: 1, 2, 3...",
      "answer": "Your detailed honest answer",
      "concession": "Optional — if conceding a point, state it clearly. Otherwise null."
    }}
  ]
}}"""

    def _user_prompt_answers(
        self, state: DebateState, questions: List[CrossExamQuestion], agent_type: str
    ) -> str:
        prompt = f"You are the {agent_type} agent.\nTopic: {state.topic}\n\n"
        prompt += "YOUR DEBATE HISTORY:\n"
        if agent_type == "PRO" and state.pro_opening:
            prompt += f"Opening: {state.pro_opening.overall_position}\n"
        elif agent_type == "CON" and state.con_opening:
            prompt += f"Opening: {state.con_opening.overall_position}\n"
        for dr in state.debate_rounds:
            rebuttals = dr.pro_rebuttals if agent_type == "PRO" else dr.con_rebuttals
            for r in rebuttals:
                factor = next((f for f in state.factors if f.id == r.factor_id), None)
                fname = factor.name if factor else r.factor_id
                prompt += f"Round {dr.round_number} on {fname}: {r.content}\n"
        prompt += "\nQUESTIONS TO ANSWER:\n"
        for i, q in enumerate(questions, 1):
            prompt += f"\n{i}. {q.question}\n"
            if q.context:
                prompt += f"   Context: {q.context}\n"
        prompt += "\nAnswer all questions honestly and thoroughly."
        return prompt

    def _parse_questions(self, response: str, target_agent: AgentRole) -> List[CrossExamQuestion]:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(response[start:end])
                return [
                    CrossExamQuestion(
                        id=str(uuid.uuid4()),
                        target_agent=target_agent,
                        question=q.get("question", ""),
                        context=q.get("context", ""),
                    )
                    for q in data.get("questions", [])
                ]
        except Exception as e:
            print(f"CrossExaminer question parse error: {e}")
        return []

    def _parse_answers(
        self, response: str, questions: List[CrossExamQuestion], agent_role: AgentRole
    ) -> List[CrossExamAnswer]:
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                data = json.loads(response[start:end])
                answers = []
                for i, a in enumerate(data.get("answers", [])):
                    if i < len(questions):
                        answers.append(CrossExamAnswer(
                            id=str(uuid.uuid4()),
                            question_id=questions[i].id,
                            agent_role=agent_role,
                            answer=a.get("answer", ""),
                            concession=a.get("concession") or None,
                        ))
                return answers
        except Exception as e:
            print(f"CrossExaminer answer parse error: {e}")
        return []

    async def execute(self, state: DebateState, **kwargs):
        pass