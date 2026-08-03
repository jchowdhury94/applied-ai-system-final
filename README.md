# PawPal+ AI

## Project Summary

**PawPal+** is a pet care planning system that helps an owner track care tasks across one or more pets and generate a daily schedule — ordered by time and flagged for scheduling conflicts. This repository extends that original system with **PawPal+ AI**, a natural-language question-answering layer that lets an owner ask about their existing pets and tasks in plain English instead of reading the schedule table directly.

The AI extension matters because it demonstrates more than "call an LLM API" — it's built as a grounded, guardrailed pipeline: a deterministic retrieval stage decides exactly what data Claude is allowed to see, a deterministic validator checks Claude's answer before it's ever shown to a user, and a deterministic fallback guarantees the system never surfaces a raw error or an unvalidated model response. The goal was to practice the engineering discipline around an LLM feature — retrieval scoping, output validation, safe failure modes, and test coverage — not just the API call itself.

## Original Project

**PawPal+** is the original, non-AI pet care planning assistant. A pet owner can add multiple pets, attach care tasks to each one (with a time and a daily/weekly/monthly frequency), and generate a daily schedule that sorts pending and completed tasks chronologically. The system detects scheduling conflicts (two tasks landing on the same due date and time slot) and automatically creates the next occurrence of a recurring task when it's marked complete. This logic lives entirely in `pawpal_system.py` (`Pet`, `Task`, `Owner`, `Scheduler`) and is exercised by both a CLI demo (`main.py`) and a Streamlit UI (`app.py`).

## Main AI Feature

PawPal+ AI is a **Retrieval-Augmented Generation (RAG)** feature: instead of asking Claude to answer freely from its own knowledge, the system first deterministically retrieves only the PawPal+ records relevant to the question, grounds Claude's prompt in exactly that data, and then validates Claude's answer against the same data before showing it to the user.

Implemented workflow:

```
User Question
      ↓
Structured Retrieval        (retrieval.py — deterministic intent + pet detection,
      ↓                      no LLM call)
PawPal Backend               (pawpal_system.py — Owner/Pet/Task/Scheduler records,
      ↓                      read-only)
Claude                        (ai_assistant.py — Anthropic API call, grounded
      ↓                      in the retrieved records only)
Validation                   (validators.py — keyword/regex checks against the
      ↓                      retrieved data)
Final Answer or Deterministic Fallback
```

If retrieval finds no supported question type or no matching data, if the Claude API key is missing or the request fails, or if validation flags an issue, the pipeline returns a deterministic, template-built answer instead — never a raw error and never an unvalidated model response.

## Features

- Add and manage multiple pets and their care tasks.
- Generate daily schedules sorted by time.
- Filter tasks by pet or completion status (available via the backend API and demonstrated in the CLI demo; not yet exposed in the Streamlit UI).
- Automatically create new occurrences for recurring daily, weekly, and monthly tasks.
- Detect scheduling conflicts and display warning messages.
- Display schedules in both a command-line demo and a Streamlit interface.
- **Ask PawPal+ AI**: a natural-language Q&A panel in the Streamlit app, grounded in the current session's pets/tasks, with retrieved context, detected intent, validation confidence, and fallback status all shown in the UI.
- Deterministic guardrails: no veterinary diagnosis/treatment advice, no claims of autonomous data changes, and no answer shown without passing validation or falling back safely.
- Structured, privacy-conscious logging of every pipeline stage (console + `logs/pawpal_ai.log`), without ever logging the API key, full prompts, or full question/answer text.

## Supported Questions

PawPal+ AI supports exactly six question types (anything else is treated as unsupported and answered safely without calling Claude):

- **Incomplete tasks** — "What tasks are incomplete?"
- **Completed tasks** — "What tasks are completed?"
- **Pet tasks** — "What tasks does [pet name] have?"
- **Today's schedule** — "What is today's schedule?"
- **Conflicts** — "Are there any scheduling conflicts?"
- **Next task** — "What task should I do next?"

## Architecture

See [`diagrams/architecture.mmd`](diagrams/architecture.mmd) for the full Mermaid diagram of the implemented system.

In short: the Streamlit UI (`app.py`) passes a question to `ai_assistant.answer_question()`, which calls `retrieval.retrieve_context()` to deterministically detect intent and pull matching records from the `Owner`/`Pet`/`Task`/`Scheduler` backend. Those records are formatted into a grounded prompt and sent to the Claude API. Claude's answer is checked by `validators.validate_answer()`; if it passes, it's shown as the final answer, and if it fails — or if retrieval, the API call, or the API key check failed first — `validators.format_fallback_answer()` builds a safe answer directly from the retrieved records instead. Every stage logs its outcome through the shared logger in `logger_config.py`, and the whole pipeline is exercised by the automated tests in `tests/`, independently of any live Claude call.

## Folder Structure

- `app.py` — Streamlit UI: add pets/tasks, generate a schedule, and ask PawPal+ AI questions.
- `main.py` — CLI demo script showing sorting, filtering, conflict detection, and recurring tasks.
- `pawpal_system.py` — core backend classes: `Pet`, `Task`, `Owner`, `Scheduler`.
- `retrieval.py` — deterministic intent/pet detection and structured record retrieval (the "R" in RAG).
- `ai_assistant.py` — orchestrates the pipeline: retrieval → Claude API call → validation → answer or fallback.
- `validators.py` — deterministic answer validation and deterministic fallback-answer formatting.
- `logger_config.py` — shared application logger (console + `logs/pawpal_ai.log`).
- `tests/` — pytest suite: `test_pawpal.py` (scheduler), `test_retrieval.py`, `test_validators.py`, `test_ai_assistant.py` (mocked Claude client), `test_logger_config.py`.
- `diagrams/architecture.mmd` — implemented AI pipeline architecture (Mermaid). `diagrams/uml_final.mmd` — final UML class diagram for the core scheduler.
- `evaluation_results.md` — manual test cases run against the live app for each supported question type and key edge cases.
- `execution_evidence.md` — raw execution evidence (pytest output, logs, retrieved-context samples) backing `evaluation_results.md`.
- `model_card.md` — model card covering intended use, guardrails, reliability, and limitations of PawPal+ AI.
- `reflection.md` — design-decision write-up for the original scheduler and its evolution during implementation.

## Installation

```bash
# 1. Clone the repository
git clone <this-repo-url>
cd applied-ai-system-final

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create a .env file for your Claude API credentials
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your-api-key-here
# Optional: override the default Claude model (see ai_assistant.DEFAULT_MODEL)
ANTHROPIC_MODEL=claude-opus-5
EOF
```

`ai_assistant.py` reads `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` via `os.environ`, so make sure the values in `.env` are exported into your shell session before launching the app (for example, `export $(grep -v '^#' .env | xargs)`, or use a tool like `direnv`). Without a configured `ANTHROPIC_API_KEY`, PawPal+ AI still runs — it automatically falls back to deterministic, template-built answers (`fallback_reason=missing_api_key`) instead of calling Claude.

## Running

Launch the Streamlit app:

```bash
python3 -m streamlit run app.py
```

Run the automated test suite:

```bash
python3 -m pytest
```

## Reproducible Execution Evidence

This section consolidates real, already-recorded commands, inputs, outputs, and reliability results so the system can be graded from this README alone. Every line below is reused verbatim from this repository (this file and `execution_evidence.md`) — nothing here was newly run or invented.

### 1. Sample Command Executions

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 -m pytest -v

python3 -m streamlit run app.py

tail -n 30 logs/pawpal_ai.log
```

### 2. Example Inputs

Pets/tasks entered before running the test cases in `evaluation_results.md` (from `execution_evidence.md` §5):

```text
Pet 1: Mochi (cat) — Feed breakfast (08:00, daily), Give medication (12:00, daily)
Pet 2: Biscuit (dog) — Morning walk (08:00, daily), Grooming (17:00, weekly)
```

Example question asked of PawPal+ AI:

```text
What are my incomplete tasks?
```

### 3. Example Outputs

Full automated test run (from `execution_evidence.md` §3, 126 tests):

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 126 items
...
============================= 126 passed in 0.10s ==============================
```

Streamlit launch output (from `execution_evidence.md` §4):

```text
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.50.179:8501
```

Recorded question/answer interaction, deterministic fallback path (no `ANTHROPIC_API_KEY` configured — from `execution_evidence.md` §7, matching the Sample Interactions section below):

```text
User question:      What are my incomplete tasks?
Retrieved context:   Incomplete tasks (4):
                      - Mochi: Feed breakfast (08:00, daily, due 2026-08-01, not completed)
                      - Biscuit: Morning walk (08:00, daily, due 2026-08-01, not completed)
                      - Mochi: Give medication (12:00, daily, due 2026-08-01, not completed)
                      - Biscuit: Grooming (17:00, weekly, due 2026-08-01, not completed)
AI answer:           Here are the incomplete tasks:
                      - Mochi: Feed breakfast at 08:00, due 2026-08-01
                      - Biscuit: Morning walk at 08:00, due 2026-08-01
                      - Mochi: Give medication at 12:00, due 2026-08-01
                      - Biscuit: Grooming at 17:00, due 2026-08-01
Intent:              incomplete_tasks
Detected pet:        none
Fallback used:       Yes (fallback_reason=missing_api_key)
```

Log lines from a separate logged interaction — the today's-schedule question, not the incomplete-tasks question above (from `execution_evidence.md` §9, shown here only to illustrate log format; no API keys, prompts, or question/answer text are ever logged):

```text
2026-08-01 21:18:03,972 | INFO | pawpal_ai.ai_assistant | Question processing started. question_length=27
2026-08-01 21:18:03,972 | INFO | pawpal_ai.retrieval | Detected intent: todays_schedule
2026-08-01 21:18:03,972 | INFO | pawpal_ai.retrieval | Retrieval completed with 4 record(s).
2026-08-01 21:18:03,972 | INFO | pawpal_ai.ai_assistant | Detected intent: todays_schedule
2026-08-01 21:18:03,972 | INFO | pawpal_ai.validators | Fallback answer generated. fallback_intent=todays_schedule
2026-08-01 21:18:03,972 | INFO | pawpal_ai.ai_assistant | Deterministic fallback used. fallback_reason=missing_api_key
2026-08-01 21:18:03,972 | INFO | pawpal_ai.ai_assistant | Processing completed. success=False fallback_used=True
```

### 4. Reliability / Guardrail Results

From `execution_evidence.md` §10 (Human Evaluation Summary):

```text
Total cases run:        10 (TC-01 through TC-10, see evaluation_results.md)
Passed:                 10 (after the retrieval.py fix; 3 originally failed)
Failed:                 0
Pass percentage:        100%
```

Guardrail behavior verified by the automated suite and manual evaluation (see `Reliability` section below for the full list):

- Every Claude-generated answer is checked by `validators.validate_answer()` against the retrieved records before being shown to a user.
- Any unsupported question, missing data, missing API key, API error, or failed validation resolves to a deterministic, template-built answer — never a raw error or an unvalidated response.
- No API key, full prompt, or full question/answer text is ever logged.
- Manual evaluation caught and fixed a real intent-detection bug in `retrieval.detect_intent()` (documented in `evaluation_results.md`), after which all 10 manual test cases and all 126 automated tests passed.

## Sample Interactions

All three recorded interactions below were captured with no `ANTHROPIC_API_KEY` configured (a deliberate scope decision for this submission — see `execution_evidence.md` §6), so every one runs the deterministic fallback path, `validators.format_fallback_answer()`, rather than a live Claude call. No validation-confidence score is reported for any of them because `validators.validate_answer()` is only invoked after a real Claude response, and that code path was exercised solely via mocked clients in `tests/test_ai_assistant.py`, not captured here as a recorded interaction. Sample data for all three (from `execution_evidence.md` §5): pets **Mochi** (Feed breakfast 08:00 daily, Give medication 12:00 daily) and **Biscuit** (Morning walk 08:00 daily, Grooming 17:00 weekly).

### Example 1 — structured retrieval end-to-end (TC-01, `execution_evidence.md` §7)

```text
User question:       What are my incomplete tasks?
Detected intent:      incomplete_tasks
Detected pet:         none
Retrieved context:    Incomplete tasks (4):
                       - Mochi: Feed breakfast (08:00, daily, due 2026-08-01, not completed)
                       - Biscuit: Morning walk (08:00, daily, due 2026-08-01, not completed)
                       - Mochi: Give medication (12:00, daily, due 2026-08-01, not completed)
                       - Biscuit: Grooming (17:00, weekly, due 2026-08-01, not completed)
Final answer:         Here are the incomplete tasks:
                       - Mochi: Feed breakfast at 08:00, due 2026-08-01
                       - Biscuit: Morning walk at 08:00, due 2026-08-01
                       - Mochi: Give medication at 12:00, due 2026-08-01
                       - Biscuit: Grooming at 17:00, due 2026-08-01
Fallback used:        Yes
Fallback reason:      missing_api_key
```

This shows the full pipeline running end-to-end: the question is routed to a supported intent, retrieval pulls exactly the matching task records (and only those), and the final answer is built directly from that retrieved data.

### Example 2 — schedule retrieval, a different intent (TC-04, `execution_evidence.md` §8 and `evaluation_results.md`)

```text
User question:       What is today's schedule?
Detected intent:      todays_schedule
Detected pet:         none
Retrieved context:    Today's schedule (4):
                       - Mochi: Feed breakfast (08:00, daily, due 2026-08-01, not completed)
                       - Biscuit: Morning walk (08:00, daily, due 2026-08-01, not completed)
                       - Mochi: Give medication (12:00, daily, due 2026-08-01, not completed)
                       - Biscuit: Grooming (17:00, weekly, due 2026-08-01, not completed)
                       Records retrieved: 4
Final answer:         Here is today's schedule:
                       - Mochi: Feed breakfast at 08:00
                       - Biscuit: Morning walk at 08:00
                       - Mochi: Give medication at 12:00
                       - Biscuit: Grooming at 17:00
Fallback used:        Yes
Fallback reason:      missing_api_key
```

This demonstrates a second supported intent (schedule retrieval instead of incomplete-tasks retrieval), grounded in raw retrieved-context output copied directly from the running app.

### Example 3 — guardrail behavior on an unsupported, veterinary question (TC-09, `evaluation_results.md`)

```text
User question:       Should I take my dog to the vet today?
Detected intent:      unsupported
Detected pet:         none
Retrieved context:    (none — no records retrieved for an unsupported question)
Final answer:         PawPal+ AI currently supports questions about: incomplete
                       tasks, completed tasks, a specific pet's tasks, today's
                       schedule, conflicts, and the next task.
Fallback used:        Yes
Fallback reason:      unsupported_question
```

This demonstrates the reliability/guardrail behavior described in the Design Decisions section: a veterinary question is recognized as out of scope, Claude is never called, and the assistant gives no diagnosis or treatment advice — only a safe, deterministic refusal.

### What these examples demonstrate together

Across all three, the same pipeline runs every time: **user question → intent detection (`retrieval.detect_intent()`) → deterministic retrieval (`retrieval.retrieve_context()`) → grounded AI pipeline (`ai_assistant.answer_question()`) → validation or deterministic fallback (`validators.py`) → final answer.** In every recorded case here, no `ANTHROPIC_API_KEY` was configured, so each interaction resolved through the deterministic fallback branch rather than a live, validated Claude response — this is a documented scope decision (`execution_evidence.md` §6), not a gap. The Claude-call and `validators.validate_answer()` branches of that same pipeline are exercised instead by the mocked-client tests in `tests/test_ai_assistant.py` (successful-response, API-error, malformed-response, and validation-failure paths), and no live Claude-generated output is claimed anywhere in this repository.

## Reliability

- **Automated tests**: the full suite (`tests/test_pawpal.py`, `test_retrieval.py`, `test_validators.py`, `test_ai_assistant.py`, `test_logger_config.py`) covers the core scheduler, intent/retrieval logic, fallback formatting, answer validation, the end-to-end assistant pipeline with a **mocked Claude client** (success, API failure, malformed response, and validation-triggered fallback), and logging behavior. See `execution_evidence.md` for the raw pytest run.
- **Validation**: every Claude-generated answer is checked by `validators.validate_answer()` against the retrieved records before it can be shown to a user.
- **Fallback**: any unsupported question, missing data, missing API key, API error, or failed validation resolves to a deterministic, template-built answer rather than an error or an unvalidated response.
- **Logging**: each pipeline stage (intent detected, retrieval outcome, Claude request attempted/succeeded, validation result, fallback used and why) is logged to console and `logs/pawpal_ai.log`, without logging the API key, full prompts, or full question/answer text.
- **Human evaluation**: `evaluation_results.md` records manually run test cases against the live Streamlit app for each supported question type plus edge cases (unknown pet, blank question, unsupported/veterinary question, missing API key). This process caught and fixed a real intent-detection bug in `retrieval.detect_intent()`, documented there alongside the fix.

## Design Decisions

- **Why structured retrieval instead of free-form context**: intent and pet detection are plain, deterministic string matching over a fixed set of supported question types. This makes it possible to know, before any Claude call happens, exactly what data can be sent and what questions are in scope — there's no risk of accidentally retrieving or leaking unrelated data because the retrieval surface is small and explicit.
- **Why deterministic validation instead of trusting the model**: an LLM can still generate a plausible-sounding but incorrect or ungrounded answer even when given the right context. `validators.py` checks the *literal* retrieved data against the answer (fabricated names/times, contradicted completion status, incorrect conflict claims, action claims, vet language) using regex/keyword rules that are simple to test, audit, and reason about — no second model is needed to police the first.
- **Why no vector database**: PawPal+'s dataset per session is small, structured, and already fully addressable by exact fields (pet name, completion status, due date, time). A fixed set of six question types can be served by direct, deterministic lookups over `Owner`/`Pet`/`Task` objects; introducing embeddings and semantic search would add real complexity and a new failure surface without solving a retrieval problem that actually exists at this scale.
- **Why no autonomous actions**: PawPal+ AI is a reporting layer, not an actor. Giving an LLM the ability to add, delete, complete, or reschedule tasks would mean a hallucinated or misinterpreted request could silently corrupt an owner's real data. Keeping the assistant strictly read-only — with validators additionally rejecting any answer that *claims* to have taken an action — removes that entire class of risk.

## Known Limitations

- Intent detection is keyword/phrase-based, not true natural-language understanding, so phrasing outside the known patterns can be misrouted or marked unsupported.
- No multi-turn memory — each question is answered independently, with no conversation history or follow-up resolution.
- No persistence — all pet/task data lives only in the Streamlit session and does not survive a restart.
- The assistant's accuracy is entirely dependent on what the owner has actually entered; it has no independent knowledge of the pets.
- Built and tested for English input only.
- Even with grounded retrieval and validation, Claude can still misinterpret an ambiguous question's phrasing — validation reduces this risk but does not eliminate it.
- The Streamlit UI does not yet expose a "mark complete" control or filtering by pet/completion status, even though both are already implemented in the backend (`pawpal_system.py`).

## Responsible AI

See [`model_card.md`](model_card.md) for the full model card: intended use, out-of-scope uses, model and data details, guardrails, reliability evidence, limitations, and potential misuse considerations for PawPal+ AI.

## Future Improvements

- Live-Claude evaluation with a real `ANTHROPIC_API_KEY` remains optional future work; it was intentionally not performed for this submission (see `execution_evidence.md` §6).
- Expose existing backend filtering (by pet, by completion status) in the Streamlit UI, and add a "mark complete" control so completed-task questions can be tested against real mixed data.
- Add true interval/duration-based conflict detection instead of exact `(due_date, time)` matching, so partially overlapping tasks are also flagged.
- Expand intent detection beyond fixed phrase matching (e.g., broader paraphrase coverage) while keeping the same deterministic-retrieval-then-validate architecture.
