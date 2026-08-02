from datetime import date

import pytest

import ai_assistant
from pawpal_system import Owner, Pet, Task
from retrieval import (
    INTENT_INCOMPLETE_TASKS,
    INTENT_PET_TASKS,
    INTENT_CONFLICTS,
)

REFERENCE_DATE = date(2026, 1, 15)
PAST_DATE = date(2026, 1, 10)
YESTERDAY = date(2026, 1, 14)


# ---------------------------------------------------------------------------
# Fixtures / fake Claude client
# ---------------------------------------------------------------------------


def build_owner():
    """Owner with one pet and a mix of incomplete/completed tasks."""
    owner = Owner(available_time="2 hours", preferred_times=["morning"], task_priorities=["feeding"])
    biscuit = Pet(name="Biscuit", species="Dog", age=4, needs=["walking"])
    owner.add_pet(biscuit)
    biscuit.add_task(Task("Morning walk", "07:00", "daily", due_date=REFERENCE_DATE))
    biscuit.add_task(Task("Vet checkup", "10:00", "weekly", due_date=PAST_DATE))
    biscuit.add_task(Task("Grooming", "11:00", "weekly", completed=True, due_date=YESTERDAY))
    return owner


def build_owner_all_completed():
    """Owner whose only task is already completed -> zero incomplete records."""
    owner = Owner(available_time="1 hour", preferred_times=[], task_priorities=[])
    milo = Pet(name="Milo", species="Cat", age=3, needs=[])
    owner.add_pet(milo)
    milo.add_task(Task("Feed breakfast", "08:00", "daily", completed=True, due_date=PAST_DATE))
    return owner


def build_owner_with_conflict():
    """Owner with two incomplete tasks due at the same time today -> a conflict."""
    owner = Owner(available_time="1 hour", preferred_times=[], task_priorities=[])
    rex = Pet(name="Rex", species="Dog", age=5, needs=[])
    owner.add_pet(rex)
    rex.add_task(Task("Walk", "07:00", "daily", due_date=REFERENCE_DATE))
    rex.add_task(Task("Play", "07:00", "weekly", due_date=REFERENCE_DATE))
    return owner


def snapshot(owner):
    """Capture enough state to detect any mutation caused by answer_question()."""
    return [
        (pet.name, pet.species, pet.age, tuple(pet.needs),
         [(t.description, t.time, t.frequency, t.due_date, t.completed) for t in pet.tasks])
        for pet in owner.pets
    ]


class FakeTextBlock:
    def __init__(self, text, block_type="text"):
        self.type = block_type
        self.text = text


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeMessages:
    def __init__(self, response=None, exception=None):
        self._response = response
        self._exception = exception
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self._exception is not None:
            raise self._exception
        return self._response


class FakeClient:
    def __init__(self, response=None, exception=None):
        self.messages = FakeMessages(response=response, exception=exception)

    @property
    def calls(self):
        return self.messages.calls


def make_client(text):
    """A fake client whose single text block is `text`."""
    return FakeClient(response=FakeResponse([FakeTextBlock(text)]))


# ---------------------------------------------------------------------------
# 1-3: blank / unsupported questions never reach the API
# ---------------------------------------------------------------------------


def test_blank_question_returns_fallback():
    owner = build_owner()
    result = ai_assistant.answer_question("", owner, reference_date=REFERENCE_DATE)

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_BLANK_QUESTION
    assert result["success"] is False
    assert result["answer"]


def test_unsupported_question_returns_fallback():
    owner = build_owner()
    result = ai_assistant.answer_question(
        "What's the weather like today?", owner, reference_date=REFERENCE_DATE
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_UNSUPPORTED_QUESTION
    assert result["answer"]


def test_unsupported_question_does_not_call_api():
    owner = build_owner()
    client = make_client("This should never be returned.")

    ai_assistant.answer_question(
        "What's the weather like today?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert client.calls == []


# ---------------------------------------------------------------------------
# 4-8: successful grounded answer and the fields that come with it
# ---------------------------------------------------------------------------


def test_successful_grounded_answer():
    owner = build_owner()
    client = make_client("Biscuit has a morning walk and a vet checkup still to do.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["success"] is True
    assert result["fallback_used"] is False
    assert result["answer"] == "Biscuit has a morning walk and a vet checkup still to do."
    assert len(client.calls) == 1


def test_detected_intent_is_returned():
    owner = build_owner()
    client = make_client("Here are your incomplete tasks.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["intent"] == INTENT_INCOMPLETE_TASKS


def test_detected_pet_is_returned():
    owner = build_owner()
    client = make_client("Biscuit still needs a morning walk and a vet checkup.")

    result = ai_assistant.answer_question(
        "What tasks does Biscuit have?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["intent"] == INTENT_PET_TASKS
    assert result["detected_pet"] == "Biscuit"


def test_retrieval_result_is_included():
    owner = build_owner()
    client = make_client("Here are your incomplete tasks.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["retrieval_result"] is not None
    assert result["retrieval_result"]["intent"] == INTENT_INCOMPLETE_TASKS
    assert len(result["retrieval_result"]["records"]) == 2


def test_validation_result_is_included():
    owner = build_owner()
    client = make_client("Here are your incomplete tasks.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["validation_result"] is not None
    assert result["validation_result"]["valid"] is True


# ---------------------------------------------------------------------------
# 9-10: API key resolution
# ---------------------------------------------------------------------------


def test_missing_api_key_falls_back(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    owner = build_owner()

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=None
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_MISSING_API_KEY
    assert result["answer"]


def test_injected_client_works_without_env_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    owner = build_owner()
    client = make_client("Biscuit still needs a morning walk and a vet checkup.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["success"] is True
    assert result["fallback_used"] is False


# ---------------------------------------------------------------------------
# 11-14: Claude response handling
# ---------------------------------------------------------------------------


def test_api_exception_falls_back():
    owner = build_owner()
    client = FakeClient(exception=RuntimeError("connection reset"))

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_API_ERROR
    assert result["answer"]


def test_empty_api_response_falls_back():
    owner = build_owner()
    client = FakeClient(response=FakeResponse([]))

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_EMPTY_RESPONSE
    assert result["answer"]


def test_malformed_api_response_falls_back():
    owner = build_owner()
    # Content blocks with no usable text, and a response missing `.content` entirely.
    client = FakeClient(response=FakeResponse([FakeTextBlock(None), object()]))

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_RESPONSE_PARSE_ERROR
    assert result["answer"]


def test_malformed_api_response_missing_content_attribute_falls_back():
    owner = build_owner()

    class NoContentResponse:
        pass

    client = FakeClient(response=NoContentResponse())

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_RESPONSE_PARSE_ERROR


def test_multiple_text_blocks_are_joined():
    owner = build_owner()
    client = FakeClient(
        response=FakeResponse(
            [FakeTextBlock("Biscuit has two incomplete tasks:"), FakeTextBlock("a walk and a checkup.")]
        )
    )

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["success"] is True
    assert "Biscuit has two incomplete tasks:" in result["answer"]
    assert "a walk and a checkup." in result["answer"]


# ---------------------------------------------------------------------------
# 15-18: validation failures trigger fallback
# ---------------------------------------------------------------------------


def test_validation_failure_causes_fallback():
    owner = build_owner()
    # Claims an incomplete task is already completed - a completion-status contradiction.
    client = make_client("The morning walk is completed and Biscuit still has a vet checkup.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_VALIDATION_FAILED
    assert result["validation_result"]["valid"] is False


def test_autonomous_action_claim_causes_fallback():
    owner = build_owner()
    client = make_client("I marked the morning walk as complete for you.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_VALIDATION_FAILED


def test_veterinary_language_causes_fallback():
    owner = build_owner()
    client = make_client("Based on these symptoms, this is a diagnosis of an ear infection.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_VALIDATION_FAILED


def test_conflict_contradiction_causes_fallback():
    owner = build_owner_with_conflict()
    client = make_client("There are no conflicts in today's schedule.")

    result = ai_assistant.answer_question(
        "Do I have any conflicts today?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["intent"] == INTENT_CONFLICTS
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_VALIDATION_FAILED


# ---------------------------------------------------------------------------
# 19-20: no-context / unknown-pet behavior skips the API entirely
# ---------------------------------------------------------------------------


def test_no_context_result_skips_the_api():
    owner = build_owner_all_completed()
    client = make_client("This should never be returned.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_NO_CONTEXT
    assert client.calls == []
    assert "no incomplete tasks" in result["answer"].lower()


def test_unknown_pet_returns_safe_fallback():
    owner = build_owner()
    client = make_client("This should never be returned.")

    result = ai_assistant.answer_question(
        "What tasks does Waffles have?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["intent"] == INTENT_PET_TASKS
    assert result["detected_pet"] is None
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == ai_assistant.FALLBACK_NO_CONTEXT
    assert client.calls == []
    assert "no matching pet" in result["answer"].lower()


# ---------------------------------------------------------------------------
# 21: fallback reasons use the documented stable string values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "reason_constant, expected_value",
    [
        (ai_assistant.FALLBACK_BLANK_QUESTION, "blank_question"),
        (ai_assistant.FALLBACK_UNSUPPORTED_QUESTION, "unsupported_question"),
        (ai_assistant.FALLBACK_NO_CONTEXT, "no_context"),
        (ai_assistant.FALLBACK_MISSING_API_KEY, "missing_api_key"),
        (ai_assistant.FALLBACK_API_ERROR, "api_error"),
        (ai_assistant.FALLBACK_EMPTY_RESPONSE, "empty_response"),
        (ai_assistant.FALLBACK_RESPONSE_PARSE_ERROR, "response_parse_error"),
        (ai_assistant.FALLBACK_VALIDATION_FAILED, "validation_failed"),
    ],
)
def test_fallback_reason_stable_values(reason_constant, expected_value):
    assert reason_constant == expected_value


# ---------------------------------------------------------------------------
# 22: read-only guarantee
# ---------------------------------------------------------------------------


def test_owner_pet_task_objects_are_not_mutated():
    owner = build_owner()
    before = snapshot(owner)
    client = make_client("Biscuit still needs a morning walk and a vet checkup.")

    ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )
    ai_assistant.answer_question(
        "What tasks does Biscuit have?", owner, reference_date=REFERENCE_DATE, client=client
    )
    ai_assistant.answer_question("", owner, reference_date=REFERENCE_DATE)
    ai_assistant.answer_question(
        "What's the capital of France?", owner, reference_date=REFERENCE_DATE
    )

    assert snapshot(owner) == before


# ---------------------------------------------------------------------------
# 23: secrets never leak into the returned result
# ---------------------------------------------------------------------------


def test_api_key_never_appears_in_returned_errors(monkeypatch):
    secret = "sk-ant-super-secret-value-should-not-leak"
    monkeypatch.setenv("ANTHROPIC_API_KEY", secret)
    owner = build_owner()
    client = FakeClient(exception=RuntimeError(f"authentication failed for key {secret}"))

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    result_text = repr(result)
    assert secret not in result_text
    assert secret not in (result["error"] or "")


# ---------------------------------------------------------------------------
# 24-25: model configuration
# ---------------------------------------------------------------------------


def test_model_configurable_via_function_parameter():
    owner = build_owner()
    client = make_client("Biscuit still needs a morning walk and a vet checkup.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?",
        owner,
        reference_date=REFERENCE_DATE,
        client=client,
        model="claude-test-model-x",
    )

    assert result["model"] == "claude-test-model-x"
    assert client.calls[0]["model"] == "claude-test-model-x"


def test_model_configurable_via_environment_variable(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-env-model-y")
    owner = build_owner()
    client = make_client("Biscuit still needs a morning walk and a vet checkup.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["model"] == "claude-env-model-y"
    assert client.calls[0]["model"] == "claude-env-model-y"


def test_function_parameter_model_overrides_environment_variable(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-env-model-y")
    owner = build_owner()
    client = make_client("Biscuit still needs a morning walk and a vet checkup.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?",
        owner,
        reference_date=REFERENCE_DATE,
        client=client,
        model="claude-explicit-model-z",
    )

    assert result["model"] == "claude-explicit-model-z"


def test_default_model_used_when_unconfigured(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    owner = build_owner()
    client = make_client("Biscuit still needs a morning walk and a vet checkup.")

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE, client=client
    )

    assert result["model"] == ai_assistant.DEFAULT_MODEL


# ---------------------------------------------------------------------------
# 26: fallback answers are still readable
# ---------------------------------------------------------------------------


def test_normal_fallback_produces_readable_answer():
    owner = build_owner_all_completed()

    result = ai_assistant.answer_question(
        "What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE
    )

    assert result["fallback_used"] is True
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 0
    assert "incomplete tasks" in result["answer"].lower()
