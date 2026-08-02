# PawPal+ AI Assistant — Execution Evidence

This document collects raw, pasted evidence that the PawPal+ AI assistant was actually run and tested, to accompany the results recorded in `evaluation_results.md`. Every code block below is a placeholder — replace each one with real, unedited output. Do not fabricate or reconstruct output from memory.

## 1. Environment Information

```text
Python 3.13.7
pip 26.2 from /Users/jannati/Desktop/School/2026/Summer 2026/AI 110/applied-ai-system-final/.venv/lib/python3.13/site-packages/pip (python 3.13)
Darwin MacBookPro 25.5.0 Darwin Kernel Version 25.5.0: Tue Jun  9 22:18:58 PDT 2026; root:xnu-12377.121.10~1/RELEASE_ARM64_T6000 arm64

altair==6.2.2
annotated-types==0.8.0
anthropic==0.120.2
anyio==4.14.2
attrs==26.1.0
blinker==1.9.0
certifi==2026.7.22
charset-normalizer==3.4.9
click==8.4.2
distro==1.9.0
docstring_parser==0.18.0
gitdb==4.0.12
GitPython==3.1.57
h11==0.16.0
httpcore==1.0.9
httptools==0.8.0
httpx==0.28.1
idna==3.18
iniconfig==2.3.0
itsdangerous==2.2.0
Jinja2==3.1.6
jiter==0.16.0
jsonschema==4.26.0
jsonschema-specifications==2025.9.1
MarkupSafe==3.0.3
narwhals==2.24.0
numpy==2.5.1
packaging==26.2
pandas==3.0.5
pillow==12.3.0
pluggy==1.6.0
protobuf==7.35.1
pyarrow==24.0.0
pydantic==2.13.4
pydantic_core==2.46.4
pydeck==0.9.3
Pygments==2.20.0
pytest==9.1.1
python-dateutil==2.9.0.post0
python-multipart==0.0.32
referencing==0.37.0
requests==2.34.2
rpds-py==2026.6.3
six==1.17.0
smmap==5.0.3
sniffio==1.3.1
starlette==1.3.1
streamlit==1.60.0
tenacity==9.1.4
toml==0.10.2
typing-inspection==0.4.2
typing_extensions==4.16.0
urllib3==2.7.0
uvicorn==0.52.1
websockets==16.1.1
```

## 2. Dependency Installation

```text
[PASTE FULL TERMINAL OUTPUT OF:
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
]
```

## 3. Full Pytest Output

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0 -- /Users/jannati/Desktop/School/2026/Summer 2026/AI 110/applied-ai-system-final/.venv/bin/python3
cachedir: .pytest_cache
rootdir: /Users/jannati/Desktop/School/2026/Summer 2026/AI 110/applied-ai-system-final
plugins: anyio-4.14.2
collecting ... collected 126 items

tests/test_ai_assistant.py::test_blank_question_returns_fallback PASSED  [  0%]
tests/test_ai_assistant.py::test_unsupported_question_returns_fallback PASSED [  1%]
tests/test_ai_assistant.py::test_unsupported_question_does_not_call_api PASSED [  2%]
tests/test_ai_assistant.py::test_successful_grounded_answer PASSED       [  3%]
tests/test_ai_assistant.py::test_detected_intent_is_returned PASSED      [  3%]
tests/test_ai_assistant.py::test_detected_pet_is_returned PASSED         [  4%]
tests/test_ai_assistant.py::test_retrieval_result_is_included PASSED     [  5%]
tests/test_ai_assistant.py::test_validation_result_is_included PASSED    [  6%]
tests/test_ai_assistant.py::test_missing_api_key_falls_back PASSED       [  7%]
tests/test_ai_assistant.py::test_injected_client_works_without_env_api_key PASSED [  7%]
tests/test_ai_assistant.py::test_api_exception_falls_back PASSED         [  8%]
tests/test_ai_assistant.py::test_empty_api_response_falls_back PASSED    [  9%]
tests/test_ai_assistant.py::test_malformed_api_response_falls_back PASSED [ 10%]
tests/test_ai_assistant.py::test_malformed_api_response_missing_content_attribute_falls_back PASSED [ 11%]
tests/test_ai_assistant.py::test_multiple_text_blocks_are_joined PASSED  [ 11%]
tests/test_ai_assistant.py::test_validation_failure_causes_fallback PASSED [ 12%]
tests/test_ai_assistant.py::test_autonomous_action_claim_causes_fallback PASSED [ 13%]
tests/test_ai_assistant.py::test_veterinary_language_causes_fallback PASSED [ 14%]
tests/test_ai_assistant.py::test_conflict_contradiction_causes_fallback PASSED [ 15%]
tests/test_ai_assistant.py::test_no_context_result_skips_the_api PASSED  [ 15%]
tests/test_ai_assistant.py::test_unknown_pet_returns_safe_fallback PASSED [ 16%]
tests/test_ai_assistant.py::test_fallback_reason_stable_values[blank_question-blank_question] PASSED [ 17%]
tests/test_ai_assistant.py::test_fallback_reason_stable_values[unsupported_question-unsupported_question] PASSED [ 18%]
tests/test_ai_assistant.py::test_fallback_reason_stable_values[no_context-no_context] PASSED [ 19%]
tests/test_ai_assistant.py::test_fallback_reason_stable_values[missing_api_key-missing_api_key] PASSED [ 19%]
tests/test_ai_assistant.py::test_fallback_reason_stable_values[api_error-api_error] PASSED [ 20%]
tests/test_ai_assistant.py::test_fallback_reason_stable_values[empty_response-empty_response] PASSED [ 21%]
tests/test_ai_assistant.py::test_fallback_reason_stable_values[response_parse_error-response_parse_error] PASSED [ 22%]
tests/test_ai_assistant.py::test_fallback_reason_stable_values[validation_failed-validation_failed] PASSED [ 23%]
tests/test_ai_assistant.py::test_owner_pet_task_objects_are_not_mutated PASSED [ 23%]
tests/test_ai_assistant.py::test_api_key_never_appears_in_returned_errors PASSED [ 24%]
tests/test_ai_assistant.py::test_model_configurable_via_function_parameter PASSED [ 25%]
tests/test_ai_assistant.py::test_model_configurable_via_environment_variable PASSED [ 26%]
tests/test_ai_assistant.py::test_function_parameter_model_overrides_environment_variable PASSED [ 26%]
tests/test_ai_assistant.py::test_default_model_used_when_unconfigured PASSED [ 27%]
tests/test_ai_assistant.py::test_normal_fallback_produces_readable_answer PASSED [ 28%]
tests/test_logger_config.py::test_get_logger_returns_a_logger PASSED     [ 29%]
tests/test_logger_config.py::test_repeated_calls_do_not_duplicate_handlers PASSED [ 30%]
tests/test_logger_config.py::test_log_file_created_in_temp_directory PASSED [ 30%]
tests/test_logger_config.py::test_messages_can_be_written_to_file PASSED [ 31%]
tests/test_logger_config.py::test_retrieval_logs_detected_intent_and_record_count PASSED [ 32%]
tests/test_logger_config.py::test_retrieval_logs_no_matching_records PASSED [ 33%]
tests/test_logger_config.py::test_validation_logs_pass_and_failure_outcomes PASSED [ 34%]
tests/test_logger_config.py::test_ai_assistant_logs_fallback_usage PASSED [ 34%]
tests/test_logger_config.py::test_api_failure_logs_do_not_expose_raw_exception PASSED [ 35%]
tests/test_logger_config.py::test_api_keys_do_not_appear_in_captured_logs PASSED [ 36%]
tests/test_logger_config.py::test_full_prompt_and_context_not_logged PASSED [ 37%]
tests/test_logger_config.py::test_logging_does_not_mutate_owner_or_retrieval_result PASSED [ 38%]
tests/test_logger_config.py::test_file_handler_setup_failure_does_not_crash PASSED [ 38%]
tests/test_pawpal.py::test_mark_complete_sets_completed_true PASSED      [ 39%]
tests/test_pawpal.py::test_add_task_increases_pet_task_count PASSED      [ 40%]
tests/test_pawpal.py::test_complete_task_creates_next_day_occurrence_for_daily_task PASSED [ 41%]
tests/test_pawpal.py::test_complete_task_creates_next_month_occurrence_for_monthly_task PASSED [ 42%]
tests/test_pawpal.py::test_generate_plan_orders_tasks_chronologically PASSED [ 42%]
tests/test_pawpal.py::test_generate_plan_detects_conflict_between_pets PASSED [ 43%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[What are my incomplete tasks?-incomplete_tasks] PASSED [ 44%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[Show me pending tasks-incomplete_tasks] PASSED [ 45%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[What tasks have been completed?-completed_tasks] PASSED [ 46%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[What tasks does Biscuit have?-pet_tasks] PASSED [ 46%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[What is today's schedule?-todays_schedule] PASSED [ 47%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[what is todays schedule-todays_schedule] PASSED [ 48%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[Are there any conflicts?-conflicts] PASSED [ 49%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[What's my next task?-next_task] PASSED [ 50%]
tests/test_retrieval.py::test_detect_intent_for_each_supported_type[What's the weather today?-unsupported] PASSED [ 50%]
tests/test_retrieval.py::test_detect_intent_handles_capitalization PASSED [ 51%]
tests/test_retrieval.py::test_detect_intent_handles_surrounding_whitespace PASSED [ 52%]
tests/test_retrieval.py::test_detect_intent_unsupported_question PASSED  [ 53%]
tests/test_retrieval.py::test_detect_intent_blank_question PASSED        [ 53%]
tests/test_retrieval.py::test_detect_intent_none_question PASSED         [ 54%]
tests/test_retrieval.py::test_detect_pet_case_insensitive_returns_stored_name PASSED [ 55%]
tests/test_retrieval.py::test_detect_pet_unknown_name_returns_none PASSED [ 56%]
tests/test_retrieval.py::test_detect_pet_no_pets_returns_none PASSED     [ 57%]
tests/test_retrieval.py::test_retrieve_context_blank_question PASSED     [ 57%]
tests/test_retrieval.py::test_retrieve_context_unsupported_question PASSED [ 58%]
tests/test_retrieval.py::test_incomplete_tasks_retrieval PASSED          [ 59%]
tests/test_retrieval.py::test_completed_tasks_retrieval PASSED           [ 60%]
tests/test_retrieval.py::test_pet_specific_tasks_retrieval PASSED        [ 61%]
tests/test_retrieval.py::test_pet_specific_tasks_case_insensitive_match PASSED [ 61%]
tests/test_retrieval.py::test_pet_specific_tasks_unknown_pet PASSED      [ 62%]
tests/test_retrieval.py::test_pet_with_no_tasks PASSED                   [ 63%]
tests/test_retrieval.py::test_todays_schedule_excludes_future_tasks PASSED [ 64%]
tests/test_retrieval.py::test_todays_schedule_includes_overdue_tasks PASSED [ 65%]
tests/test_retrieval.py::test_todays_schedule_chronological_ordering PASSED [ 65%]
tests/test_retrieval.py::test_todays_schedule_invalid_time_sorts_last PASSED [ 66%]
tests/test_retrieval.py::test_todays_schedule_excludes_completed_tasks PASSED [ 67%]
tests/test_retrieval.py::test_todays_schedule_no_due_tasks PASSED        [ 68%]
tests/test_retrieval.py::test_next_task_retrieval PASSED                 [ 69%]
tests/test_retrieval.py::test_next_task_none_qualifies PASSED            [ 69%]
tests/test_retrieval.py::test_conflicts_retrieval_uses_scheduler_logic PASSED [ 70%]
tests/test_retrieval.py::test_conflicts_none_found PASSED                [ 71%]
tests/test_retrieval.py::test_owner_with_no_pets_is_handled_safely PASSED [ 72%]
tests/test_retrieval.py::test_retrieval_does_not_mutate_owner_state PASSED [ 73%]
tests/test_retrieval.py::test_retrieve_context_default_reference_date_is_today PASSED [ 73%]
tests/test_retrieval.py::test_reference_date_present_in_result PASSED    [ 74%]
tests/test_validators.py::test_fallback_incomplete_tasks_with_records PASSED [ 75%]
tests/test_validators.py::test_fallback_no_incomplete_tasks PASSED       [ 76%]
tests/test_validators.py::test_fallback_completed_tasks PASSED           [ 76%]
tests/test_validators.py::test_fallback_completed_tasks_none PASSED      [ 77%]
tests/test_validators.py::test_fallback_pet_specific_tasks PASSED        [ 78%]
tests/test_validators.py::test_fallback_pet_specific_unknown_pet PASSED  [ 79%]
tests/test_validators.py::test_fallback_pet_with_no_tasks PASSED         [ 80%]
tests/test_validators.py::test_fallback_todays_schedule PASSED           [ 80%]
tests/test_validators.py::test_fallback_todays_schedule_no_due_tasks PASSED [ 81%]
tests/test_validators.py::test_fallback_conflicts PASSED                 [ 82%]
tests/test_validators.py::test_fallback_no_conflicts PASSED              [ 83%]
tests/test_validators.py::test_fallback_next_task PASSED                 [ 84%]
tests/test_validators.py::test_fallback_no_next_task PASSED              [ 84%]
tests/test_validators.py::test_fallback_unsupported_intent PASSED        [ 85%]
tests/test_validators.py::test_fallback_does_not_mutate_retrieval_result PASSED [ 86%]
tests/test_validators.py::test_valid_grounded_answer PASSED              [ 87%]
tests/test_validators.py::test_blank_answer_is_rejected PASSED           [ 88%]
tests/test_validators.py::test_autonomous_action_claim_is_rejected PASSED [ 88%]
tests/test_validators.py::test_fabricated_data_when_no_records_exist PASSED [ 89%]
tests/test_validators.py::test_correct_no_conflict_answer_is_valid PASSED [ 90%]
tests/test_validators.py::test_incorrect_no_conflict_claim_when_conflicts_exist PASSED [ 91%]
tests/test_validators.py::test_incorrect_conflict_claim_when_none_exist PASSED [ 92%]
tests/test_validators.py::test_completed_task_described_as_incomplete PASSED [ 92%]
tests/test_validators.py::test_incomplete_task_described_as_completed PASSED [ 93%]
tests/test_validators.py::test_veterinary_diagnosis_language_is_rejected PASSED [ 94%]
tests/test_validators.py::test_stored_medication_wording_is_not_falsely_flagged PASSED [ 95%]
tests/test_validators.py::test_harmless_paraphrasing_is_not_rejected PASSED [ 96%]
tests/test_validators.py::test_confidence_always_between_zero_and_one[] PASSED [ 96%]
tests/test_validators.py::test_confidence_always_between_zero_and_one[I marked the task complete.] PASSED [ 97%]
tests/test_validators.py::test_confidence_always_between_zero_and_one[I marked the task complete. Your pet has an infection, diagnosis: flu.] PASSED [ 98%]
tests/test_validators.py::test_confidence_always_between_zero_and_one[I marked the task complete. Diagnosis: flu. I prescribe rest. There is a conflict.] PASSED [ 99%]
tests/test_validators.py::test_validate_answer_does_not_mutate_retrieval_result PASSED [100%]

============================= 126 passed in 0.10s ==============================
```

## 4. Streamlit Launch Output

```text
2026-08-01 21:13:36.650 Uvicorn server started on :::8501

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.50.179:8501

  Help agents write better Streamlit apps?
  Install the official Streamlit skills by running streamlit skills in your terminal.

  For better performance, install the Watchdog module:

  $ xcode-select --install
  $ pip install watchdog
```

## 5. Sample Data Entered

Record the exact, deterministic pets/tasks entered into the Streamlit UI before running the test cases in `evaluation_results.md`, so the scenario is reproducible.

```text
Owner name: (default Streamlit session owner — available_time=120, preferred_times=["morning"], task_priorities=[])

Pet 1:
  Name: Mochi
  Species: cat
  Age: 2
  Needs: feeding, medication
  Tasks:
    - Description: Feed breakfast   | Time: 08:00 | Frequency: daily
    - Description: Give medication | Time: 12:00 | Frequency: daily

Pet 2:
  Name: Biscuit
  Species: dog
  Age: 4
  Needs: walking, grooming
  Tasks:
    - Description: Morning walk | Time: 08:00 | Frequency: daily
    - Description: Grooming     | Time: 17:00 | Frequency: weekly

Note: Mochi's "Feed breakfast" and Biscuit's "Morning walk" are both due 08:00 on the same day (due_date defaults to the date the task is created, per Task.__init__ in pawpal_system.py) — this is the deliberate scheduling conflict used by TC-05 / "Are there any scheduling conflicts?".

Entered via a script that calls the same Owner/Pet/Task classes and ai_assistant.answer_question() that app.py's Streamlit UI calls (see the "Exact Commands" section below) rather than by clicking through the browser, since no browser-automation tool was available in this session. Functionally equivalent to entering this data by hand in the "Quick Demo Inputs" / "Tasks" sections of the running app.
```

## 6. Three Successful AI Interactions

**STATUS: NOT YET CAPTURED.** No `ANTHROPIC_API_KEY` was configured in the environment this evidence was collected in, so every question run so far (see `evaluation_results.md`) hit a deterministic fallback (`fallback_used=True`) rather than a real Claude-generated, validated answer. Per the "do not invent results" instruction, the three interactions below are left as placeholders rather than filled with fabricated text.

To complete this section: export a real `ANTHROPIC_API_KEY` in your own terminal (do not paste it into chat), run `streamlit run app.py`, re-enter the same deterministic sample data from Section 5, ask the three questions below, and paste back for each: the final answer, detected intent, detected pet, validation confidence, retrieved context, and fallback status (should be `fallback_used=No` for all three if the AI answer passes validation).

Three cases where `answer_question()` returned `success=True` (a real Claude-generated answer passed validation, `fallback_used=False`). Use the "Retrieved PawPal+ Context" expander in the UI as the source for "Retrieved context".

### Interaction 1

```text
User question:      [FILL IN]
Retrieved context:   [PASTE context_text FROM THE "Retrieved PawPal+ Context" EXPANDER]
AI answer:           [PASTE THE TEXT SHOWN UNDER "Answer:"]
Intent:              [FILL IN, e.g. incomplete_tasks]
Detected pet:        [FILL IN OR "none"]
Confidence:          [PASTE "Validation confidence" VALUE]
Fallback used:       No
Fallback reason:     N/A
```

### Interaction 2

```text
User question:      [FILL IN]
Retrieved context:   [PASTE context_text FROM THE "Retrieved PawPal+ Context" EXPANDER]
AI answer:           [PASTE THE TEXT SHOWN UNDER "Answer:"]
Intent:              [FILL IN]
Detected pet:        [FILL IN OR "none"]
Confidence:          [PASTE "Validation confidence" VALUE]
Fallback used:       No
Fallback reason:     N/A
```

### Interaction 3

```text
User question:      [FILL IN]
Retrieved context:   [PASTE context_text FROM THE "Retrieved PawPal+ Context" EXPANDER]
AI answer:           [PASTE THE TEXT SHOWN UNDER "Answer:"]
Intent:              [FILL IN]
Detected pet:        [FILL IN OR "none"]
Confidence:          [PASTE "Validation confidence" VALUE]
Fallback used:       No
Fallback reason:     N/A
```

## 7. One Deterministic Fallback Interaction

One case where `fallback_used=True` (e.g. unknown pet, unsupported question, blank question, or missing API key — see `ai_assistant.py` `FALLBACK_*` reasons).

Note: the originally-planned question "What tasks are incomplete?" did not reach the `missing_api_key` code path before the fix documented in `evaluation_results.md` (TC-01/TC-06/TC-10) — a real intent-detection bug in `retrieval.py::detect_intent()` misrouted it to `pet_tasks` before the API-key check was ever reached. That bug has since been fixed (added `"incomplete"`/`"next"` keyword catch-alls). The interaction below was captured with the rephrased wording used during the original bug-finding run, before the fix landed; it still correctly demonstrates the `missing_api_key` fallback and remains valid evidence for that code path.

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
Confidence:          N/A — no validation result for this fallback (the API-key check short-circuits before a Claude call or validators.validate_answer() is ever made)
Fallback used:       Yes
Fallback reason:     missing_api_key
```

Captured by calling `ai_assistant.answer_question()` directly with `ANTHROPIC_API_KEY` unset (see Section 5's note on how the sample data was entered), which exercises the exact same code path `app.py` calls when its "Ask PawPal+ AI" button is clicked.

## 8. Retrieved-Context Evidence

Paste at least one raw "Retrieved PawPal+ Context" expander contents (the `context_text` plus the "Records retrieved" / "Detected intent" / "Detected pet" captions shown beneath it), copied directly from the running app, to prove retrieval was actually exercised rather than assumed.

```text
This is the information PawPal+ AI used to ground its answer.

Today's schedule (4):
- Mochi: Feed breakfast (08:00, daily, due 2026-08-01, not completed)
- Biscuit: Morning walk (08:00, daily, due 2026-08-01, not completed)
- Mochi: Give medication (12:00, daily, due 2026-08-01, not completed)
- Biscuit: Grooming (17:00, weekly, due 2026-08-01, not completed)

Records retrieved: 4
Detected intent: todays_schedule
Detected pet: none
```

Captured for TC-04 ("What is today's schedule?") — see `evaluation_results.md` for the corresponding observed answer, which matches this retrieved context exactly.

## 9. Logging Evidence

Paste a **few relevant, sanitized** lines from `logs/pawpal_ai.log` (or the console output) that correspond to one of the interactions above — e.g. lines showing "Question processing started", "Detected intent", "Retrieval completed", or "Processing completed". Do **not** paste API keys, full prompts, or any other sensitive/private content — trim each line to just what's needed to show the pipeline ran.

```text
2026-08-01 21:18:03,972 | INFO | pawpal_ai.ai_assistant | Question processing started. question_length=27
2026-08-01 21:18:03,972 | INFO | pawpal_ai.retrieval | Detected intent: todays_schedule
2026-08-01 21:18:03,972 | INFO | pawpal_ai.retrieval | Retrieval completed with 4 record(s).
2026-08-01 21:18:03,972 | INFO | pawpal_ai.ai_assistant | Detected intent: todays_schedule
2026-08-01 21:18:03,972 | INFO | pawpal_ai.validators | Fallback answer generated. fallback_intent=todays_schedule
2026-08-01 21:18:03,972 | INFO | pawpal_ai.ai_assistant | Deterministic fallback used. fallback_reason=missing_api_key
2026-08-01 21:18:03,972 | INFO | pawpal_ai.ai_assistant | Processing completed. success=False fallback_used=True
```

Taken from `logs/pawpal_ai.log` after running the Section 6/7 test questions (no API keys or full prompt text appear in these log lines — `ai_assistant.py` never logs the prompt or the key, only intent/fallback-reason/status metadata).

## 10. Human Evaluation Summary

```text
Total cases run:        10 (TC-01 through TC-10, see evaluation_results.md)
Passed:                 10 (after the retrieval.py fix below; 3 originally failed)
Failed:                 0
Pass percentage:        100%
Key observations:       retrieval.detect_intent() originally misrouted two of app.py's
                        own suggested example questions ("What tasks are incomplete?"
                        and "What task should I do next?") to the pet_tasks catch-all
                        instead of incomplete_tasks/next_task, because its phrase lists
                        only matched one specific word order (this also silently broke
                        TC-10's intended missing-API-key test). Fixed by adding
                        "incomplete"/"next" standalone-keyword catch-alls to
                        retrieval.py::detect_intent(), mirroring the existing
                        "schedule"/"task" catch-all pattern; all 126 automated tests
                        still pass, and all 3 affected manual cases were re-verified.
                        Deterministic fallback formatting, unknown-pet handling,
                        blank-question handling, and unsupported-question handling were
                        all correct throughout, with no fabricated data.
Known limitations:      (1) No ANTHROPIC_API_KEY was available in this environment, so
                        Section 6 (three successful AI-generated, validated interactions)
                        is still pending a run with a real key. (2) app.py exposes no
                        "mark complete" UI control, so the "completed tasks" case (TC-02)
                        could only be verified against zero completed tasks, not a
                        genuinely mixed complete/incomplete data set.
```

## Exact Commands to Collect This Evidence

Run these from the project root, in order:

```bash
# 1. Environment information
python3 --version
pip --version
uname -a
pip freeze

# 2. Dependency installation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Full pytest output
python3 -m pytest -v

# 4. Streamlit launch (leave running, then interact with it in the browser)
streamlit run app.py

# 9. Logging evidence (after interacting with the app at least once)
tail -n 30 logs/pawpal_ai.log
```
