"""Tests for logger_config.py and the logging integrated into retrieval.py,
validators.py, and ai_assistant.py.

Every test rewires logger_config to a temporary log directory and resets the
shared "pawpal_ai" logger's handlers before and after each test, so nothing
here depends on, or writes to, the project's real logs/ directory. Log
content is asserted by reading the temporary log file directly rather than
via pytest's caplog fixture: pytest's log capture attaches its own handler
to any non-propagating logger (ours intentionally sets propagate=False), and
that handler would otherwise mask whether get_logger() itself really wired
up handlers. All Claude API behavior stays mocked, matching the rest of the
test suite.
"""

import logging
from datetime import date

import pytest

import ai_assistant
import logger_config
import retrieval
import validators
from pawpal_system import Owner, Pet, Task

REFERENCE_DATE = date(2026, 1, 15)
PAST_DATE = date(2026, 1, 10)


# ---------------------------------------------------------------------------
# Isolation fixture: temp log directory, clean handler state per test
# ---------------------------------------------------------------------------


def _clear_handlers(target_logger):
    for handler in list(target_logger.handlers):
        target_logger.removeHandler(handler)
        handler.close()


@pytest.fixture(autouse=True)
def isolated_logger(monkeypatch, tmp_path):
    """Reset the shared app logger and point it at a temp directory so these
    tests never touch the real logs/ directory or leak handlers between
    tests."""
    _clear_handlers(logging.getLogger(logger_config._APP_LOGGER_NAME))
    logger_config._configured = False

    temp_log_dir = tmp_path / "logs"
    monkeypatch.setattr(logger_config, "LOG_DIR", str(temp_log_dir))

    yield temp_log_dir

    _clear_handlers(logging.getLogger(logger_config._APP_LOGGER_NAME))
    logger_config._configured = False


def _force_configuration():
    """Trigger real (re)configuration of the shared app logger so it writes
    to this test's temporary log directory instead of doing nothing."""
    logger_config.get_logger("_bootstrap")


def _read_log_file(log_dir):
    for handler in logging.getLogger(logger_config._APP_LOGGER_NAME).handlers:
        handler.flush()
    log_file = log_dir / logger_config.LOG_FILE_NAME
    return log_file.read_text(encoding="utf-8") if log_file.exists() else ""


# ---------------------------------------------------------------------------
# Fixtures: owners and a fake Claude client (mirrors tests/test_ai_assistant.py)
# ---------------------------------------------------------------------------


def _build_owner():
    owner = Owner(available_time="2 hours", preferred_times=["morning"], task_priorities=["feeding"])
    biscuit = Pet(name="Biscuit", species="Dog", age=4, needs=["walking"])
    owner.add_pet(biscuit)
    biscuit.add_task(Task("Morning walk", "07:00", "daily", due_date=REFERENCE_DATE))
    biscuit.add_task(Task("Vet checkup", "10:00", "weekly", due_date=PAST_DATE))
    return owner


def _build_owner_all_completed():
    owner = Owner(available_time="1 hour", preferred_times=[], task_priorities=[])
    milo = Pet(name="Milo", species="Cat", age=3, needs=[])
    owner.add_pet(milo)
    milo.add_task(Task("Feed breakfast", "08:00", "daily", completed=True, due_date=PAST_DATE))
    return owner


def _snapshot(owner):
    return [
        (pet.name, pet.species, pet.age, tuple(pet.needs),
         [(t.description, t.time, t.frequency, t.due_date, t.completed) for t in pet.tasks])
        for pet in owner.pets
    ]


class _FakeTextBlock:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _FakeResponse:
    def __init__(self, content):
        self.content = content


class _FakeMessages:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception

    def create(self, **kwargs):
        if self._exception is not None:
            raise self._exception
        return self._response


class _FakeClient:
    def __init__(self, response=None, exception=None):
        self.messages = _FakeMessages(response=response, exception=exception)


def _make_client(text):
    return _FakeClient(response=_FakeResponse([_FakeTextBlock(text)]))


# ---------------------------------------------------------------------------
# 1-2: get_logger() basics and duplicate-handler avoidance
# ---------------------------------------------------------------------------


def test_get_logger_returns_a_logger():
    logger = logger_config.get_logger("sample")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "pawpal_ai.sample"


def test_repeated_calls_do_not_duplicate_handlers():
    # Snapshot first: pytest's own log-capture handler attaches itself to any
    # non-propagating logger (ours is one, by design) before the test body
    # runs, so we compare against a baseline instead of an absolute count.
    app_logger = logging.getLogger(logger_config._APP_LOGGER_NAME)
    pre_existing = list(app_logger.handlers)

    logger_config.get_logger("module_a")
    logger_config.get_logger("module_b")
    logger_config.get_logger("module_a")

    added = [h for h in app_logger.handlers if h not in pre_existing]
    assert len(added) == 2  # one console handler, one file handler

    for _ in range(10):
        logger_config.get_logger("module_a")
        logger_config.get_logger("module_c")

    still_added = [h for h in app_logger.handlers if h not in pre_existing]
    assert len(still_added) == len(added)


# ---------------------------------------------------------------------------
# 3-4: file creation and writing, scoped to a temp directory
# ---------------------------------------------------------------------------


def test_log_file_created_in_temp_directory(isolated_logger):
    logger_config.get_logger("file_creation")

    log_file = isolated_logger / logger_config.LOG_FILE_NAME
    assert log_file.exists()


def test_messages_can_be_written_to_file(isolated_logger):
    logger = logger_config.get_logger("write_test")
    logger.info("hello from the test suite")

    content = _read_log_file(isolated_logger)
    assert "hello from the test suite" in content


# ---------------------------------------------------------------------------
# 5: retrieval.py logs detected intent and record count
# ---------------------------------------------------------------------------


def test_retrieval_logs_detected_intent_and_record_count(isolated_logger):
    _force_configuration()
    owner = _build_owner()

    result = retrieval.retrieve_context(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE
    )

    content = _read_log_file(isolated_logger)
    assert len(result["records"]) == 2
    assert "Detected intent: incomplete_tasks" in content
    assert "Retrieval completed with 2 record(s)." in content


def test_retrieval_logs_no_matching_records(isolated_logger):
    _force_configuration()
    owner = _build_owner_all_completed()

    retrieval.retrieve_context(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE
    )

    content = _read_log_file(isolated_logger)
    assert "No matching records were found." in content


# ---------------------------------------------------------------------------
# 6: validators.py logs pass/fail outcomes
# ---------------------------------------------------------------------------


def test_validation_logs_pass_and_failure_outcomes(isolated_logger):
    _force_configuration()
    retrieval_result = {
        "intent": retrieval.INTENT_INCOMPLETE_TASKS,
        "records": [],
        "detected_pet": None,
    }

    validators.validate_answer("There are no incomplete tasks.", retrieval_result)
    validators.validate_answer("I marked the task as complete for you.", retrieval_result)

    content = _read_log_file(isolated_logger)
    assert "Validation passed" in content
    assert "Validation failed" in content
    assert "issue_count=1" in content


# ---------------------------------------------------------------------------
# 7: ai_assistant.py logs deterministic fallback usage
# ---------------------------------------------------------------------------


def test_ai_assistant_logs_fallback_usage(isolated_logger):
    _force_configuration()
    owner = _build_owner_all_completed()

    ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE
    )

    content = _read_log_file(isolated_logger)
    assert "Deterministic fallback used" in content
    assert "fallback_reason=no_context" in content


# ---------------------------------------------------------------------------
# 8-9: secrets never appear in logs
# ---------------------------------------------------------------------------


def test_api_failure_logs_do_not_expose_raw_exception(isolated_logger, monkeypatch):
    _force_configuration()
    secret = "sk-ant-super-secret-value-should-not-leak"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    owner = _build_owner()
    client = _FakeClient(exception=RuntimeError(f"authentication failed for key {secret}"))

    ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    content = _read_log_file(isolated_logger)
    assert secret not in content
    assert "RuntimeError" in content
    assert "Claude API request failed" in content


def test_api_keys_do_not_appear_in_captured_logs(isolated_logger, monkeypatch):
    _force_configuration()
    secret = "sk-ant-another-secret-value"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    owner = _build_owner()
    client = _make_client("Biscuit has a walk and a checkup left.")

    ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    content = _read_log_file(isolated_logger)
    assert secret not in content


# ---------------------------------------------------------------------------
# 10: full prompts / complete context text are never logged
# ---------------------------------------------------------------------------


def test_full_prompt_and_context_not_logged(isolated_logger):
    _force_configuration()
    owner = _build_owner()
    question = "What are my incomplete tasks?"
    client = _make_client("Biscuit has a walk and a checkup left.")

    ai_assistant.answer_question(question, owner, reference_date=REFERENCE_DATE, client=client)

    content = _read_log_file(isolated_logger)
    assert question not in content
    assert "Morning walk" not in content
    assert "Vet checkup" not in content


# ---------------------------------------------------------------------------
# 11: logging never mutates retrieval results or PawPal+ objects
# ---------------------------------------------------------------------------


def test_logging_does_not_mutate_owner_or_retrieval_result(isolated_logger):
    _force_configuration()
    owner = _build_owner()
    before = _snapshot(owner)

    result_one = retrieval.retrieve_context(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE
    )
    result_two = retrieval.retrieve_context(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE
    )

    assert _snapshot(owner) == before
    assert result_one == result_two


# ---------------------------------------------------------------------------
# 12: a broken log directory/file never crashes the application
# ---------------------------------------------------------------------------


def test_file_handler_setup_failure_does_not_crash(monkeypatch):
    app_logger = logging.getLogger(logger_config._APP_LOGGER_NAME)
    pre_existing = list(app_logger.handlers)

    def _raise_os_error(*args, **kwargs):
        raise OSError("simulated permission failure")

    monkeypatch.setattr(logger_config.os, "makedirs", _raise_os_error)

    logger = logger_config.get_logger("resilient")
    logger.info("this should not raise even though the log directory is unavailable")

    added = [h for h in app_logger.handlers if h not in pre_existing]
    assert len(added) == 1  # console handler only, no file handler
