# AETHER Backend (FastAPI) — What this folder does

This backend runs **Project AETHER**, a multi-agent debate system exposed via a **FastAPI** API.

At a high level:
- You send a debate topic + time budget to an API endpoint.
- The backend orchestrates several agents (factor extraction → pro → con → synthesis).
- It returns a final decision (verdict, confidence, reason, risks, conditions).
- It also records the full debate transcript to JSON files under `backend/conversation/`.

---

## 1) Folder structure (what each part is for)

### Entry points
- `main.py`
  - Starts the FastAPI app (used with `python main.py`).
- `test_debate.py`
  - Simple client script to call the API and print the result + trace.

### Application package: `app/`
- `app/api/routes.py`
  - API routes for starting a debate and retrieving the debate trace.
- `app/core/config.py`
  - Central configuration using `pydantic-settings` (loads from `.env`).
- `app/models/debate.py`
  - Pydantic models describing the request/response/state objects.

### Agents: `app/agents/`
Each agent is a small “role” with its own prompt and responsibilities.
- `base.py`
  - Shared LLM client wrapper and helper utilities used by all agents.
- `factor_extraction.py`
  - Extracts the minimal set of key debate factors (dimensions) to focus on.
- `pro_agent.py`
  - Generates arguments in favor of each factor.
- `con_agent.py`
  - Generates counter-arguments against the pro arguments for each factor.
- `synthesizer.py`
  - Produces the final decision based strictly on what was debated.

### Services: `app/services/`
- `orchestrator.py`
  - The main coordinator that runs the end-to-end debate.
  - Calls agents in order and records actions.
- `moderator.py`
  - Controls debate progression/phase decisions.
- `conversation_store.py`
  - Persists an append-only, structured transcript as JSON per `debate_id`.

---

## 2) What the backend can do

### A) Start a full debate
The backend can run a complete debate pipeline:
1. **Factor Extraction**: picks up to a small number of important dimensions.
2. **Pro**: argues for each factor.
3. **Con**: challenges pro on each factor.
4. **Synthesizer**: decides the final verdict using only the debate content.

### B) Return results + trace
The API returns:
- final verdict & confidence
- reason, risks, conditions
- a trace of actions taken during the debate

### C) Save debate transcripts to disk
For observability and debugging, the backend writes a JSON file for each debate:
- Location: `backend/conversation/<debate_id>.json`
- Includes events like:
  - `debate_started`
  - `factor_extraction.prompt` / `.response`
  - `pro.prompt` / `.response`, `pro_argument`
  - `con.prompt` / `.response`, `con_argument`
  - `synthesis.prompt` / `.response`, `synthesis_decision`
  - `final_state`

This makes it easy to review exactly what each agent said and what the system decided.

---

## 3) API endpoints (what to call)

Base URL (local): `http://localhost:8000`

### Health check
- `GET /health`

### Start debate
- `POST /api/v1/debate/start`

Example request body:
```json
{
  "topic": "Capital punishment should be abolished",
  "time_budget": 1200
}
```

### Get debate trace (actions)
- `GET /api/v1/debate/{debate_id}/trace`

---

## 4) Configuration (.env)

Configuration is defined in `app/core/config.py` and loaded from `backend/.env`.

Common settings:
- `GROQ_API_KEY` — required to call the LLM provider
- `GROQ_MODEL` — model name (default: `llama-3.1-8b-instant`)

Logging & storage toggles:
- `LOG_AGENT_CONVERSATION` — prints a readable transcript to terminal
- `LOG_LLM_PROMPTS` / `LOG_LLM_RESPONSES` — optional verbose LLM IO printing
- `SAVE_CONVERSATIONS` — enables writing JSON transcripts
- `CONVERSATION_DIR` — folder name (default: `conversation`)
- `STORE_LLM_IO` — store prompt/response events in the JSON transcript

---

## 5) How to run (local)

From `backend/`:
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create `backend/.env` with at least:
   ```env
   GROQ_API_KEY=your_key_here
   ```
3. Start the server:
   ```bash
   python main.py
   ```
4. Run the test client:
   ```bash
   python test_debate.py
   ```

---

## 6) Notes / design choices

- **In-memory debate storage**: debates are stored in-process (not in a database). This is fine for local use and demos.
- **Deterministic audit trail**: JSON transcripts under `backend/conversation/` are intended to make the system debuggable and easy to demo.
- **Multi-agent separation**: each agent has a single clear job to keep prompts and outputs structured.

---

## 7) Where to look for key behavior

- Debate orchestration logic: `app/services/orchestrator.py`
- Phase control logic: `app/services/moderator.py`
- Transcript persistence: `app/services/conversation_store.py`
- API surface: `app/api/routes.py`
