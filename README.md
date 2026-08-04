# PawPal+ AI

## Project Summary

**PawPal+** is a pet care planning system that helps an owner track care tasks across one or more pets and generate a daily schedule — ordered by time and flagged for scheduling conflicts. This repository extends that original system with **PawPal+ AI**, a natural-language question-answering layer that lets an owner ask about their existing pets and tasks in plain English instead of reading the schedule table directly.

## Problem Being Solved

A pet owner using PawPal+ already has all their pets' care tasks recorded, but answering a question like "What does Mochi still need today?" means scanning a schedule table by hand — checking every task's pet, time, and completion status. PawPal+ AI solves this by letting the owner just ask the question in plain English and get a direct answer, without giving up any of the reliability guarantees of the underlying scheduler: the AI layer cannot invent data, cannot change data, and cannot answer outside a fixed, safe scope. It also has to keep working — with a safe, still-useful answer — even if the AI provider is unreachable or misconfigured.

## Main AI Feature

PawPal+ AI is a **Retrieval-Augmented Generation (RAG)** feature: instead of asking Claude to answer freely from its own knowledge, the system first deterministically retrieves only the PawPal+ records relevant to the question, grounds Claude's prompt in exactly that data, and then validates Claude's answer against the same data before showing it to the user. The engineering discipline here — retrieval scoping, output validation, safe failure modes, and test coverage — is the point, not just the API call itself.

## Current Architecture

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

**Claude is the normal generation path.** For any supported question where retrieval finds matching data and an API key is configured, the pipeline calls Claude and — once the answer passes validation — shows that Claude-generated answer. This has been verified with a real, live Anthropic API call (see "How to verify Claude generated the answer" below and `execution_evidence.md` §0). The deterministic formatter in `validators.format_fallback_answer()` is the **backup path**: it activates only when retrieval finds no supported question type or no matching data, the Claude API key is missing, the API request fails, or the generated answer fails validation — never a raw error and never an unvalidated model response.

## Explanation of the RAG Pipeline

1. **Retrieval** (`retrieval.py`) — `detect_intent()` classifies the question into one of six supported intents using deterministic keyword/phrase matching (no LLM call, no ambiguity about what data can be seen). `detect_pet()` matches a pet's stored name as a case-insensitive substring of the question. `retrieve_context()` then pulls exactly the matching `Task` records from the owner's `Pet`/`Task` objects and formats them into a compact `context_text` string — never the full session state.
2. **Grounded generation** (`ai_assistant.py`) — `answer_question()` builds a user-turn prompt containing the question, the detected intent/pet, and that `context_text`, sends it to `client.messages.create()` alongside a system prompt that restricts Claude to that context, forbids veterinary advice, and forbids claiming to modify data, then extracts the response text.
3. **Validation** (`validators.py`) — `validate_answer()` deterministically re-checks the returned answer against the same retrieved records: does it claim to have taken an action, use veterinary diagnosis/treatment language, invent pet names/times/tasks not in the data, misstate whether a conflict exists, or contradict a task's actual completion status? Each issue found subtracts a fixed 0.34 from a confidence score starting at 1.0; the answer is only shown if zero issues were found.
4. **Deterministic fallback** (`validators.format_fallback_answer()`) — builds a plain, template-based answer directly from the same retrieved records, with no LLM involved. This is what's shown whenever step 1 finds nothing usable, step 2's API call fails or the key is missing, or step 3 rejects the answer.
5. **Logging** (`logger_config.py`) — every stage above logs its outcome (intent detected, retrieval outcome, Claude request attempted/succeeded, validation passed/failed, fallback used and why) to console and `logs/pawpal_ai.log`, without ever logging the API key, the full prompt, or the full question/answer text.

## Features

- Add and manage multiple pets and their care tasks.
- Generate daily schedules sorted by time.
- Filter tasks by pet or completion status (available via the backend API and demonstrated in the CLI demo; not yet exposed as its own control in the Streamlit UI).
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

## Guardrails

- **Read-only, always.** `ai_assistant.py` and `retrieval.py` have no code path that adds, deletes, completes, or reschedules a task. `validators.validate_answer()` additionally scans every Claude-generated answer for first-person claims of having taken such an action (e.g. "I marked the task complete") and routes any hit to the deterministic fallback, so even a confused or manipulated model output can't be shown as if it changed something.
- **No veterinary advice.** The system prompt explicitly forbids diagnosis, prescriptions, and treatment instructions. `validators.py` independently scans every answer for vet-specific phrases ("diagnosis", "prescribe", "give this medication", etc.) regardless of what the system prompt achieved, and falls back if any are found (unless the phrase is just part of an already-stored task description, e.g. a task literally named "Give medication").
- **Deterministic retrieval scope.** Intent and pet detection are plain string matching over a fixed set of six question types — there's no risk of accidentally retrieving or leaking data the question didn't ask about, because the retrieval surface is small, explicit, and decided entirely before any Claude call happens.
- **Fabrication and contradiction checks.** `validators.py` flags an answer that references specific-sounding data (times, capitalized proper nouns, conflict language) when retrieval found zero records, and flags an answer that states a task's completion status opposite to what was actually retrieved.
- **Unsupported questions never reach Claude.** Anything outside the six supported intents gets a fixed, safe message describing what PawPal+ AI can answer — Claude is never called.

## Deterministic Fallback

Whenever the Claude path can't produce a validated answer, `validators.format_fallback_answer()` builds one directly from the retrieved records — the same records that would have been sent to Claude — using plain string formatting with no model involved. This activates for: a blank question, an unsupported question, a supported question with no matching data, a missing `ANTHROPIC_API_KEY`, a failed or malformed Claude API response, or a Claude answer that fails validation. Every one of these resolves to a safe, readable answer — never a raw exception, and never an unvalidated model response reaching the user.

## Setup Instructions

### 1. Clone the repository

```bash
git clone <this-repo-url>
cd applied-ai-system-final
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs `streamlit`, `pytest`, `anthropic` (the official Anthropic Python SDK), and `python-dotenv`.

### 4. Set up your `.env` file securely

Copy the template and fill in your own values — **never** type a real key directly into a file you might commit:

```bash
cp .env.example .env
```

Then edit `.env` (which is already listed in `.gitignore` and will never be committed) to contain:

```bash
ANTHROPIC_API_KEY=your-real-api-key-here
ANTHROPIC_MODEL=claude-sonnet-5
```

**Required environment variables:**

| Variable | Required? | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | No — the app still runs and safely falls back without it | Anthropic API key used to construct the `anthropic.Anthropic()` client in `ai_assistant.py`. Read via `os.environ.get("ANTHROPIC_API_KEY")`. Never hardcoded anywhere in the codebase. |
| `ANTHROPIC_MODEL` | No — defaults to `ai_assistant.DEFAULT_MODEL` (`claude-haiku-4-5`) if unset | Overrides which Claude model is used for `client.messages.create()`. Any current, valid Claude model ID works (e.g. `claude-sonnet-5`, `claude-opus-5`, `claude-haiku-4-5`). |

> ⚠️ **Security warning: never commit your `.env` file.** It is already covered by `.gitignore` (`.env` and `.env.*`, with `.env.example` explicitly excluded from that pattern) — confirm with `git check-ignore .env` before committing anything if you're ever unsure. Only `.env.example`, which contains placeholder text and no real credentials, should ever be checked into version control. If a real key is ever accidentally committed, rotate it in the Anthropic Console immediately — removing it from a future commit does not remove it from git history.

`ai_assistant.py` calls `load_dotenv()` at import time (via `python-dotenv`), so values in `.env` are loaded automatically into the process environment — you do **not** need to manually `export` them into your shell first.

Without a configured `ANTHROPIC_API_KEY`, PawPal+ AI still runs — it automatically falls back to deterministic, template-built answers (`fallback_reason=missing_api_key`) instead of calling Claude. This is verified behavior, not a hypothetical: see `execution_evidence.md` §0.8 for a real test of this exact path.

## How to Run Streamlit

```bash
python3 -m streamlit run app.py
```

This starts a local Uvicorn server (default `http://localhost:8501`) and opens the PawPal+ UI in your browser.

## How to Run Tests

```bash
python3 -m pytest
```

For verbose per-test output:

```bash
python3 -m pytest -v
```

All 126 tests currently pass (`126 passed`) — see `execution_evidence.md` for the full recorded output.

## How to Use the Interface

1. **Add a pet** — fill in owner name, pet name, species, age, and comma-separated needs, then click **Add pet**. All fields are required; the form warns you and does not add the pet if any are missing.
2. **Add tasks** — once at least one pet exists, pick a pet, enter a task description and time, choose a frequency (daily/weekly/monthly), and click **Add task**.
3. **Generate a schedule** — click **Generate schedule** to see all tasks sorted by time, with any scheduling conflicts (two tasks at the same due date and time) called out as warnings.
4. **Ask PawPal+ AI** — expand "Example questions" for phrasing ideas, type a question about your pets/tasks into the text box, and click **Ask PawPal+ AI**. The answer, detected intent/pet, fallback status (if used), and validation confidence (if a Claude answer was generated) are all shown. Expand "Retrieved PawPal+ Context" to see exactly what data was retrieved and sent to Claude.
5. **Clear Everything** — check the confirmation box, then click **Clear Everything** to wipe all pets, tasks, and the last AI result from the current session and reload the page. The button is disabled until the confirmation box is checked.

## How to Verify That Claude Generated the Answer

Every result from `ai_assistant.answer_question()` is a dictionary with a `fallback_used` field. **`fallback_used=False` (shown in the UI as the absence of any fallback notice) means the displayed answer came from a real, validated Claude API response** — not a template. You can also check:

- `result["success"]` is `True` only when Claude was called, its response parsed, and validation passed.
- `result["validation_result"]` is populated (with `valid`, `confidence`, and `issues`) only after a real Claude response was validated — it is `None` on every fallback path, since there is nothing to validate.
- In the Streamlit UI, a **"Validation confidence: ..."** caption appears beneath the answer only when a Claude-generated answer was actually validated and shown.

This has been verified with a real API call: calling `answer_question("What tasks does Mochi have?", owner)` with a configured key and matching data returned `success=True`, `fallback_used=False`, and `validation_result["valid"]=True` with `confidence=1.0` (see `execution_evidence.md` §0.6 and `evaluation_results.md`).

## How to Recognize When Fallback Was Used

- `result["fallback_used"]` is `True`, and `result["fallback_reason"]` is one of the stable `ai_assistant.FALLBACK_*` constants: `blank_question`, `unsupported_question`, `no_context`, `missing_api_key`, `api_error`, `empty_response`, `response_parse_error`, or `validation_failed`.
- In the Streamlit UI, an info box reading **"PawPal+ used a deterministic answer based directly on retrieved records instead of an AI-generated answer (reason: ...)"** appears beneath the answer whenever this happens.
- `result["validation_result"]` is `None` on every fallback path (there's no Claude answer to have validated).

## Architecture Diagram

See [`diagrams/architecture.mmd`](diagrams/architecture.mmd) for the full Mermaid diagram of the implemented system.

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
- `evaluation_results.md` — test cases run against the pipeline for each supported question type and key edge cases, including a live-Claude-API run.
- `execution_evidence.md` — raw execution evidence (pytest output, syntax checks, Streamlit startup, live API call evidence, logs) backing `evaluation_results.md`.
- `model_card.md` — model card covering intended use, guardrails, reliability, and limitations of PawPal+ AI.
- `reflection.md` — design-decision write-up for the original scheduler and its evolution during implementation.
- `.env.example` — template for the two environment variables the app reads; copy to `.env` and fill in real values (never commit `.env`).

## Reliability

- **Automated tests**: the full suite (`tests/test_pawpal.py`, `test_retrieval.py`, `test_validators.py`, `test_ai_assistant.py`, `test_logger_config.py`) covers the core scheduler, intent/retrieval logic, fallback formatting, answer validation, the end-to-end assistant pipeline with a **mocked Claude client** (success, API failure, malformed response, and validation-triggered fallback), and logging behavior. See `execution_evidence.md` for the raw pytest run.
- **Live Claude API evaluation**: with a real `ANTHROPIC_API_KEY` configured, every supported question type was run against the real Anthropic API and returned a successful, validated, grounded answer; every edge case (unknown pet, blank question, unsupported question, missing key) correctly triggered the deterministic fallback without calling Claude. See `evaluation_results.md` → "Live API Evaluation" and `execution_evidence.md` §0.
- **Validation**: every Claude-generated answer is checked by `validators.validate_answer()` against the retrieved records before it can be shown to a user.
- **Fallback**: any unsupported question, missing data, missing API key, API error, or failed validation resolves to a deterministic, template-built answer rather than an error or an unvalidated response.
- **Logging**: each pipeline stage (intent detected, retrieval outcome, Claude request attempted/succeeded, validation result, fallback used and why) is logged to console and `logs/pawpal_ai.log`, without logging the API key, full prompts, or full question/answer text.
- **Human evaluation**: `evaluation_results.md` also preserves an earlier, pre-live-key evaluation that caught and fixed a real intent-detection bug in `retrieval.detect_intent()`, documented there alongside the fix (which is confirmed still present and working in the live evaluation).

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
- Conflict detection only matches tasks at the exact same `(due_date, time)` — tasks that meaningfully overlap but aren't scheduled at the identical minute are not flagged.

## Responsible AI

See [`model_card.md`](model_card.md) for the full model card: intended use, out-of-scope uses, model and data details, guardrails, privacy/security considerations, reliability evidence, limitations, and potential misuse considerations for PawPal+ AI.

## Future Improvements

- Expose existing backend filtering (by pet, by completion status) in the Streamlit UI, and add a "mark complete" control.
- Add true interval/duration-based conflict detection instead of exact `(due_date, time)` matching, so partially overlapping tasks are also flagged.
- Expand intent detection beyond fixed phrase matching (e.g., broader paraphrase coverage) while keeping the same deterministic-retrieval-then-validate architecture.
- Add automated (non-mocked) live-API smoke tests that run in CI with a securely injected key, so the live path is continuously verified rather than checked manually per audit.
