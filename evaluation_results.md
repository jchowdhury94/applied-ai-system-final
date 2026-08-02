# PawPal+ AI Assistant — Evaluation Results

This document records manual test results for `ai_assistant.answer_question()` as exercised through the Streamlit "Ask PawPal+ AI" panel in `app.py`. Each row covers one supported question type, one edge case, or one failure mode described in `ai_assistant.py` / `retrieval.py`.

## Test Results

| Test ID | User Input | Expected Retrieval | Evaluation Criteria | Observed Answer | Fallback Used | Confidence | Pass/Fail | Notes |
|---|---|---|---|---|---|---|---|---|
| TC-01 | "What tasks are incomplete?" | intent=`incomplete_tasks`; records = all not-completed tasks across all pets, sorted by time | Answer lists exactly the incomplete tasks from the retrieved context, with no invented pets/times/tasks; matches `context_text` | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-02 | "What tasks are completed?" | intent=`completed_tasks`; records = all completed tasks across all pets, sorted by time | Answer lists exactly the completed tasks from the retrieved context; no incomplete tasks are misreported as completed | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-03 | "What tasks does Mochi have?" (Mochi is an added pet) | intent=`pet_tasks`; detected_pet=`Mochi`; records = all of Mochi's tasks | Answer is scoped only to Mochi's tasks; detected pet shown in UI matches "Mochi"; no other pet's tasks appear | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-04 | "What is today's schedule?" | intent=`todays_schedule`; records = incomplete tasks with `due_date <= today`, sorted by time | Answer reflects only tasks due today or earlier that are not completed; matches reference date used in the test | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-05 | "Are there any scheduling conflicts?" (two tasks entered at the same time for different pets) | intent=`conflicts`; records = conflict groups from `Scheduler.find_conflicts()` over today's due tasks | Answer correctly states whether a conflict exists; if a conflict exists, both conflicting tasks/pets are named; answer does not claim "no conflicts" when conflicts were retrieved | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-06 | "What task should I do next?" | intent=`next_task`; records = first (earliest-time) incomplete task due today or earlier | Answer names exactly one task — the earliest due/incomplete one — with correct pet, time, and due date | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-07 | "What tasks does Rex have?" (Rex was never added as a pet) | intent=`pet_tasks`; detected_pet=`None`; records=[] | Fallback is used (`FALLBACK_NO_CONTEXT` or pet-not-found path); answer states no matching pet was found; no task data is invented for "Rex" | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-08 | "" (submit with the question box left blank) | Not reached — `answer_question()` short-circuits before calling `retrieval.retrieve_context()` | Streamlit shows the "Please enter a question" warning, OR if submitted with only whitespace, `fallback_reason=blank_question` is used and answer is the unsupported-question fallback text | `[PASTE OBSERVED ANSWER OR UI WARNING TEXT]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-09 | "Should I take my dog to the vet today?" | intent=`unsupported`; records=[] | `fallback_reason=unsupported_question`; answer lists the supported question types and gives no veterinary advice | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |
| TC-10 | "What tasks are incomplete?" with `ANTHROPIC_API_KEY` unset/removed from the environment before launching Streamlit | intent=`incomplete_tasks`; records populated normally (retrieval does not depend on the API key) | `fallback_reason=missing_api_key`; answer equals the deterministic `format_fallback_answer()` output for incomplete tasks; no exception/crash is shown in the UI | `[PASTE OBSERVED ANSWER]` | `[YES / NO]` | `[PASTE CONFIDENCE VALUE]` | `[PASS / FAIL]` | `[NOTES]` |

## Testing Procedure

1. **Start the Streamlit app.**
   Activate the project virtual environment and run:
   ```bash
   streamlit run app.py
   ```
   Confirm the app loads in the browser at the printed local URL before proceeding.

2. **Add deterministic sample pets and tasks.**
   Using the "Quick Demo Inputs" and "Tasks" sections in the UI, add a fixed, repeatable set of pets/tasks (record exactly what you entered in `execution_evidence.md` §5) so retrieval results are reproducible across test runs — e.g. a pet named `Mochi` with an incomplete task due today, a completed task, and a second pet sharing a task time with `Mochi` to trigger a conflict for TC-05.

3. **Submit each question.**
   For each Test ID above, type the exact "User Input" text into the "Ask a question about your pets and tasks" box and click **Ask PawPal+ AI**. For TC-10, stop the app, unset `ANTHROPIC_API_KEY` in the shell, and relaunch before submitting.

4. **Copy the displayed answer.**
   Copy the text shown under **Answer:** verbatim into the "Observed Answer" column — do not paraphrase or summarize it.

5. **Record fallback status, confidence, and retrieved context.**
   From the same result panel, record:
   - Whether the "PawPal+ used a deterministic answer..." info box appeared (`Fallback Used`) and its stated reason.
   - The "Validation confidence" caption value (`Confidence`) when an AI answer was generated; leave blank if a fallback with no validation result was used.
   - Expand "Retrieved PawPal+ Context" and confirm it matches the "Expected Retrieval" column (also copy it into `execution_evidence.md` §8 for at least one case per intent).

6. **Mark Pass or Fail using the listed criteria.**
   Mark **Pass** only if the observed answer, fallback behavior, and confidence all satisfy the "Evaluation Criteria" column with no fabricated or contradicted data. Mark **Fail** otherwise, and explain the discrepancy in "Notes".

## Summary

- **Total cases:** `[FILL IN]`
- **Passed:** `[FILL IN]`
- **Failed:** `[FILL IN]`
- **Pass percentage:** `[FILL IN]`
- **Important findings:** `[FILL IN]`
