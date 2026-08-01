from datetime import date

import pytest

from pawpal_system import Owner, Pet, Task
from retrieval import (
    detect_intent,
    detect_pet,
    retrieve_context,
    INTENT_INCOMPLETE_TASKS,
    INTENT_COMPLETED_TASKS,
    INTENT_PET_TASKS,
    INTENT_TODAYS_SCHEDULE,
    INTENT_CONFLICTS,
    INTENT_NEXT_TASK,
    INTENT_UNSUPPORTED,
)

REFERENCE_DATE = date(2026, 1, 15)
PAST_DATE = date(2026, 1, 10)
FUTURE_DATE = date(2026, 1, 20)
YESTERDAY = date(2026, 1, 14)


def build_owner():
    """Fresh, deterministic fixture: two pets with a mix of task states."""
    owner = Owner(available_time="2 hours", preferred_times=["morning"], task_priorities=["feeding"])

    biscuit = Pet(name="Biscuit", species="Dog", age=4, needs=["walking"])
    whiskers = Pet(name="Whiskers", species="Cat", age=2, needs=["feeding"])
    owner.add_pet(biscuit)
    owner.add_pet(whiskers)

    biscuit.add_task(Task("Morning walk", "07:00", "daily", due_date=REFERENCE_DATE))
    biscuit.add_task(Task("Vet visit", "10:00", "weekly", due_date=PAST_DATE))
    biscuit.add_task(Task("Bath", "09:00", "monthly", due_date=FUTURE_DATE))
    biscuit.add_task(Task("Grooming", "11:00", "weekly", completed=True, due_date=YESTERDAY))

    whiskers.add_task(Task("Feed breakfast", "07:00", "daily", due_date=REFERENCE_DATE))
    whiskers.add_task(Task("Litter box", "not-a-time", "daily", due_date=REFERENCE_DATE))
    whiskers.add_task(Task("Vaccine", "08:00", "monthly", completed=True, due_date=PAST_DATE))

    return owner


def build_owner_with_empty_pet():
    owner = build_owner()
    owner.add_pet(Pet(name="Nemo", species="Fish", age=1, needs=[]))
    return owner


def build_owner_no_pets():
    return Owner(available_time="1 hour", preferred_times=[], task_priorities=[])


def snapshot(owner):
    """Capture enough state to detect any mutation caused by retrieval."""
    return [
        (pet.name, [(t.description, t.time, t.frequency, t.due_date, t.completed) for t in pet.tasks])
        for pet in owner.pets
    ]


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("question, expected", [
    ("What are my incomplete tasks?", INTENT_INCOMPLETE_TASKS),
    ("Show me pending tasks", INTENT_INCOMPLETE_TASKS),
    ("What tasks have been completed?", INTENT_COMPLETED_TASKS),
    ("What tasks does Biscuit have?", INTENT_PET_TASKS),
    ("What is today's schedule?", INTENT_TODAYS_SCHEDULE),
    ("what is todays schedule", INTENT_TODAYS_SCHEDULE),
    ("Are there any conflicts?", INTENT_CONFLICTS),
    ("What's my next task?", INTENT_NEXT_TASK),
    ("What's the weather today?", INTENT_UNSUPPORTED),
])
def test_detect_intent_for_each_supported_type(question, expected):
    assert detect_intent(question) == expected


def test_detect_intent_handles_capitalization():
    assert detect_intent("INCOMPLETE TASKS") == INTENT_INCOMPLETE_TASKS


def test_detect_intent_handles_surrounding_whitespace():
    assert detect_intent("   completed tasks   ") == INTENT_COMPLETED_TASKS


def test_detect_intent_unsupported_question():
    assert detect_intent("What is the capital of France?") == INTENT_UNSUPPORTED


def test_detect_intent_blank_question():
    assert detect_intent("") == INTENT_UNSUPPORTED
    assert detect_intent("   ") == INTENT_UNSUPPORTED


def test_detect_intent_none_question():
    assert detect_intent(None) == INTENT_UNSUPPORTED


# ---------------------------------------------------------------------------
# Pet detection
# ---------------------------------------------------------------------------

def test_detect_pet_case_insensitive_returns_stored_name():
    owner = build_owner()
    assert detect_pet("what tasks does biscuit have", owner) == "Biscuit"
    assert detect_pet("WHISKERS tasks please", owner) == "Whiskers"


def test_detect_pet_unknown_name_returns_none():
    owner = build_owner()
    assert detect_pet("what tasks does Rex have", owner) is None


def test_detect_pet_no_pets_returns_none():
    owner = build_owner_no_pets()
    assert detect_pet("what tasks does Biscuit have", owner) is None


# ---------------------------------------------------------------------------
# Blank / unsupported questions
# ---------------------------------------------------------------------------

def test_retrieve_context_blank_question():
    owner = build_owner()
    result = retrieve_context("   ", owner, reference_date=REFERENCE_DATE)
    assert result["supported"] is False
    assert result["records"] == []
    assert result["message"]
    assert result["context_text"]


def test_retrieve_context_unsupported_question():
    owner = build_owner()
    result = retrieve_context("What's the weather like?", owner, reference_date=REFERENCE_DATE)
    assert result["intent"] == INTENT_UNSUPPORTED
    assert result["supported"] is False
    assert result["records"] == []


# ---------------------------------------------------------------------------
# Incomplete / completed tasks
# ---------------------------------------------------------------------------

def test_incomplete_tasks_retrieval():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)

    assert result["intent"] == INTENT_INCOMPLETE_TASKS
    assert result["supported"] is True
    descriptions = [r["description"] for r in result["records"]]
    assert descriptions == ["Morning walk", "Feed breakfast", "Bath", "Vet visit", "Litter box"]
    assert all(r["completed"] is False for r in result["records"])


def test_completed_tasks_retrieval():
    owner = build_owner()
    result = retrieve_context("What tasks have been completed?", owner, reference_date=REFERENCE_DATE)

    assert result["intent"] == INTENT_COMPLETED_TASKS
    descriptions = [r["description"] for r in result["records"]]
    assert descriptions == ["Vaccine", "Grooming"]
    assert all(r["completed"] is True for r in result["records"])


# ---------------------------------------------------------------------------
# Pet-specific tasks
# ---------------------------------------------------------------------------

def test_pet_specific_tasks_retrieval():
    owner = build_owner()
    result = retrieve_context("What tasks does Biscuit have?", owner, reference_date=REFERENCE_DATE)

    assert result["intent"] == INTENT_PET_TASKS
    assert result["detected_pet"] == "Biscuit"
    descriptions = [r["description"] for r in result["records"]]
    assert descriptions == ["Morning walk", "Bath", "Vet visit", "Grooming"]
    assert all(r["pet_name"] == "Biscuit" for r in result["records"])


def test_pet_specific_tasks_case_insensitive_match():
    owner = build_owner()
    result = retrieve_context("what tasks does biscuit have", owner, reference_date=REFERENCE_DATE)
    assert result["detected_pet"] == "Biscuit"
    assert len(result["records"]) == 4


def test_pet_specific_tasks_unknown_pet():
    owner = build_owner()
    result = retrieve_context("What tasks does Rex have?", owner, reference_date=REFERENCE_DATE)

    assert result["intent"] == INTENT_PET_TASKS
    assert result["detected_pet"] is None
    assert result["records"] == []
    assert result["message"]


def test_pet_with_no_tasks():
    owner = build_owner_with_empty_pet()
    result = retrieve_context("What tasks does Nemo have?", owner, reference_date=REFERENCE_DATE)

    assert result["detected_pet"] == "Nemo"
    assert result["records"] == []
    assert result["message"]


# ---------------------------------------------------------------------------
# Today's schedule
# ---------------------------------------------------------------------------

def test_todays_schedule_excludes_future_tasks():
    owner = build_owner()
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)

    descriptions = [r["description"] for r in result["records"]]
    assert "Bath" not in descriptions  # due FUTURE_DATE


def test_todays_schedule_includes_overdue_tasks():
    owner = build_owner()
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)

    descriptions = [r["description"] for r in result["records"]]
    assert "Vet visit" in descriptions  # due PAST_DATE, still incomplete


def test_todays_schedule_chronological_ordering():
    owner = build_owner()
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)

    descriptions = [r["description"] for r in result["records"]]
    assert descriptions == ["Morning walk", "Feed breakfast", "Vet visit", "Litter box"]


def test_todays_schedule_invalid_time_sorts_last():
    owner = build_owner()
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)

    assert result["records"][-1]["description"] == "Litter box"
    assert result["records"][-1]["time"] == "not-a-time"


def test_todays_schedule_excludes_completed_tasks():
    owner = build_owner()
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)

    descriptions = [r["description"] for r in result["records"]]
    assert "Vaccine" not in descriptions
    assert "Grooming" not in descriptions


def test_todays_schedule_no_due_tasks():
    owner = build_owner_no_pets()
    owner.add_pet(Pet(name="Nemo", species="Fish", age=1, needs=[]))
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)

    assert result["records"] == []
    assert result["message"]


# ---------------------------------------------------------------------------
# Next task
# ---------------------------------------------------------------------------

def test_next_task_retrieval():
    owner = build_owner()
    result = retrieve_context("What's my next task?", owner, reference_date=REFERENCE_DATE)

    assert result["intent"] == INTENT_NEXT_TASK
    assert len(result["records"]) == 1
    assert result["records"][0]["description"] == "Morning walk"


def test_next_task_none_qualifies():
    owner = Owner(available_time="1 hour", preferred_times=[], task_priorities=[])
    pet = Pet(name="Biscuit", species="Dog", age=4, needs=[])
    owner.add_pet(pet)
    pet.add_task(Task("Bath", "09:00", "monthly", due_date=FUTURE_DATE))

    result = retrieve_context("What's my next task?", owner, reference_date=REFERENCE_DATE)

    assert result["records"] == []
    assert result["message"]


# ---------------------------------------------------------------------------
# Conflicts
# ---------------------------------------------------------------------------

def test_conflicts_retrieval_uses_scheduler_logic():
    owner = build_owner()
    result = retrieve_context("Are there any conflicts?", owner, reference_date=REFERENCE_DATE)

    assert result["intent"] == INTENT_CONFLICTS
    assert len(result["records"]) == 1
    conflict = result["records"][0]
    assert conflict["time"] == "07:00"
    conflicting_descriptions = {t["description"] for t in conflict["tasks"]}
    assert conflicting_descriptions == {"Morning walk", "Feed breakfast"}


def test_conflicts_none_found():
    owner = Owner(available_time="1 hour", preferred_times=[], task_priorities=[])
    pet = Pet(name="Biscuit", species="Dog", age=4, needs=[])
    owner.add_pet(pet)
    pet.add_task(Task("Morning walk", "07:00", "daily", due_date=REFERENCE_DATE))

    result = retrieve_context("Are there any conflicts?", owner, reference_date=REFERENCE_DATE)

    assert result["records"] == []
    assert result["message"]


# ---------------------------------------------------------------------------
# Owner with no pets
# ---------------------------------------------------------------------------

def test_owner_with_no_pets_is_handled_safely():
    owner = build_owner_no_pets()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)

    assert result["supported"] is True
    assert result["records"] == []
    assert result["message"]
    assert result["context_text"]


# ---------------------------------------------------------------------------
# No mutation
# ---------------------------------------------------------------------------

def test_retrieval_does_not_mutate_owner_state():
    owner = build_owner()
    before = snapshot(owner)

    questions = [
        "What are my incomplete tasks?",
        "What tasks have been completed?",
        "What tasks does Biscuit have?",
        "What is today's schedule?",
        "Are there any conflicts?",
        "What's my next task?",
        "unsupported question",
        "",
    ]
    for question in questions:
        retrieve_context(question, owner, reference_date=REFERENCE_DATE)

    after = snapshot(owner)
    assert before == after
    assert len(owner.pets) == 2


def test_retrieve_context_default_reference_date_is_today():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner)
    assert result["reference_date"] == date.today()


def test_reference_date_present_in_result():
    owner = build_owner()
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)
    assert result["reference_date"] == REFERENCE_DATE
