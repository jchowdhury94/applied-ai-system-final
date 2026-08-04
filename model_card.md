# PawPal+ AI Model Card

## System Overview

**PawPal+** began as a deterministic pet care planning system: a set of Python classes (`Pet`, `Task`, `Owner`, `Scheduler` in `pawpal_system.py`) that let an owner track care tasks across one or more pets, generate a chronologically ordered daily schedule, detect scheduling conflicts, and automatically regenerate recurring daily/weekly tasks on completion. This core logic contains no AI and is fully covered by its own pytest suite (`tests/test_pawpal.py`).

The **final project** extends PawPal+ with a natural-language question-answering layer, **PawPal+ AI**, exposed through the "Ask PawPal+ AI" panel in the Streamlit app (`app.py`). This layer lets an owner ask questions about their existing pets and tasks in plain English instead of reading the schedule table directly. It is strictly read-only: it cannot add, delete, complete, or reschedule anything, and it never mutates `Owner`, `Pet`, `Task`, or `Scheduler` state.

PawPal+ AI is built as a **Retrieval-Augmented Generation (RAG)** pipeline rather than a system that lets a language model answer freely:

1. **Retrieval** (`retrieval.py`) — deterministically classifies the question into one of a fixed set of supported intents (keyword/phrase matching, no LLM call), identifies which pet (if any) the question refers to, and pulls only the matching `Pet`/`Task` records already stored in the session's `Owner` object.
2. **Grounded generation** (`ai_assistant.py`) — sends the retrieved records, not the full dataset and not the raw session state, to the Claude API as context, along with a system prompt that restricts Claude to that context.
3. **Validation** (`validators.py`) — deterministically checks Claude's answer against the same retrieved records for fabricated facts, contradicted completion states, incorrect conflict claims, veterinary language, and claims that the assistant took an action.
4. **Deterministic fallback** (`validators.format_fallback_answer`) — if retrieval finds no supported intent, no data, no configured API key, an API failure, or a validation failure, the system falls back to a plain, template-generated answer built directly from the retrieved records instead of an AI-generated one. No user-facing path in this system can return an unvalidated Claude answer.
5. **Logging** (`logger_config.py`) — every stage of the pipeline (intent detected, retrieval outcome, Claude request attempted/succeeded, validation passed/failed, fallback used and why) is logged to console and to `logs/pawpal_ai.log` through a single shared logger, without ever logging the API key, the full prompt, or full question/answer content.

## Intended Use

PawPal+ AI is designed to let an owner query the pet care data **already stored in their own PawPal+ session** using natural language, as a convenience layer on top of the deterministic scheduler. It supports exactly six question types, detected by `retrieval.detect_intent()`:

- **Incomplete tasks** — "What tasks are incomplete?"
- **Completed tasks** — "What tasks are completed?"
- **Pet tasks** — "What tasks does [pet name] have?"
- **Today's schedule** — "What is today's schedule?"
- **Conflicts** — "Are there any scheduling conflicts?"
- **Next task** — "What task should I do next?"

Any question that does not match one of these intents is treated as unsupported and answered with a fixed, safe message listing the supported question types — it is never passed to Claude.

## Out-of-Scope Use

PawPal+ AI is **not** intended for:

- **Veterinary diagnosis or treatment advice.** The system prompt explicitly forbids this, and `validators.py` scans answers for diagnosis/prescription/dosage language and routes any hit to the deterministic fallback.
- **Emergency decisions.** PawPal+ AI has no awareness of urgency or medical risk and must never be relied on for time-sensitive or safety-critical decisions about an animal's health.
- **Modifying task data.** The assistant cannot add, delete, complete, or reschedule tasks under any circumstances. It has no write path into `Owner`/`Pet`/`Task`/`Scheduler`, and `validators.py` additionally flags any answer that *claims* to have performed such an action so that claim is never shown to the user as a real answer.
- **Unrelated questions.** Anything outside the six supported intents (general chit-chat, unrelated factual questions, etc.) is refused via the unsupported-question fallback rather than answered.
- **Autonomous planning.** PawPal+ AI does not decide what an owner should do, prioritize tasks, or take initiative — it only reports on data that already exists as a result of the owner's own inputs.

## AI Model

- **Provider and model ID:** Claude, from Anthropic, accessed via the **Anthropic API** (`anthropic` Python SDK, `client.messages.create`). The API key is read from the `ANTHROPIC_API_KEY` environment variable and the model ID from `ANTHROPIC_MODEL` (both loaded from `.env` via `python-dotenv`); neither is ever hardcoded. `ai_assistant.DEFAULT_MODEL` (`claude-haiku-4-5`) is the fallback used only when `ANTHROPIC_MODEL` is unset. **Verified live** on 2026-08-04 with `ANTHROPIC_MODEL=claude-sonnet-5` — a real Claude Sonnet 5 API call succeeded end-to-end (`success=True`, `fallback_used=False`, `validation_result.valid=True`; see `execution_evidence.md` §0.6). The model resolution order (function parameter → `ANTHROPIC_MODEL` → `DEFAULT_MODEL`) means the exact model in use is always a deployment-time or call-time configuration choice, never buried application logic.
- **No fine-tuning.** Claude is used purely as a general-purpose, off-the-shelf model called through the standard Messages API. No training, fine-tuning, or model customization is performed anywhere in this project.
- **Purpose of the model:** generate a natural-language answer to a scope-limited pet-care question, using only the structured records `retrieval.py` has already decided are relevant. Claude's job is narrowly *phrasing and light synthesis of already-retrieved facts* — it is never the source of what data exists, never allowed to decide what data to look at, and never given write access to any PawPal+ object.
- **Structured retrieval, not open-ended search.** The "R" in this RAG pipeline is not a vector database or semantic search — it is deterministic, structured retrieval over the existing in-memory `Owner`/`Pet`/`Task` objects, keyed by an intent classified with plain string matching.
- **Deterministic validation.** Claude's output is never trusted directly. Every generated answer passes through `validators.validate_answer()`, a rules-based (regex/keyword) checker with no model of its own, before it can be shown to the user.

## Data Used

Claude only ever receives the **compact text context** (`context_text`) built by `retrieval.py` from the records matching the detected intent — never the full `Owner` object, never data for other intents, and never data beyond what the question asked about. Depending on intent, this context can include:

- Pet name(s) associated with each task
- Task descriptions
- Task times and due dates
- Task frequency (daily, weekly, monthly)
- Completion status (completed / not completed)
- Scheduling conflicts (grouped tasks sharing the same due date and time slot)

This data comes entirely from what the owner has already entered into their own Streamlit session (`st.session_state.owner`) — PawPal+ AI has no external data source, no persistent database, and no access to other users' data. If retrieval finds no supported intent or no matching records, no context is sent to Claude at all and the system falls back immediately.

## Privacy and Security Considerations

- **No secrets in code or version control.** `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` are read from environment variables (via `.env`, loaded by `python-dotenv`) and never hardcoded anywhere in `ai_assistant.py` or elsewhere. `.env` is listed in `.gitignore` (along with `.env.*`, with `.env.example` explicitly un-ignored) and is confirmed excluded from version control (`git check-ignore .env`). Only `.env.example`, containing placeholder values, is committed.
- **No secrets in logs.** `logger_config.py`'s shared logger never receives the API key, the full prompt sent to Claude, or the full question/answer text — only structured metadata (intent, fallback reason, pass/fail outcomes, question length). This is enforced by dedicated tests (`test_api_keys_do_not_appear_in_captured_logs`, `test_full_prompt_and_context_not_logged`, `test_api_key_never_appears_in_returned_errors`).
- **No secrets in error messages.** Exception handling in `ai_assistant.py` logs only the exception's type name (`type(exc).__name__`), never the exception's message or arguments, which could otherwise echo back request details.
- **No persistence beyond the session.** All pet/task data lives only in `st.session_state.owner` for the duration of one browser session; nothing is written to disk or a database, so there is no data-at-rest exposure to protect.
- **Least data sent to the model.** Only the `context_text` for the detected intent is sent to Claude — never the full `Owner` object, never other users' data (there is no multi-user state to begin with), and never the API key itself (which lives only in the SDK client's auth header, not in any prompt content).

## Guardrails

- **Deterministic retrieval.** Intent classification and pet detection are plain string/keyword matching with no LLM involved, so the *scope* of what Claude can be asked about is fixed and auditable before any API call happens.
- **Validation.** `validators.validate_answer()` checks every generated answer for: claims that the assistant performed a data-changing action, veterinary diagnosis/treatment language, incorrect claims about the presence or absence of scheduling conflicts, and contradictions of a task's actual completion status. It also flags an answer as fabricated when it references a pet or task despite retrieval finding **zero** matching records for the intent (`validators._looks_fabricated`) — this check does not re-verify every individual detail (name, time, conflict) of an answer against a non-empty set of retrieved records, so a generated answer could in principle add a plausible-but-wrong detail (e.g. a slightly wrong time) alongside otherwise-correct records without being caught by this specific rule. Any issue that *is* detected triggers the fallback.
- **Unsupported-question handling.** Questions outside the six supported intents never reach Claude; they receive a fixed, safe message describing what PawPal+ AI can answer.
- **No autonomous task changes.** The assistant has no code path capable of adding, deleting, completing, or rescheduling tasks — `ai_assistant.py` and `retrieval.py` are documented and tested as read-only, and the Streamlit UI's rendering function (`_render_ai_result`) only reads from the result dictionary.
- **Deterministic fallback.** Any failure mode — blank question, unsupported question, no matching records, missing API key, API error, empty/malformed response, or failed validation — resolves to a template-generated answer built directly from retrieved records (or a fixed safe message), never a raw error or an unvalidated model output.
- **Logging.** Every stage of the pipeline is logged with stable, structured messages (intent, fallback reason, pass/fail outcomes) for traceability, while explicitly avoiding logging the API key, full prompts, or full question/answer text.

## Reliability

Reliability evidence comes from three sources documented in this repository:

- **Automated tests, including mocked API tests.** The full suite (126 tests, per `execution_evidence.md`) covers the deterministic scheduler (`tests/test_pawpal.py`), intent/retrieval logic (`tests/test_retrieval.py`), fallback formatting and answer validation (`tests/test_validators.py`), logging behavior (`tests/test_logger_config.py`), and the end-to-end assistant pipeline (`tests/test_ai_assistant.py`) — the latter using a mocked Claude client so success paths, API failures, malformed responses, and validation-triggered fallbacks are all exercised without depending on a live API key. All 126 tests pass (`python -m pytest`, re-verified 2026-08-04).
- **Live Claude API evaluation (2026-08-04).** With a real `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL=claude-sonnet-5` configured, `ai_assistant.answer_question()` was called directly (the same function the Streamlit UI calls) for every supported intent plus edge cases. Every case where retrieval found matching records made a real Claude API call and returned `success=True`, `fallback_used=False`, `validation_result.valid=True` with a fully grounded answer; every case without matching data, with an unsupported question, or with a missing key correctly triggered the deterministic fallback without ever calling Claude. See `evaluation_results.md` → "Live API Evaluation" and `execution_evidence.md` §0 for full details, including a missing-key fallback test run separately (without touching the real `.env` file) that confirmed `fallback_reason=missing_api_key`.
- **Historical human evaluation.** `evaluation_results.md` also preserves 10 manually run test cases from 2026-08-01 (before a live key was available), covering each supported intent plus edge cases. That process caught and fixed a real intent-detection bug (`retrieval.detect_intent()` missing certain word orders for "incomplete" and "next"); all 10 cases passed after the fix, and the fix is confirmed still present and working in the 2026-08-04 live evaluation above.
- **Deterministic fallback as a reliability mechanism.** Because every non-nominal condition (including any Claude API failure or validation failure) resolves to a deterministic, template-based answer rather than a crash or an unchecked model response, the system has no failure mode that surfaces raw errors or unvalidated output to the user.

Claude is the **normal generation path** for any supported question with matching data and a configured API key — this is now verified with a real, successful live call, not a hypothetical. The deterministic formatter in `validators.format_fallback_answer()` is the **backup path**, used only when retrieval finds no supported intent or no data, the API key is missing, the API call fails, or validation rejects the generated answer.

## Limitations

- **Keyword-based intent detection.** `retrieval.detect_intent()` uses fixed phrase and keyword matching rather than true natural-language understanding, so phrasing outside its known patterns can be misrouted or marked unsupported even when a human would recognize the intent.
- **No multi-turn memory.** Each question is answered independently; PawPal+ AI does not track conversation history or resolve references to earlier questions ("what about tomorrow?").
- **No persistence.** All pet/task data lives only in the Streamlit session (`st.session_state.owner`); nothing is saved to disk or a database, so data does not survive a session restart.
- **Depends entirely on user-entered data.** PawPal+ AI has no independent knowledge of the user's pets — it can only be as accurate, complete, or up to date as what the owner has entered into the app.
- **English only.** Intent phrases, pet-name matching, and the system prompt are all written for English input; behavior on other languages is untested and unsupported.
- **Claude may still misunderstand ambiguous questions.** Even when retrieval correctly finds a supported intent and relevant records, Claude's phrasing of the answer is generative and could misinterpret nuance in the question; this risk is mitigated, not eliminated, by `validators.validate_answer()`.

## Biases

PawPal+ AI does not reason about any protected or demographic attribute — its entire dataset is pet names, task descriptions, times, frequencies, and completion flags typed in by a single owner, so classic demographic bias categories do not apply here. The biases that do exist are structural, coming from how the deterministic layers were built and what data they see:

- **Data-entry bias.** The assistant only knows what the owner has typed in. A pet whose tasks are logged in detail will be well-represented in every answer; a pet the owner tracks loosely (fewer tasks, vaguer descriptions) will appear thin or absent in responses, even if that pet's real-world care needs are just as significant. PawPal+ AI has no way to detect or correct for this — it reports the data as entered, not as it "should" be.
- **English-and-phrasing bias in intent detection.** `retrieval.detect_intent()` and `detect_pet()` are keyword/substring matching authored around a specific set of expected English phrasings (see Limitations). Questions phrased the way the developer anticipated are recognized; equally valid questions phrased differently, in a different dialect, or in another language are more likely to be marked unsupported. This is a bias toward the phrasing patterns the keyword list happens to cover, not a deliberate design choice to exclude any group.
- **Ordering/tie-break bias.** Task lists are produced with Python's `sorted()`, which is stable (`pawpal_system._time_sort_key`, used in `pawpal_system.py` and `retrieval.py`). When two tasks share the same time, the one entered earlier in the session consistently sorts first in schedules and in "next task" answers. This gives a small, systematic edge to whichever pet or task the owner happened to add first, rather than reflecting any meaningful priority.

None of these biases involve people-facing attributes (race, gender, age, etc.) since the system has no such data; they are limited to how faithfully and evenly the assistant represents the owner's own pet-care data.

## Potential Misuse

A user could attempt to use PawPal+ AI outside its intended scope — for example, asking it for veterinary advice, trying to phrase a request as if it could change task data ("mark this complete"), or asking unrelated questions expecting a general-purpose chatbot. The guardrails in this system reduce that risk at multiple layers: the system prompt instructs Claude never to give veterinary diagnosis/treatment advice and never to claim it can modify data; `validators.py` independently scans every generated answer for veterinary language and action claims regardless of what Claude actually said; unsupported questions never reach Claude at all; and the assistant has no underlying write capability to `Owner`/`Pet`/`Task`/`Scheduler`, so even a successfully "tricked" answer could not actually change any data. The combination of a narrow, deterministic retrieval scope and independent output validation means misuse is limited to receiving an unhelpful or refused answer, not an unsafe or destructive action.

## AI Collaboration

PawPal+ AI was built with AI assistance throughout the design and implementation of `retrieval.py`, `ai_assistant.py`, `validators.py`, and `logger_config.py`, on top of the pre-existing deterministic `pawpal_system.py`. AI suggestions were used to speed up design and boilerplate, but every suggestion was checked against the automated test suite and read through in review before being accepted, rather than being merged on trust.

**One helpful AI suggestion:**

> AI suggested splitting the natural-language question-answering feature into five separate concerns instead of one combined function: structured retrieval (`retrieval.py`), Claude orchestration (`ai_assistant.py`), deterministic answer validation (`validators.py`), a deterministic fallback path (`validators.format_fallback_answer`), and privacy-conscious logging (`logger_config.py`). This was genuinely helpful because it made each piece independently testable — retrieval, validation, and fallback formatting could all be unit-tested with plain Python data and no API key or mocking (`tests/test_retrieval.py`, `tests/test_validators.py`), while only the Claude call itself needed a mocked client (`tests/test_ai_assistant.py`). It also kept the AI layer strictly read-only by construction: because intent classification and record retrieval happen entirely in deterministic code *before* Claude is ever called, there was never a code path where Claude's output could influence what data got retrieved or expand its own access to the session.

**One flawed AI suggestion:**

> Early in development, an AI suggestion for the Claude API call used an unverified, unsuitable default model identifier hardcoded directly in `ai_assistant.py` rather than a real, documented model name. This was caught during code review before finalization, not accepted as-is. The fix was to centralize the model name in a single `ai_assistant.DEFAULT_MODEL` constant, document it, and make it overridable via the `ANTHROPIC_MODEL` environment variable or a function parameter (`ai_assistant.py`, see "AI Model" above), so the exact model in use is an explicit, reviewable deployment choice instead of an unverified string buried in application logic. More generally, AI-generated code in this project was never accepted blindly: every suggestion was run against the pytest suite and read through manually, and functionality was only considered done once the corresponding tests passed and the code was reviewed line by line.

## Reflection

1. **What limitations or biases exist in the system?** PawPal+ AI's intent detection (`retrieval.detect_intent()`) is keyword/phrase-based rather than a true NLU model, so phrasing outside its known patterns can be misrouted or marked unsupported even when a human would understand the question — this is a real, observed limitation, not a hypothetical one (see the reliability-testing surprise below). Pet-name matching is substring-based, which can misfire on pet names that are substrings of each other or of common words. The system has no persistence (all data lives only in `st.session_state.owner` for the duration of one browser session) and no multi-turn memory (each question is answered independently, with no awareness of earlier questions in the same conversation). It is entirely dependent on the accuracy and completeness of what the owner has typed in — it has no independent source of truth about the pet. Conflict detection only compares exact matching due times, so tasks that meaningfully overlap but aren't scheduled at the identical time are not flagged as conflicts. Finally, the system supports exactly six question types by design; anything else is refused rather than answered, which is a deliberate scope limitation but a limitation nonetheless.
2. **Could the AI be misused, and how is misuse reduced?** Yes — a user could try to ask PawPal+ AI for veterinary diagnosis or treatment advice, phrase a question as if it could change task data ("mark this complete"), or treat it as a general-purpose chatbot for unrelated questions. Misuse is reduced at several independent layers (see "Guardrails" and "Potential Misuse" above): the system prompt forbids veterinary and data-modification language; `validators.py` independently re-scans every generated answer for that language regardless of what Claude actually produced, and routes any hit to the deterministic fallback; questions outside the six supported intents never reach Claude at all; and the assistant has no underlying write path into `Owner`/`Pet`/`Task`/`Scheduler`, so even a successfully "tricked" response could not actually change any data. The worst realistic outcome of attempted misuse is an unhelpful or refused answer, not an unsafe or destructive action.
3. **What surprised me during reliability testing?** During human evaluation (`evaluation_results.md`), two of the questions suggested directly in the Streamlit UI — "What tasks are incomplete?" and "What task should I do next?" — were routed to the wrong intent (the generic `pet_tasks` catch-all) instead of `incomplete_tasks` and `next_task`, because `retrieval.detect_intent()`'s deterministic phrase matching did not recognize that word order. It was surprising that the app's *own* suggested example questions could trip up its own intent detection. The issue was found through manual evaluation against the running app, not by the automated suite, and was fixed in `retrieval.py` by adding standalone `"incomplete"`/`"next"` keyword catch-alls alongside the existing `"schedule"`/`"task"` catch-alls. The complete automated suite (126 tests) still passed after the fix, and all three affected manual cases were re-run and passed.
4. **How did I collaborate with AI?** AI was used as a design and implementation collaborator for the RAG pipeline — proposing the retrieval/orchestration/validation/fallback/logging split described above, and helping draft the initial versions of `retrieval.py`, `ai_assistant.py`, `validators.py`, and `logger_config.py`. Every suggestion went through the project's own pytest suite and a manual code review before being kept, and the human evaluation pass against the live Streamlit app (`evaluation_results.md`) was run and interpreted independently of the AI, which is how the intent-detection bug above was actually caught.
5. **What was one helpful suggestion?** Splitting the AI layer into structured retrieval, Claude orchestration, deterministic validation, a deterministic fallback, and privacy-conscious logging as five separate, independently testable pieces — see "AI Collaboration" above.
6. **What was one flawed suggestion?** An unverified, unsuitable default Claude model identifier hardcoded in `ai_assistant.py`, caught in review and replaced with the documented, configurable `DEFAULT_MODEL` / `ANTHROPIC_MODEL` setup — see "AI Collaboration" above.

Update (2026-08-04): a live, validated Claude-generated answer **has now been evidenced end-to-end** (see "Reliability" above) — with a real `ANTHROPIC_API_KEY` configured, `ai_assistant.answer_question()` returned `success=True`, `fallback_used=False`, and `validation_result.valid=True` for every supported question type with matching data, using `claude-sonnet-5`. The earlier note in this section described the state of the project on 2026-08-01, before a live key was available; it is preserved above for its historical record of the AI-collaboration process, but the "no live Claude-generated response" framing no longer applies. Full evidence is in `evaluation_results.md` and `execution_evidence.md` §0.
