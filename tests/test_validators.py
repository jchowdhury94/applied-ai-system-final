import copy
from datetime import date

import pytest

from pawpal_system import Owner, Pet, Task
from retrieval import retrieve_context
from validators import format_fallback_answer, validate_answer

REFERENCE_DATE = date(2026, 1, 15)
PAST_DATE = date(2026, 1, 10)
FUTURE_DATE = date(2026, 1, 20)
YESTERDAY = date(2026, 1, 14)


def build_owner():
    """Fresh, deterministic fixture: two pets with a mix of task states,
    including a same-time conflict (Morning walk / Feed breakfast at 07:00)."""
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
    whiskers.add_task(Task("Vaccine", "08:00", "monthly", completed=True, due_date=PAST_DATE))

    return owner


def build_owner_no_conflicts():
    owner = Owner(available_time="1 hour", preferred_times=[], task_priorities=[])
    pet = Pet(name="Biscuit", species="Dog", age=4, needs=[])
    owner.add_pet(pet)
    pet.add_task(Task("Morning walk", "07:00", "daily", due_date=REFERENCE_DATE))
    return owner


def build_owner_no_pets():
    return Owner(available_time="1 hour", preferred_times=[], task_priorities=[])


def build_owner_with_empty_pet():
    owner = build_owner_no_pets()
    owner.add_pet(Pet(name="Nemo", species="Fish", age=1, needs=[]))
    return owner


def build_owner_future_only():
    owner = Owner(available_time="1 hour", preferred_times=[], task_priorities=[])
    pet = Pet(name="Biscuit", species="Dog", age=4, needs=[])
    owner.add_pet(pet)
    pet.add_task(Task("Bath", "09:00", "monthly", due_date=FUTURE_DATE))
    return owner


def build_owner_with_medication_task():
    owner = Owner(available_time="1 hour", preferred_times=[], task_priorities=[])
    pet = Pet(name="Biscuit", species="Dog", age=4, needs=[])
    owner.add_pet(pet)
    pet.add_task(Task("Give this medication", "08:00", "daily", due_date=REFERENCE_DATE))
    return owner


# ---------------------------------------------------------------------------
# Part 1: Deterministic fallback answers
# ---------------------------------------------------------------------------


def test_fallback_incomplete_tasks_with_records():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "Biscuit" in answer
    assert "Morning walk" in answer
    assert "07:00" in answer
    assert str(REFERENCE_DATE) in answer
    assert "Whiskers" in answer
    assert "Feed breakfast" in answer


def test_fallback_no_incomplete_tasks():
    owner = build_owner_no_pets()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "no incomplete tasks" in answer.lower()


def test_fallback_completed_tasks():
    owner = build_owner()
    result = retrieve_context("What tasks have been completed?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "Grooming" in answer
    assert "Vaccine" in answer
    assert "Biscuit" in answer
    assert "Whiskers" in answer


def test_fallback_completed_tasks_none():
    owner = build_owner_no_conflicts()
    result = retrieve_context("What tasks have been completed?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "no completed tasks" in answer.lower()


def test_fallback_pet_specific_tasks():
    owner = build_owner()
    result = retrieve_context("What tasks does Biscuit have?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "Biscuit" in answer
    assert "Morning walk" in answer
    assert "Bath" in answer
    assert "Vet visit" in answer
    assert "Grooming" in answer


def test_fallback_pet_specific_unknown_pet():
    owner = build_owner()
    result = retrieve_context("What tasks does Rex have?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "no matching pet" in answer.lower()


def test_fallback_pet_with_no_tasks():
    owner = build_owner_with_empty_pet()
    result = retrieve_context("What tasks does Nemo have?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "Nemo" in answer
    assert "no tasks" in answer.lower()


def test_fallback_todays_schedule():
    owner = build_owner()
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "Morning walk" in answer
    assert "Feed breakfast" in answer
    assert "Vet visit" in answer
    # Order must match the retrieval result's own ordering (chronological).
    assert answer.index("Morning walk") < answer.index("Feed breakfast") < answer.index("Vet visit")


def test_fallback_todays_schedule_no_due_tasks():
    owner = build_owner_future_only()
    result = retrieve_context("What is today's schedule?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "no incomplete tasks are due today or overdue" in answer.lower()


def test_fallback_conflicts():
    owner = build_owner()
    result = retrieve_context("Are there any conflicts?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "07:00" in answer
    assert "Morning walk" in answer
    assert "Feed breakfast" in answer


def test_fallback_no_conflicts():
    owner = build_owner_no_conflicts()
    result = retrieve_context("Are there any conflicts?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "no scheduling conflicts" in answer.lower()


def test_fallback_next_task():
    owner = build_owner()
    result = retrieve_context("What's my next task?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "Morning walk" in answer
    assert "Biscuit" in answer


def test_fallback_no_next_task():
    owner = build_owner_future_only()
    result = retrieve_context("What's my next task?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    assert "no incomplete task due today or overdue" in answer.lower()


def test_fallback_unsupported_intent():
    owner = build_owner()
    result = retrieve_context("What's the weather today?", owner, reference_date=REFERENCE_DATE)
    answer = format_fallback_answer(result)

    lowered = answer.lower()
    assert "incomplete tasks" in lowered
    assert "completed tasks" in lowered
    assert "conflicts" in lowered
    assert "next task" in lowered


def test_fallback_does_not_mutate_retrieval_result():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)
    before = copy.deepcopy(result)

    format_fallback_answer(result)

    assert result == before


# ---------------------------------------------------------------------------
# Part 2: Answer validation
# ---------------------------------------------------------------------------


def test_valid_grounded_answer():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)

    answer = (
        "Biscuit still needs a morning walk and a vet visit, and Whiskers "
        "still needs breakfast. None of these are marked complete yet."
    )
    validation = validate_answer(answer, result)

    assert validation["valid"] is True
    assert validation["issues"] == []
    assert validation["confidence"] == 1.0
    assert validation["fallback_recommended"] is False


def test_blank_answer_is_rejected():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)

    for blank in ("", "   ", "\n\t"):
        validation = validate_answer(blank, result)
        assert validation["valid"] is False
        assert validation["issues"]
        assert validation["fallback_recommended"] is True


def test_autonomous_action_claim_is_rejected():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)

    for answer in [
        "I marked the Morning walk task as complete for Biscuit.",
        "I added a task for Whiskers.",
        "I deleted the vet visit task.",
        "I rescheduled Biscuit's bath.",
    ]:
        validation = validate_answer(answer, result)
        assert validation["valid"] is False
        assert any("action" in issue.lower() for issue in validation["issues"])
        assert validation["fallback_recommended"] is True


def test_fabricated_data_when_no_records_exist():
    owner = build_owner_no_pets()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)
    assert result["records"] == []

    answer = "Biscuit's morning walk conflicts with Whiskers' feeding at 7:00."
    validation = validate_answer(answer, result)

    assert validation["valid"] is False
    assert any("invent" in issue.lower() for issue in validation["issues"])


def test_correct_no_conflict_answer_is_valid():
    owner = build_owner_no_conflicts()
    result = retrieve_context("Are there any conflicts?", owner, reference_date=REFERENCE_DATE)
    assert result["records"] == []

    answer = "No scheduling conflicts were found for today."
    validation = validate_answer(answer, result)

    assert validation["valid"] is True
    assert validation["issues"] == []


def test_incorrect_no_conflict_claim_when_conflicts_exist():
    owner = build_owner()
    result = retrieve_context("Are there any conflicts?", owner, reference_date=REFERENCE_DATE)
    assert result["records"]

    answer = "There are no scheduling conflicts today."
    validation = validate_answer(answer, result)

    assert validation["valid"] is False
    assert any("conflict" in issue.lower() for issue in validation["issues"])


def test_incorrect_conflict_claim_when_none_exist():
    owner = build_owner_no_conflicts()
    result = retrieve_context("Are there any conflicts?", owner, reference_date=REFERENCE_DATE)
    assert result["records"] == []

    answer = "There is a conflict today."
    validation = validate_answer(answer, result)

    assert validation["valid"] is False
    assert any("conflict" in issue.lower() for issue in validation["issues"])


def test_completed_task_described_as_incomplete():
    owner = build_owner()
    result = retrieve_context("What tasks have been completed?", owner, reference_date=REFERENCE_DATE)

    answer = "Grooming is incomplete."
    validation = validate_answer(answer, result)

    assert validation["valid"] is False
    assert any("contradict" in issue.lower() for issue in validation["issues"])


def test_incomplete_task_described_as_completed():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)

    answer = "Morning walk is completed."
    validation = validate_answer(answer, result)

    assert validation["valid"] is False
    assert any("contradict" in issue.lower() for issue in validation["issues"])


def test_veterinary_diagnosis_language_is_rejected():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)

    answer = "Your pet has an infection; the diagnosis is clear, so I prescribe antibiotics."
    validation = validate_answer(answer, result)

    assert validation["valid"] is False
    assert any("veterinary" in issue.lower() for issue in validation["issues"])


def test_stored_medication_wording_is_not_falsely_flagged():
    owner = build_owner_with_medication_task()
    result = retrieve_context("What tasks does Biscuit have?", owner, reference_date=REFERENCE_DATE)
    assert result["records"]

    answer = "Biscuit's task is: Give this medication, due today."
    validation = validate_answer(answer, result)

    assert validation["valid"] is True
    assert validation["issues"] == []


def test_harmless_paraphrasing_is_not_rejected():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)

    answer = (
        "Looks like there is still a walk and a checkup pending for one pet, "
        "and breakfast still needs to happen for the other."
    )
    validation = validate_answer(answer, result)

    assert validation["valid"] is True
    assert validation["issues"] == []


@pytest.mark.parametrize("answer", [
    "",
    "I marked the task complete.",
    "I marked the task complete. Your pet has an infection, diagnosis: flu.",
    "I marked the task complete. Diagnosis: flu. I prescribe rest. There is a conflict.",
])
def test_confidence_always_between_zero_and_one(answer):
    owner = build_owner()
    result = retrieve_context("Are there any conflicts?", owner, reference_date=REFERENCE_DATE)

    validation = validate_answer(answer, result)

    assert 0.0 <= validation["confidence"] <= 1.0


def test_validate_answer_does_not_mutate_retrieval_result():
    owner = build_owner()
    result = retrieve_context("What are my incomplete tasks?", owner, reference_date=REFERENCE_DATE)
    before = copy.deepcopy(result)

    validate_answer("Biscuit still needs a morning walk.", result)

    assert result == before
