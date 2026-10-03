# AETHER System Architecture

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         HTTP REQUEST                             │
│               POST /api/v1/debate/start                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Router                                │
│                   (app/api/routes.py)                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Debate Orchestrator                             │
│              (app/services/orchestrator.py)                      │
│                                                                   │
│  • Initializes DebateState                                       │
│  • Coordinates all agents                                        │
│  • Manages debate loop                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────┐
         │      MODERATOR          │
         │ (services/moderator.py) │
         │                         │
         │ • Tracks time           │
         │ • Decides next action   │
         │ • Controls flow         │
         └────────┬────────────────┘
                  │
                  │ Determines next action
                  │
        ┌─────────┴──────────────────────────────┐
        │                                         │
        ▼                                         ▼
┌──────────────┐                         ┌──────────────┐
│    PHASE 1   │                         │   PHASE 2    │
│   FACTOR     │──────────┐              │ ARGUMENTATION│
│  EXTRACTION  │          │              │              │
└──────┬───────┘          │              └──────┬───────┘
       │                  │                     │
       ▼                  │                     │
┌──────────────┐          │              ┌──────┴───────┐
│ Agent 1      │          │              │ For each     │
│ Factor       │          │              │ factor:      │
│ Extraction   │          │              └──────┬───────┘
└──────┬───────┘          │                     │
       │                  │              ┌──────┴───────┐
       │ Returns:         │              │              │
       │ - factors[]      │              │              │
       │                  │              │              │
       ▼                  │              ▼              ▼
┌──────────────┐          │      ┌──────────┐   ┌──────────┐
│ SHARED       │◄─────────┼──────┤ Agent 2  │   │ Agent 3  │
│ DEBATE       │          │      │ PRO      │   │ CON      │
│ STATE        │          │      │ Agent    │   │ Agent    │
│              │          │      └──────────┘   └──────────┘
│ Contains:    │          │           │              │
│ • topic      │          │           │ arguments[]  │
│ • factors[]  │          │           └──────┬───────┘
│ • arguments[]│          │                  │
│ • time info  │          │                  ▼
│ • conflicts  │          │         ┌──────────────┐
│ • verdict    │          │         │ Disagreement │
│              │          │         │ detected?    │
└──────┬───────┘          │         └──────┬───────┘
       │                  │                │
       │                  │         If high & time allows
       │                  │                │
       │                  │                ▼
       │                  │       ┌──────────────┐
       │                  │       │ Cross-Exam   │
       │                  │       │ (Optional)   │
       │                  │       └──────────────┘
       │                  │
       │                  │
       ▼                  │
┌──────────────┐          │
│   PHASE 3    │          │
│  SYNTHESIS   │◄─────────┘
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Agent 5      │
│ Synthesizer  │
│              │
│ Produces:    │
│ • verdict    │
│ • confidence │
│ • reason     │
│ • risks      │
│ • conditions │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       HTTP RESPONSE                              │
│                   DebateState + Decision                         │
└─────────────────────────────────────────────────────────────────┘
```

## Agent Interaction Pattern

```
Agents DO NOT talk directly to each other
       │
       │ All interaction through
       │ Shared Debate State
       ▼

┌────────────┐     ┌────────────┐     ┌────────────┐
│  Agent 1   │────▶│   Debate   │◀────│  Agent 2   │
│  (Factor)  │     │   State    │     │   (Pro)    │
└────────────┘     │            │     └────────────┘
                   │  • topic   │
┌────────────┐     │  • factors │     ┌────────────┐
│  Agent 3   │────▶│  • args    │◀────│  Agent 5   │
│   (Con)    │     │  • time    │     │ (Synth)    │
└────────────┘     └────────────┘     └────────────┘
```

## Time-Based Scaling

```
TIME BUDGET  │  FACTORS  │  DEPTH    │  CROSS-EXAM
─────────────┼───────────┼───────────┼──────────────
  5 min      │    1      │  Shallow  │   No
 10 min      │   2-3     │  Medium   │   Maybe
 20 min      │   3-4     │   Deep    │   Yes
```

## Data Flow

```
1. Request arrives
   └─▶ topic + time_budget

2. Initialize DebateState
   └─▶ Creates shared state object

3. Factor Extraction
   └─▶ Populates state.factors[]

4. For each factor:
   ├─▶ Pro Agent adds to state.arguments[]
   ├─▶ Con Agent adds to state.arguments[]
   └─▶ (Optional) Cross-examination

5. Synthesis
   ├─▶ Reads entire state
   └─▶ Populates state.verdict, confidence, reason

6. Return DebateState
   └─▶ Complete decision with trace
```

## Module Dependencies

```
main.py
  ├─▶ app.api.routes
  │     └─▶ app.services.orchestrator
  │           ├─▶ app.services.moderator
  │           └─▶ app.agents.*
  │                 └─▶ app.agents.base
  │                       └─▶ anthropic (Claude API)
  │
  └─▶ app.core.config
        └─▶ pydantic_settings

app.models.debate
  └─▶ Defines all data structures
```

## Key Files Reference

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point |
| `app/api/routes.py` | REST API endpoints |
| `app/services/orchestrator.py` | Main debate coordinator |
| `app/services/moderator.py` | Time & flow control |
| `app/agents/base.py` | Base agent class |
| `app/agents/factor_extraction.py` | Agent 1 - Factor extraction |
| `app/agents/pro_agent.py` | Agent 2 - Pro arguments |
| `app/agents/con_agent.py` | Agent 3 - Con arguments |
| `app/agents/synthesizer.py` | Agent 5 - Final decision |
| `app/models/debate.py` | Pydantic data models |
| `app/core/config.py` | Configuration settings |

## Comparison: AETHER vs Traditional Systems

| Feature | Web Scraping/RAG | AETHER |
|---------|------------------|---------|
| Goal | Information expansion | Decision compression |
| Approach | Consensus seeking | Forced disagreement |
| Time | No urgency | Time-aware |
| Output | Information dump | Clear verdict |
| Accountability | None | Confidence + risks |
| Interaction | User Q&A | Agent debate |
