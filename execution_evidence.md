# PawPal+ AI Assistant — Execution Evidence

This document collects raw, pasted evidence that the PawPal+ AI assistant was actually run and tested, to accompany the results recorded in `evaluation_results.md`. Every code block below is a placeholder — replace each one with real, unedited output. Do not fabricate or reconstruct output from memory.

## 1. Environment Information

```text
[PASTE OUTPUT OF: python3 --version]
[PASTE OUTPUT OF: pip --version]
[PASTE OUTPUT OF: uname -a   (or `ver` on Windows)]
[PASTE OUTPUT OF: pip freeze   (or at least: streamlit, anthropic, pytest versions)]
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
[PASTE FULL, UNEDITED OUTPUT OF: python3 -m pytest -v]
```

## 4. Streamlit Launch Output

```text
[PASTE FULL TERMINAL OUTPUT OF: streamlit run app.py
INCLUDING the "Local URL" / "Network URL" lines Streamlit prints on startup.]
```

## 5. Sample Data Entered

Record the exact, deterministic pets/tasks entered into the Streamlit UI before running the test cases in `evaluation_results.md`, so the scenario is reproducible.

```text
Owner name: [FILL IN]

Pet 1:
  Name: [FILL IN]
  Species: [FILL IN]
  Age: [FILL IN]
  Needs: [FILL IN]
  Tasks:
    - Description: [FILL IN] | Time: [FILL IN] | Frequency: [FILL IN]
    - Description: [FILL IN] | Time: [FILL IN] | Frequency: [FILL IN]

Pet 2:
  Name: [FILL IN]
  Species: [FILL IN]
  Age: [FILL IN]
  Needs: [FILL IN]
  Tasks:
    - Description: [FILL IN] | Time: [FILL IN] | Frequency: [FILL IN]

[ADD/REMOVE ROWS AS NEEDED TO MATCH WHAT WAS ACTUALLY ENTERED]
```

## 6. Three Successful AI Interactions

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

```text
User question:      [FILL IN]
Retrieved context:   [PASTE context_text, OR NOTE IF RETRIEVAL WAS NOT REACHED]
AI answer:           [PASTE THE DETERMINISTIC FALLBACK TEXT SHOWN UNDER "Answer:"]
Intent:              [FILL IN OR "none"]
Detected pet:        [FILL IN OR "none"]
Confidence:          [PASTE VALUE OR "N/A — no validation result for this fallback"]
Fallback used:       Yes
Fallback reason:     [FILL IN, e.g. missing_api_key / unsupported_question / no_context / blank_question]
```

## 8. Retrieved-Context Evidence

Paste at least one raw "Retrieved PawPal+ Context" expander contents (the `context_text` plus the "Records retrieved" / "Detected intent" / "Detected pet" captions shown beneath it), copied directly from the running app, to prove retrieval was actually exercised rather than assumed.

```text
[PASTE RAW "Retrieved PawPal+ Context" EXPANDER CONTENTS HERE]
```

## 9. Logging Evidence

Paste a **few relevant, sanitized** lines from `logs/pawpal_ai.log` (or the console output) that correspond to one of the interactions above — e.g. lines showing "Question processing started", "Detected intent", "Retrieval completed", or "Processing completed". Do **not** paste API keys, full prompts, or any other sensitive/private content — trim each line to just what's needed to show the pipeline ran.

```text
[PASTE 3-6 SANITIZED LOG LINES HERE, e.g.:
2026-08-01 12:00:00,000 | INFO | pawpal_ai.ai_assistant | Question processing started. question_length=27
2026-08-01 12:00:00,001 | INFO | pawpal_ai.retrieval | Detected intent: incomplete_tasks
2026-08-01 12:00:00,050 | INFO | pawpal_ai.ai_assistant | Processing completed. success=True fallback_used=False
]
```

## 10. Human Evaluation Summary

```text
Total cases run:        [FILL IN]
Passed:                 [FILL IN]
Failed:                 [FILL IN]
Pass percentage:        [FILL IN]
Key observations:       [FILL IN]
Known limitations:      [FILL IN]
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
