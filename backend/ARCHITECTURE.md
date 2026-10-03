A multi-agent agentic AI system using an orchestrator-driven pipeline, where specialized LLM agents debate a topic across structured phases to produce a synthesized decision report.






# Project AETHER — System Flow

---

## Agent & LLM Map

```
Factor Extraction   →  Groq
Pro Agent           →  Groq
Con Agent           →  Groq
Cross Examiner      →  Groq
Round Evaluator     →  Groq
Synthesizer         →  Gemini (primary) / Groq (fallback)
Rebuttal summary    →  Gemini (neutral 1-sentence summary_fact per rebuttal)
```

---

## Debate Flow

```
0. Authentication
   - Signup / Login → JWT access_token (30min) + refresh_token (7 days)
   - All debate endpoints require Bearer token
        ↓

1. Initialization
   - DebateState created with unique debate_id
   - Saved to MongoDB immediately
   - Real-time clock started by Moderator
        ↓

2. Factor Extraction  [FactorExtractionAgent — Groq]
   - Reads topic + time_budget
   - Extracts decision DIMENSIONS (abstract, not literal)
   - Max factors scaled to time budget:
       300s  → 1 factor
       600s  → 2 factors
       900s  → 3 factors
       1200s → 4 factors
   - Hard cap enforced in code regardless of LLM output
        ↓

3. Pro Opening Statement  [ProAgent — Groq]
   - Sees: topic + all factors
   - Does NOT see Con's position yet
   - States position on every factor
   - Declares key assumptions
        ↓

4. Con Opening Statement  [ConAgent — Groq]
   - Sees: topic + all factors + Pro's opening
   - States opposition on every factor
   - Identifies risks and failure modes
        ↓

5. Rebuttal Rounds  [ProAgent + ConAgent + RoundEvaluatorAgent — Groq]
   - Runs 1 to 4 rounds (MIN=1, MAX=4)
   - Each round:
       a. Pro rebuts Con — once per factor
          → Gemini generates neutral summary_fact for each rebuttal
       b. Con rebuts Pro — once per factor
          → Gemini generates neutral summary_fact for each rebuttal
       c. Round Evaluator assesses the round (neutral, no bias):
          - New arguments introduced?
          - Going in circles?
          - Unresolved conflicts?
          → should_continue = true  → next round
          → should_continue = false → move to Cross Examination
        ↓

6. Cross Examination  [CrossExaminerAgent — Groq]
   - Has full visibility of all openings + all rebuttal rounds
   - Generates 3-5 sharp questions for Pro:
       - Probes contradictions across rounds
       - Targets unchallenged assumptions
       - Exposes gaps between claims and proof
   - Pro answers all questions (must be direct, can concede)
   - Generates 3-5 sharp questions for Con (same strategy)
   - Con answers all questions
        ↓

7. Closing Statements  [ProAgent + ConAgent — Groq]
   - Only runs if time_remaining > 60s
   - Pro closing:
       - Summarises strongest arguments that survived
       - Acknowledges valid points from Con
       - Reinforces final position
   - Con closing:
       - Same structure as Pro
        ↓

8. Synthesis  [SynthesizerAgent — Gemini primary / Groq fallback]
   - Reads everything:
       factors + openings + rebuttal summaries +
       cross-exam Q&A + closings + unresolved conflicts
   - Produces final DebateReport:
       pro_strongest_arguments
       con_strongest_arguments
       arguments_that_held_up
       arguments_that_collapsed
       concession_points
       debate_quality          →  High / Medium / Low
       confidence_score        →  0.0 to 1.0
                                  0.5  = perfectly balanced
                                  >0.5 = Pro made stronger case
                                  <0.5 = Con made stronger case
       verdict                 →  final answer (only if clearly decidable)
       what_worked
       what_failed
       why_it_happened
       how_to_improve
        ↓

9. Finalization
   - Full DebateState + report saved to MongoDB
   - User debate count incremented
   - Usage logged
   - phase → COMPLETED
   - Response returned to client
```

---

## MongoDB Collections

```
users         →  one document per user
sessions      →  one per login (TTL auto-deletes expired)
debates       →  one per debate (full state + embedded report)
events        →  many per debate (ordered event log)
usage_logs    →  one per action (debate_started, debate_completed)
```

---

## Time Budget Guide

```
300s   →  1 factor  →  ~3-4 min   →  may skip closing statements
600s   →  2 factors →  ~6-8 min   →  full flow completes
900s   →  3 factors →  ~10-12 min →  full flow comfortably
1200s  →  4 factors →  ~15-18 min →  full flow with room to spare
```