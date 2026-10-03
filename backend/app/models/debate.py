"""
Pydantic models for AETHER Debate System
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    FACTOR_EXTRACTION = "factor_extraction"
    PRO = "pro"
    CON = "con"
    MODERATOR = "moderator"
    CROSS_EXAMINER = "cross_examiner"
    ROUND_EVALUATOR = "round_evaluator"
    SYNTHESIZER = "synthesizer"


class DebatePhase(str, Enum):
    INITIALIZATION = "initialization"
    FACTOR_EXTRACTION = "factor_extraction"
    OPENING_STATEMENTS = "opening_statements"
    REBUTTAL_ROUNDS = "rebuttal_rounds"
    CROSS_EXAMINATION = "cross_examination"
    CLOSING_STATEMENTS = "closing_statements"
    SYNTHESIS = "synthesis"
    COMPLETED = "completed"


class Factor(BaseModel):
    id: str
    name: str
    description: str
    importance: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Opening Statements
# ---------------------------------------------------------------------------

class OpeningStatement(BaseModel):
    id: str
    agent_role: AgentRole
    stance: Literal["pro", "con"]
    factor_positions: Dict[str, str] = {}   # factor_id -> position text
    overall_position: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Rebuttal Rounds
# ---------------------------------------------------------------------------

class RebuttalArgument(BaseModel):
    id: str
    round_number: int
    agent_role: AgentRole
    stance: Literal["pro", "con"]
    factor_id: str
    content: str
    summary_fact: str = ""
    challenged_claims: List[str] = []
    new_points: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DebateRound(BaseModel):
    round_number: int
    pro_rebuttals: List[RebuttalArgument] = []
    con_rebuttals: List[RebuttalArgument] = []
    should_continue: bool = False
    evaluation_reason: str = ""
    new_arguments_introduced: bool = False
    conflicts_resolved: List[str] = []
    conflicts_remaining: List[str] = []


class RoundEvaluation(BaseModel):
    round_number: int
    should_continue: bool
    reason: str
    new_arguments_introduced: bool
    going_in_circles: bool
    unresolved_conflicts: List[str] = []
    resolved_conflicts: List[str] = []


# ---------------------------------------------------------------------------
# Cross Examination
# ---------------------------------------------------------------------------

class CrossExamQuestion(BaseModel):
    id: str
    target_agent: AgentRole
    question: str
    context: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrossExamAnswer(BaseModel):
    id: str
    question_id: str
    agent_role: AgentRole
    answer: str
    concession: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConcessionPoint(BaseModel):
    agent_role: AgentRole
    factor_id: Optional[str] = None
    conceded_point: str
    context: str = ""


# ---------------------------------------------------------------------------
# Closing Statements
# ---------------------------------------------------------------------------

class ClosingStatement(BaseModel):
    id: str
    agent_role: AgentRole
    stance: Literal["pro", "con"]
    strongest_arguments: List[str] = []
    conceded_points: List[str] = []
    final_position: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Debate Report
# ---------------------------------------------------------------------------

class ArgumentAssessment(BaseModel):
    argument_summary: str
    held_up: bool
    reason: str


class DebateReport(BaseModel):
    pro_strongest_arguments: List[str] = []
    con_strongest_arguments: List[str] = []
    arguments_that_held_up: List[ArgumentAssessment] = []
    arguments_that_collapsed: List[ArgumentAssessment] = []
    concession_points: List[ConcessionPoint] = []
    debate_quality: str = ""
    debate_quality_reason: str = ""
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence_reason: str = ""
    verdict: Optional[str] = None
    what_worked: List[str] = []
    what_failed: List[str] = []
    why_it_happened: str = ""
    how_to_improve: List[str] = []
    debate_trace: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Debate State
# ---------------------------------------------------------------------------

class DebateAction(BaseModel):
    action_type: str
    agent: AgentRole
    content: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DebateState(BaseModel):
    debate_id: str
    topic: str
    time_budget: int
    time_elapsed: int = 0
    time_remaining: int

    phase: DebatePhase = DebatePhase.INITIALIZATION

    # Phase 1
    factors: List[Factor] = []

    # Phase 2 - Opening Statements
    pro_opening: Optional[OpeningStatement] = None
    con_opening: Optional[OpeningStatement] = None

    # Phase 3 - Rebuttal Rounds
    debate_rounds: List[DebateRound] = []
    current_round_number: int = 0

    # Phase 4 - Cross Examination
    cross_exam_questions: List[CrossExamQuestion] = []
    cross_exam_answers: List[CrossExamAnswer] = []

    # Phase 5 - Closing Statements
    pro_closing: Optional[ClosingStatement] = None
    con_closing: Optional[ClosingStatement] = None

    # Tracking
    action_history: List[DebateAction] = []
    unresolved_conflicts: List[str] = []
    resolved_conflicts: List[str] = []
    exposed_assumptions: List[str] = []
    concession_points: List[ConcessionPoint] = []

    debate_value: float = 1.0

    # Final report
    report: Optional[DebateReport] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ---------------------------------------------------------------------------
# API Models
# ---------------------------------------------------------------------------

class DebateRequest(BaseModel):
    topic: str = Field(..., min_length=10, max_length=1000)
    time_budget: int = Field(default=600, ge=300, le=1200)
    document_content: Optional[str] = None


class DebateResponse(BaseModel):
    debate_id: str
    status: str
    current_phase: DebatePhase
    state: DebateState


# Backward compat
class FinalDecision(BaseModel):
    verdict: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    risks: List[str]
    conditions: List[str] = []
    debate_trace: List[Dict[str, Any]] = []