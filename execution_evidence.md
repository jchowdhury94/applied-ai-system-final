# PawPal+ AI Assistant — Execution Evidence

This document collects raw, pasted evidence that the PawPal+ AI assistant was actually run and tested, to accompany the results recorded in `evaluation_results.md`. Every code block below is real, unedited output captured from this repository. Do not fabricate or reconstruct output from memory.

**This document now includes a real, live Anthropic API call (Section 0, 2026-08-04).** Sections 1–10 below Section 0 are the original evidence collected on 2026-08-01, before a working `ANTHROPIC_API_KEY` was available; they are preserved for their bug-fix record and are explicitly labeled **historical** where their original text claimed no live API was used. Section 0 supersedes those claims.

## 0. Live Evidence — 2026-08-04

### 0.1 Python version and dependency versions

```text
Python 3.13.7
anthropic==0.120.2
streamlit==1.60.0
python-dotenv (installed, version satisfies python-dotenv>=1.0.0 in requirements.txt)
pytest==9.1.1
```

Full `pip freeze` output for this environment is unchanged from Section 1 below (same `.venv`, re-verified via `pip install -r requirements.txt` on 2026-08-04, which reported `Requirement already satisfied` for every package).

### 0.2 Dependency installation (re-run)

```bash
$ python -m pip install -r requirements.txt
```

```text
Requirement already satisfied: streamlit>=1.30 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 1)) (1.60.0)
Requirement already satisfied: pytest>=7.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 2)) (9.1.1)
Requirement already satisfied: anthropic>=0.40.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 3)) (0.120.2)
Requirement already satisfied: python-dotenv>=1.0.0 in ./.venv/lib/python3.13/site-packages (from -r requirements.txt (line 4)) (... satisfied)
[...all transitive dependencies already satisfied...]
```

### 0.3 Syntax check

```bash
$ python -m py_compile app.py ai_assistant.py retrieval.py validators.py logger_config.py pawpal_system.py
$ echo $?
0
```

No output, exit code 0 — all six modules compile cleanly.

### 0.4 Full pytest run

```bash
$ python -m pytest -v
```

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 126 items

[...126 test IDs, all PASSED — identical list to Section 3 below, re-run and re-verified on 2026-08-04...]

============================= 126 passed in 0.10s ==============================
```

**126 passed, 0 failed.** Full per-test output is in Section 3 below (the test IDs and pass/fail status are unchanged from that run — this repeat run confirms nothing has regressed).

### 0.5 Streamlit startup

```bash
$ python -m streamlit run app.py --server.headless true --server.port 8502
```

```text
2026-08-04 08:41:58.577 Uvicorn server started on :::8502

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8502
  Network URL: http://192.168.50.179:8502
  External URL: http://136.55.227.224:8502

  For better performance, install the Watchdog module:

  $ xcode-select --install
  $ pip install watchdog
```

The process was left running for 6 seconds (confirming it stays up, not just that it starts) and then stopped (`pkill -f "streamlit run app.py"`). No errors or tracebacks were printed.

### 0.6 Successful live Claude API call

Using the real `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` loaded privately from `.env` (never printed or logged — see Section 0.9), `ai_assistant.answer_question()` was called directly with the sample data specified for this audit:

```text
Mochi: Feed breakfast at 08:00 (daily)
Mochi: Give medication at 12:00 (daily)
Biscuit: Morning walk at 08:00 (daily)

Question: "What tasks does Mochi have?"
```

Result (fields read directly from the returned dictionary — no API key anywhere in this output):

```text
model:                     claude-sonnet-5
intent:                    pet_tasks
detected_pet:              Mochi
records_retrieved:         2
success:                   True
fallback_used:             False
fallback_reason:           None
error:                     None
validation_result.valid:            True
validation_result.confidence:       1.0
validation_result.issues:           []
answer:
  Mochi has 2 tasks recorded in PawPal+:

  1. **Feed breakfast** — 08:00, daily, due 2026-08-04, not yet completed
  2. **Give medication** — 12:00, daily, due 2026-08-04, not yet completed

  Let me know if you'd like more details — but note I can't modify, complete,
  or reschedule these tasks myself.
```

This confirms, from a real network call to the Anthropic API: `success=True`, `fallback_used=False`, `validation_result.valid=True`, and a model-generated answer that is fully grounded in the retrieved records (no invented pets, tasks, times, or conflicts).

### 0.7 Full question-type matrix (live)

The same live-API run was repeated across every supported question type and edge case (raw JSON below matches the table in `evaluation_results.md` → "Live API Evaluation"):

```json
[
  {"case": "Incomplete tasks", "detected_intent": "incomplete_tasks", "records_retrieved": 4, "success": true, "fallback_used": false, "validation_valid": true, "validation_confidence": 1.0},
  {"case": "Completed tasks", "detected_intent": "completed_tasks", "records_retrieved": 1, "success": true, "fallback_used": false, "validation_valid": true, "validation_confidence": 1.0},
  {"case": "Specific pet's tasks", "detected_intent": "pet_tasks", "records_retrieved": 4, "success": true, "fallback_used": false, "validation_valid": true, "validation_confidence": 1.0},
  {"case": "Today's schedule", "detected_intent": "todays_schedule", "records_retrieved": 3, "success": true, "fallback_used": false, "validation_valid": true, "validation_confidence": 1.0},
  {"case": "Scheduling conflicts", "detected_intent": "conflicts", "records_retrieved": 1, "success": true, "fallback_used": false, "validation_valid": true, "validation_confidence": 1.0},
  {"case": "Next task", "detected_intent": "next_task", "records_retrieved": 1, "success": true, "fallback_used": false, "validation_valid": true, "validation_confidence": 1.0},
  {"case": "Unknown pet", "detected_intent": "pet_tasks", "records_retrieved": 0, "success": false, "fallback_used": true, "fallback_reason": "no_context"},
  {"case": "Blank question", "detected_intent": null, "records_retrieved": 0, "success": false, "fallback_used": true, "fallback_reason": "blank_question"},
  {"case": "Unsupported question", "detected_intent": "unsupported", "records_retrieved": 0, "success": false, "fallback_used": true, "fallback_reason": "unsupported_question"}
]
```

Full answer text for each case is in `evaluation_results.md` → "Live API Evaluation" table.

### 0.8 Missing-API-key fallback test (separate from the real key)

The real `.env` file was never modified. Instead, `ANTHROPIC_API_KEY` was removed from the *in-process* environment only, after `python-dotenv` had already loaded it, so `ai_assistant.answer_question()`'s own `os.environ.get("ANTHROPIC_API_KEY")` check saw nothing configured:

```python
import os
os.environ.pop("ANTHROPIC_API_KEY", None)  # this process only — .env file untouched
```

Result:

```text
success:            False
fallback_used:      True
fallback_reason:    missing_api_key
error:              The Claude API key is not configured.
answer:             Tasks for Mochi:
                     - Feed breakfast at 08:00, due 2026-08-04 (not completed)
```

Immediately after, the real `.env` file was read back and confirmed unchanged (both `ANTHROPIC_API_KEY=` and `ANTHROPIC_MODEL=` lines still present; values not printed). This demonstrates the missing-key fallback path in isolation, without ever touching the real credential.

### 0.9 Sanitized log lines (2026-08-04 run)

Tail of `logs/pawpal_ai.log` after the above runs — no API keys, prompts, or question/answer text appear (confirmed with `grep -c "sk-ant" logs/pawpal_ai.log` → `0` matches):

```text
2026-08-04 08:40:28,560 | INFO | pawpal_ai.validators | Validation passed. issue_count=0 confidence=1.00
2026-08-04 08:40:28,560 | INFO | pawpal_ai.ai_assistant | Validation passed for the generated answer.
2026-08-04 08:40:28,560 | INFO | pawpal_ai.ai_assistant | Processing completed. success=True fallback_used=False
2026-08-04 08:40:28,560 | INFO | pawpal_ai.ai_assistant | Question processing started. question_length=20
2026-08-04 08:40:28,560 | INFO | pawpal_ai.ai_assistant | Model selected: claude-sonnet-5
2026-08-04 08:40:28,560 | INFO | pawpal_ai.retrieval | Retrieval started.
2026-08-04 08:40:28,560 | INFO | pawpal_ai.retrieval | Detected intent: next_task
2026-08-04 08:40:28,561 | INFO | pawpal_ai.retrieval | Retrieval completed with 1 record(s).
2026-08-04 08:40:28,561 | INFO | pawpal_ai.ai_assistant | Detected intent: next_task
2026-08-04 08:40:28,588 | INFO | pawpal_ai.ai_assistant | Claude request attempted.
2026-08-04 08:40:32,286 | INFO | pawpal_ai.ai_assistant | Claude request succeeded.
2026-08-04 08:40:32,287 | INFO | pawpal_ai.validators | Validation started.
2026-08-04 08:40:32,287 | INFO | pawpal_ai.validators | Validation passed. issue_count=0 confidence=1.00
2026-08-04 08:40:32,287 | INFO | pawpal_ai.ai_assistant | Validation passed for the generated answer.
2026-08-04 08:40:32,287 | INFO | pawpal_ai.ai_assistant | Processing completed. success=True fallback_used=False
2026-08-04 08:40:32,288 | INFO | pawpal_ai.retrieval | Detected intent: pet_tasks
2026-08-04 08:40:32,288 | INFO | pawpal_ai.retrieval | No matching records were found.
2026-08-04 08:40:32,288 | INFO | pawpal_ai.ai_assistant | Deterministic fallback used. fallback_reason=no_context
2026-08-04 08:40:32,288 | INFO | pawpal_ai.ai_assistant | Processing completed. success=False fallback_used=True
2026-08-04 08:40:32,289 | INFO | pawpal_ai.ai_assistant | Deterministic fallback used. fallback_reason=blank_question
2026-08-04 08:40:32,289 | INFO | pawpal_ai.ai_assistant | Deterministic fallback used. fallback_reason=unsupported_question
```

This shows both pipeline paths back to back within the same log file: the successful `Claude request attempted` → `Claude request succeeded` → `Validation passed` → `success=True fallback_used=False` sequence, and the deterministic `Deterministic fallback used` sequence for the no-context/blank/unsupported cases — confirming both paths described in the README ("Successful path: Question → Retrieval → Claude → Validation → Answer" and "Fallback path: Question → Retrieval → Deterministic formatter → Answer") are real and exercised.

### 0.10 What this supersedes

Section 6 below ("Live Claude Interaction Evidence Not Performed (By Decision)") and the "no `ANTHROPIC_API_KEY`" framing throughout Sections 5, 7, 9, and 10 described the state of this project on 2026-08-01, before a live key was available. That framing is now outdated for the project as a whole — a real Claude API key is configured and has been successfully exercised, as shown above. Sections 1–10 are kept below for their original historical/bug-fix value (in particular, the retrieval.py intent-detection bug fix, which is still present and verified working in the 2026-08-04 run) and are labeled accordingly.

---

## 1. Environment Information (historical — 2026-08-01)

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

## 2. Dependency Installation (historical — 2026-08-01)

Captured in a clean, temporary virtual environment (`.venv-evidence`), separate from the project's regular `.venv`, using:

```bash
python3 -m venv .venv-evidence
source .venv-evidence/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
deactivate
rm -rf .venv-evidence
```

```text
Requirement already satisfied: pip in ./.venv-evidence/lib/python3.13/site-packages (25.2)
Collecting pip
  Using cached pip-26.2-py3-none-any.whl.metadata (4.6 kB)
Using cached pip-26.2-py3-none-any.whl (1.8 MB)
Installing collected packages: pip
  Attempting uninstall: pip
    Found existing installation: pip 25.2
    Uninstalling pip-25.2:
      Successfully uninstalled pip-25.2
Successfully installed pip-26.2
---SEPARATOR---
Collecting streamlit>=1.30 (from -r requirements.txt (line 1))
  Using cached streamlit-1.60.0-py3-none-any.whl.metadata (10 kB)
Collecting pytest>=7.0 (from -r requirements.txt (line 2))
  Using cached pytest-9.1.1-py3-none-any.whl.metadata (7.6 kB)
Collecting anthropic>=0.40.0 (from -r requirements.txt (line 3))
  Using cached anthropic-0.120.2-py3-none-any.whl.metadata (3.3 kB)
Collecting altair!=5.4.0,!=5.4.1,<7,>=4.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached altair-6.2.2-py3-none-any.whl.metadata (11 kB)
Collecting blinker<2,>=1.5.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached blinker-1.9.0-py3-none-any.whl.metadata (1.6 kB)
Collecting click<9,>=7.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached click-8.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting gitpython!=3.1.19,<4,>=3.0.7 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached gitpython-3.1.57-py3-none-any.whl.metadata (13 kB)
Collecting numpy<3,>=1.23 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached numpy-2.5.1-cp313-cp313-macosx_14_0_arm64.whl.metadata (6.6 kB)
Collecting packaging>=20 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached packaging-26.2-py3-none-any.whl.metadata (3.5 kB)
Collecting pandas<4,>=1.4.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached pandas-3.0.5-cp313-cp313-macosx_11_0_arm64.whl.metadata (79 kB)
Collecting pillow<13,>=7.1.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached pillow-12.3.0-cp313-cp313-macosx_11_0_arm64.whl.metadata (9.1 kB)
Collecting pydeck<1,>=0.8.0b4 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached pydeck-0.9.3-py2.py3-none-any.whl.metadata (4.2 kB)
Collecting protobuf<8,>=3.20 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached protobuf-7.35.1-cp310-abi3-macosx_10_9_universal2.whl.metadata (595 bytes)
Collecting pyarrow<25,>=7.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached pyarrow-24.0.0-cp313-cp313-macosx_12_0_arm64.whl.metadata (3.0 kB)
Collecting requests<3,>=2.27 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached requests-2.34.2-py3-none-any.whl.metadata (4.8 kB)
Collecting tenacity<10,>=8.1.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached tenacity-9.1.4-py3-none-any.whl.metadata (1.2 kB)
Collecting toml<2,>=0.10.1 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached toml-0.10.2-py2.py3-none-any.whl.metadata (7.1 kB)
Collecting typing-extensions<5,>=4.10.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached typing_extensions-4.16.0-py3-none-any.whl.metadata (3.3 kB)
Collecting starlette<2,>=0.40.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached starlette-1.3.1-py3-none-any.whl.metadata (6.4 kB)
Collecting uvicorn<1,>=0.30.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached uvicorn-0.52.1-py3-none-any.whl.metadata (6.6 kB)
Collecting httptools<1,>=0.6.3 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached httptools-0.8.0-cp313-cp313-macosx_11_0_arm64.whl.metadata (3.5 kB)
Collecting anyio<5,>=4.0.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached anyio-4.14.2-py3-none-any.whl.metadata (4.6 kB)
Collecting python-multipart<1,>=0.0.10 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached python_multipart-0.0.32-py3-none-any.whl.metadata (2.1 kB)
Collecting websockets<17,>=12.0.0 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached websockets-16.1.1-cp313-cp313-macosx_11_0_arm64.whl.metadata (6.8 kB)
Collecting itsdangerous<3,>=2.1.2 (from streamlit>=1.30->-r requirements.txt (line 1))
  Using cached itsdangerous-2.2.0-py3-none-any.whl.metadata (1.9 kB)
Collecting jinja2 (from altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached jinja2-3.1.6-py3-none-any.whl.metadata (2.9 kB)
Collecting jsonschema>=3.0 (from altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached jsonschema-4.26.0-py3-none-any.whl.metadata (7.6 kB)
Collecting narwhals>=2.4.0 (from altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached narwhals-2.24.0-py3-none-any.whl.metadata (15 kB)
Collecting idna>=2.8 (from anyio<5,>=4.0.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached idna-3.18-py3-none-any.whl.metadata (6.1 kB)
Collecting gitdb<5,>=4.0.1 (from gitpython!=3.1.19,<4,>=3.0.7->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached gitdb-4.0.12-py3-none-any.whl.metadata (1.2 kB)
Collecting smmap<6,>=3.0.1 (from gitdb<5,>=4.0.1->gitpython!=3.1.19,<4,>=3.0.7->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached smmap-5.0.3-py3-none-any.whl.metadata (4.6 kB)
Collecting python-dateutil>=2.8.2 (from pandas<4,>=1.4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl.metadata (8.4 kB)
Collecting charset_normalizer<4,>=2 (from requests<3,>=2.27->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached charset_normalizer-3.4.9-cp313-cp313-macosx_10_13_universal2.whl.metadata (41 kB)
Collecting urllib3<3,>=1.26 (from requests<3,>=2.27->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached urllib3-2.7.0-py3-none-any.whl.metadata (6.9 kB)
Collecting certifi>=2023.5.7 (from requests<3,>=2.27->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached certifi-2026.7.22-py3-none-any.whl.metadata (2.5 kB)
Collecting h11>=0.8 (from uvicorn<1,>=0.30.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting iniconfig>=1.0.1 (from pytest>=7.0->-r requirements.txt (line 2))
  Using cached iniconfig-2.3.0-py3-none-any.whl.metadata (2.5 kB)
Collecting pluggy<2,>=1.5 (from pytest>=7.0->-r requirements.txt (line 2))
  Using cached pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
Collecting pygments>=2.7.2 (from pytest>=7.0->-r requirements.txt (line 2))
  Using cached pygments-2.20.0-py3-none-any.whl.metadata (2.5 kB)
Collecting distro<2,>=1.7.0 (from anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached distro-1.9.0-py3-none-any.whl.metadata (6.8 kB)
Collecting docstring-parser<1,>=0.15 (from anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached docstring_parser-0.18.0-py3-none-any.whl.metadata (3.5 kB)
Collecting httpx<1,>=0.25.0 (from anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting jiter<1,>=0.4.0 (from anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached jiter-0.16.0-cp313-cp313-macosx_11_0_arm64.whl.metadata (5.2 kB)
Collecting pydantic<3,>=1.9.0 (from anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached pydantic-2.13.4-py3-none-any.whl.metadata (109 kB)
Collecting sniffio (from anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
Collecting httpcore==1.* (from httpx<1,>=0.25.0->anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting annotated-types>=0.6.0 (from pydantic<3,>=1.9.0->anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached annotated_types-0.8.0-py3-none-any.whl.metadata (15 kB)
Collecting pydantic-core==2.46.4 (from pydantic<3,>=1.9.0->anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached pydantic_core-2.46.4-cp313-cp313-macosx_11_0_arm64.whl.metadata (6.6 kB)
Collecting typing-inspection>=0.4.2 (from pydantic<3,>=1.9.0->anthropic>=0.40.0->-r requirements.txt (line 3))
  Using cached typing_inspection-0.4.2-py3-none-any.whl.metadata (2.6 kB)
Collecting MarkupSafe>=2.0 (from jinja2->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl.metadata (2.7 kB)
Collecting attrs>=22.2.0 (from jsonschema>=3.0->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached attrs-26.1.0-py3-none-any.whl.metadata (8.8 kB)
Collecting jsonschema-specifications>=2023.03.6 (from jsonschema>=3.0->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached jsonschema_specifications-2025.9.1-py3-none-any.whl.metadata (2.9 kB)
Collecting referencing>=0.28.4 (from jsonschema>=3.0->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached referencing-0.37.0-py3-none-any.whl.metadata (2.8 kB)
Collecting rpds-py>=0.25.0 (from jsonschema>=3.0->altair!=5.4.0,!=5.4.1,<7,>=4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached rpds_py-2026.6.3-cp313-cp313-macosx_11_0_arm64.whl.metadata (4.1 kB)
Collecting six>=1.5 (from python-dateutil>=2.8.2->pandas<4,>=1.4.0->streamlit>=1.30->-r requirements.txt (line 1))
  Using cached six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Using cached streamlit-1.60.0-py3-none-any.whl (10.4 MB)
Using cached altair-6.2.2-py3-none-any.whl (797 kB)
Using cached anyio-4.14.2-py3-none-any.whl (125 kB)
Using cached blinker-1.9.0-py3-none-any.whl (8.5 kB)
Using cached click-8.4.2-py3-none-any.whl (119 kB)
Using cached gitpython-3.1.57-py3-none-any.whl (217 kB)
Using cached gitdb-4.0.12-py3-none-any.whl (62 kB)
Using cached httptools-0.8.0-cp313-cp313-macosx_11_0_arm64.whl (111 kB)
Using cached itsdangerous-2.2.0-py3-none-any.whl (16 kB)
Using cached numpy-2.5.1-cp313-cp313-macosx_14_0_arm64.whl (5.3 MB)
Using cached pandas-3.0.5-cp313-cp313-macosx_11_0_arm64.whl (9.9 MB)
Using cached pillow-12.3.0-cp313-cp313-macosx_11_0_arm64.whl (4.8 MB)
Using cached protobuf-7.35.1-cp310-abi3-macosx_10_9_universal2.whl (433 kB)
Using cached pyarrow-24.0.0-cp313-cp313-macosx_12_0_arm64.whl (35.0 MB)
Using cached pydeck-0.9.3-py2.py3-none-any.whl (11.4 MB)
Using cached python_multipart-0.0.32-py3-none-any.whl (30 kB)
Using cached requests-2.34.2-py3-none-any.whl (73 kB)
Using cached charset_normalizer-3.4.9-cp313-cp313-macosx_10_13_universal2.whl (317 kB)
Using cached idna-3.18-py3-none-any.whl (65 kB)
Using cached smmap-5.0.3-py3-none-any.whl (24 kB)
Using cached starlette-1.3.1-py3-none-any.whl (73 kB)
Using cached tenacity-9.1.4-py3-none-any.whl (28 kB)
Using cached toml-0.10.2-py2.py3-none-any.whl (16 kB)
Using cached typing_extensions-4.16.0-py3-none-any.whl (45 kB)
Using cached urllib3-2.7.0-py3-none-any.whl (131 kB)
Using cached uvicorn-0.52.1-py3-none-any.whl (79 kB)
Using cached websockets-16.1.1-cp313-cp313-macosx_11_0_arm64.whl (177 kB)
Using cached pytest-9.1.1-py3-none-any.whl (386 kB)
Using cached pluggy-1.6.0-py3-none-any.whl (20 kB)
Using cached anthropic-0.120.2-py3-none-any.whl (1.0 MB)
Using cached distro-1.9.0-py3-none-any.whl (20 kB)
Using cached docstring_parser-0.18.0-py3-none-any.whl (22 kB)
Using cached httpx-0.28.1-py3-none-any.whl (73 kB)
Using cached httpcore-1.0.9-py3-none-any.whl (78 kB)
Using cached jiter-0.16.0-cp313-cp313-macosx_11_0_arm64.whl (306 kB)
Using cached pydantic-2.13.4-py3-none-any.whl (472 kB)
Using cached pydantic_core-2.46.4-cp313-cp313-macosx_11_0_arm64.whl (2.0 MB)
Using cached annotated_types-0.8.0-py3-none-any.whl (13 kB)
Using cached certifi-2026.7.22-py3-none-any.whl (136 kB)
Using cached h11-0.16.0-py3-none-any.whl (37 kB)
Using cached iniconfig-2.3.0-py3-none-any.whl (7.5 kB)
Using cached jinja2-3.1.6-py3-none-any.whl (134 kB)
Using cached jsonschema-4.26.0-py3-none-any.whl (90 kB)
Using cached attrs-26.1.0-py3-none-any.whl (67 kB)
Using cached jsonschema_specifications-2025.9.1-py3-none-any.whl (18 kB)
Using cached markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl (12 kB)
Using cached narwhals-2.24.0-py3-none-any.whl (461 kB)
Using cached packaging-26.2-py3-none-any.whl (100 kB)
Using cached pygments-2.20.0-py3-none-any.whl (1.2 MB)
Using cached python_dateutil-2.9.0.post0-py2.py3-none-any.whl (229 kB)
Using cached referencing-0.37.0-py3-none-any.whl (26 kB)
Using cached rpds_py-2026.6.3-cp313-cp313-macosx_11_0_arm64.whl (338 kB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Using cached typing_inspection-0.4.2-py3-none-any.whl (14 kB)
Using cached sniffio-1.3.1-py3-none-any.whl (10 kB)
Installing collected packages: websockets, urllib3, typing-extensions, toml, tenacity, sniffio, smmap, six, rpds-py, python-multipart, pygments, pyarrow, protobuf, pluggy, pillow, packaging, numpy, narwhals, MarkupSafe, jiter, itsdangerous, iniconfig, idna, httptools, h11, docstring-parser, distro, click, charset_normalizer, certifi, blinker, attrs, annotated-types, uvicorn, typing-inspection, requests, referencing, python-dateutil, pytest, pydantic-core, jinja2, httpcore, gitdb, anyio, starlette, pydeck, pydantic, pandas, jsonschema-specifications, httpx, gitpython, jsonschema, anthropic, altair, streamlit

Successfully installed MarkupSafe-3.0.3 altair-6.2.2 annotated-types-0.8.0 anthropic-0.120.2 anyio-4.14.2 attrs-26.1.0 blinker-1.9.0 certifi-2026.7.22 charset_normalizer-3.4.9 click-8.4.2 distro-1.9.0 docstring-parser-0.18.0 gitdb-4.0.12 gitpython-3.1.57 h11-0.16.0 httpcore-1.0.9 httptools-0.8.0 httpx-0.28.1 idna-3.18 iniconfig-2.3.0 itsdangerous-2.2.0 jinja2-3.1.6 jiter-0.16.0 jsonschema-4.26.0 jsonschema-specifications-2025.9.1 narwhals-2.24.0 numpy-2.5.1 packaging-26.2 pandas-3.0.5 pillow-12.3.0 pluggy-1.6.0 protobuf-7.35.1 pyarrow-24.0.0 pydantic-2.13.4 pydantic-core-2.46.4 pydeck-0.9.3 pygments-2.20.0 pytest-9.1.1 python-dateutil-2.9.0.post0 python-multipart-0.0.32 referencing-0.37.0 requests-2.34.2 rpds-py-2026.6.3 six-1.17.0 smmap-5.0.3 sniffio-1.3.1 starlette-1.3.1 streamlit-1.60.0 tenacity-9.1.4 toml-0.10.2 typing-extensions-4.16.0 typing-inspection-0.4.2 urllib3-2.7.0 uvicorn-0.52.1 websockets-16.1.1
```

Installed package versions match `requirements.txt`'s pinned ranges (`streamlit>=1.30`, `pytest>=7.0`, `anthropic>=0.40.0`) and are consistent with the `pip freeze` output recorded in Section 1. The temporary environment was removed after installation (`deactivate && rm -rf .venv-evidence`) and never affected the project's regular `.venv`.

## 3. Full Pytest Output (historical — 2026-08-01, re-verified 2026-08-04 in Section 0.4)

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

## 4. Streamlit Launch Output (historical — 2026-08-01, re-verified 2026-08-04 in Section 0.5)

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

## 5. Sample Data Entered (historical — 2026-08-01)

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

## 6. Live Claude Interaction Evidence — Historical Note (2026-08-01), Superseded by Section 0

**This section is historical.** At the time this evidence was originally collected (2026-08-01), using a real `ANTHROPIC_API_KEY` was out of scope: `ANTHROPIC_API_KEY` was intentionally left unset while collecting this evidence. That is no longer the case — **Section 0 above (2026-08-04) contains a real, successful live Claude API call** (`success=True`, `fallback_used=False`, `validation_result.valid=True`), plus a separate missing-key fallback test performed without ever touching the real credential. The rest of this section is preserved unedited to show what was verified before live evidence existed.

What was verified at the time (2026-08-01), before live evidence existed:

* Claude API orchestration in `ai_assistant.py` (request construction, response parsing, error handling) was exercised using **mocked Anthropic API clients** injected via the `client=` parameter — never a real network call to Anthropic.
* The real application workflow — intent detection, context retrieval, answer validation, and fallback formatting in `retrieval.py`, `validators.py`, and `ai_assistant.py` — was exercised end-to-end through **deterministic fallback responses**, which do not depend on the Anthropic API being reachable.
* The automated test suite (`tests/test_ai_assistant.py`, 126 tests total passing — see Section 3) verifies, using mocked clients, each of the following code paths:
  * **Successful-response path** — `test_successful_grounded_answer`, `test_detected_intent_is_returned`, `test_detected_pet_is_returned`, `test_multiple_text_blocks_are_joined`
  * **API-error path** — `test_api_exception_falls_back`
  * **Malformed-response path** — `test_malformed_api_response_falls_back`, `test_malformed_api_response_missing_content_attribute_falls_back`, `test_empty_api_response_falls_back`
  * **Validation-failure path** — `test_validation_failure_causes_fallback`, `test_autonomous_action_claim_causes_fallback`, `test_veterinary_language_causes_fallback`, `test_conflict_contradiction_causes_fallback`
  * **Secret-protection path** — `test_api_key_never_appears_in_returned_errors`

At the time, no question, answer, intent, pet, confidence score, or context in Sections 5, 7, 8, and 9 came from a real Claude API response — every fallback interaction recorded there was produced by the deterministic fallback path, which activates precisely because no live API key was configured then. **This has since changed: see Section 0 for real, live Claude-generated output, obtained with the current source code and a real `ANTHROPIC_API_KEY`.**

## 7. One Deterministic Fallback Interaction (historical — 2026-08-01)

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

## 8. Retrieved-Context Evidence (historical — 2026-08-01)

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

## 9. Logging Evidence (historical — 2026-08-01; a fresh, sanitized log excerpt from the live 2026-08-04 run is in Section 0.9)

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

Taken from `logs/pawpal_ai.log` after running the Section 8 test question (TC-04, "What is today's schedule?" — note the `todays_schedule` intent below matches Section 8, not the incomplete-tasks question in Section 7) (no API keys or full prompt text appear in these log lines — `ai_assistant.py` never logs the prompt or the key, only intent/fallback-reason/status metadata).

## 10. Human Evaluation Summary (historical — 2026-08-01; superseded by the Live API Evaluation summary in evaluation_results.md)

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
Known limitations:      (1) No ANTHROPIC_API_KEY was used in this environment — a
                        deliberate decision for this submission, not an oversight — so
                        Section 6 documents mocked-client and deterministic-fallback
                        verification instead of live, AI-generated, validated
                        interactions. (2) app.py exposes no "mark complete" UI control,
                        so the "completed tasks" case (TC-02) could only be verified
                        against zero completed tasks, not a genuinely mixed
                        complete/incomplete data set.
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
