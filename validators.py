"""Guardrails and deterministic fallback phase for PawPal+.

This module consumes the structured dictionary returned by
retrieval.retrieve_context() and does two jobs, both with plain
deterministic logic and no LLM calls:

1. format_fallback_answer() - build a readable answer directly from the
   retrieved records, for use when no AI answer is available (or the AI
   answer fails validation).
2. validate_answer() - check a (future) AI-generated answer against the
   retrieved data and flag anything that looks unsafe or ungrounded.

Nothing in this module mutates the retrieval result or any PawPal+ objects.
"""

import re
import string

from retrieval import (
    INTENT_INCOMPLETE_TASKS,
    INTENT_COMPLETED_TASKS,
    INTENT_PET_TASKS,
    INTENT_TODAYS_SCHEDULE,
    INTENT_CONFLICTS,
    INTENT_NEXT_TASK,
    INTENT_UNSUPPORTED,
)

# ---------------------------------------------------------------------------
# Part 1: Deterministic fallback
# ---------------------------------------------------------------------------


def format_fallback_answer(retrieval_result):
    """Build a concise, readable answer straight from retrieved records.

    No LLM is involved - this is a plain lookup over the structured
    dictionary produced by retrieval.retrieve_context().
    """
    intent = retrieval_result.get("intent")
    records = retrieval_result.get("records", [])

    if intent == INTENT_INCOMPLETE_TASKS:
        return _format_incomplete_tasks(records)
    if intent == INTENT_COMPLETED_TASKS:
        return _format_completed_tasks(records)
    if intent == INTENT_PET_TASKS:
        return _format_pet_tasks(retrieval_result)
    if intent == INTENT_TODAYS_SCHEDULE:
        return _format_todays_schedule(records)
    if intent == INTENT_CONFLICTS:
        return _format_conflicts(records)
    if intent == INTENT_NEXT_TASK:
        return _format_next_task(records)
    return _format_unsupported()


def _format_incomplete_tasks(records):
    if not records:
        return "There are no incomplete tasks."
    lines = ["Here are the incomplete tasks:"]
    for record in records:
        pet = record.get("pet_name") or "Unknown pet"
        lines.append(
            f"- {pet}: {record['description']} at {record['time']}, due {record['due_date']}"
        )
    return "\n".join(lines)


def _format_completed_tasks(records):
    if not records:
        return "There are no completed tasks."
    lines = ["Here are the completed tasks:"]
    for record in records:
        pet = record.get("pet_name") or "Unknown pet"
        lines.append(f"- {pet}: {record['description']} at {record['time']}")
    return "\n".join(lines)


def _format_pet_tasks(retrieval_result):
    pet_name = retrieval_result.get("detected_pet")
    records = retrieval_result.get("records", [])

    if not pet_name:
        return "No matching pet was found for this question."
    if not records:
        return f"{pet_name} has no tasks on record."

    lines = [f"Tasks for {pet_name}:"]
    for record in records:
        status = "completed" if record.get("completed") else "not completed"
        lines.append(
            f"- {record['description']} at {record['time']}, due {record['due_date']} ({status})"
        )
    return "\n".join(lines)


def _format_todays_schedule(records):
    if not records:
        return "No incomplete tasks are due today or overdue."
    lines = ["Here is today's schedule:"]
    for record in records:
        pet = record.get("pet_name") or "Unknown pet"
        lines.append(f"- {pet}: {record['description']} at {record['time']}")
    return "\n".join(lines)


def _format_conflicts(records):
    if not records:
        return "No scheduling conflicts were found."
    lines = ["Here are the scheduling conflicts:"]
    for conflict in records:
        details = ", ".join(
            f"{task.get('pet_name') or 'Unknown pet'}: {task['description']}"
            for task in conflict.get("tasks", [])
        )
        lines.append(f"- At {conflict['time']}: {details}")
    return "\n".join(lines)


def _format_next_task(records):
    if not records:
        return "There is no incomplete task due today or overdue."
    record = records[0]
    pet = record.get("pet_name") or "Unknown pet"
    return f"The next task is: {pet} - {record['description']} at {record['time']}, due {record['due_date']}."


def _format_unsupported():
    return (
        "PawPal+ AI currently supports questions about: incomplete tasks, "
        "completed tasks, a specific pet's tasks, today's schedule, "
        "conflicts, and the next task."
    )


# ---------------------------------------------------------------------------
# Part 2: Answer validation
# ---------------------------------------------------------------------------

_ISSUE_DEDUCTION = 0.34

_ACTION_VERBS = [
    "marked", "unmarked", "added", "deleted", "removed", "rescheduled",
    "updated", "changed", "completed", "created", "scheduled", "moved",
    "edited", "modified", "cancelled", "canceled",
]
_FIRST_PERSON_ACTION_PATTERN = re.compile(
    r"\bi(?:'ve|'ll|'m| have| just| will| am)?\s+(?:" + "|".join(_ACTION_VERBS) + r")\b"
)

_VET_PHRASES = [
    "your pet has",
    "diagnosis",
    "prescribe",
    "give this medication",
    "increase the dose",
    "stop the medication",
]

_NO_CONFLICT_PHRASES = [
    "no conflict",
    "no scheduling conflict",
    "there are no conflicts",
    "there is no conflict",
    "without any conflicts",
    "no conflicts were found",
]

_CONFLICT_EXISTS_PHRASES = [
    "there is a conflict",
    "there's a conflict",
    "a conflict exists",
    "conflicts were found",
    "there are conflicts",
    "a conflict was found",
    "have a conflict",
]

_TIME_PATTERN = re.compile(r"\b([0-1]?\d|2[0-3]):[0-5]\d\b")

_COMMON_CAPITALIZED_WORDS = {
    "pawpal", "i", "there", "no", "the", "currently", "this", "that",
    "please", "sorry", "unfortunately", "ok", "okay", "here", "today",
    "yes",
}


def validate_answer(answer, retrieval_result):
    """Validate a (future) AI-generated answer against retrieved PawPal+ data.

    Confidence scoring rule: start at 1.0 and subtract a fixed 0.34 for each
    validation issue found, then clamp the result to the [0.0, 1.0] range.
    `valid` is True only when zero issues were found. `fallback_recommended`
    mirrors "not valid" - whenever any issue is found, the caller should use
    format_fallback_answer() instead of the AI-generated answer.

    Uses deterministic keyword/regex rules only - no LLM calls, no complex
    natural-language understanding.
    """
    issues = []

    if answer is None or not answer.strip():
        issues.append("The answer is empty or contains only whitespace.")
        return _build_validation_result(issues)

    lowered = answer.lower()

    if _detect_prohibited_action_claim(lowered):
        issues.append(
            "The answer claims the assistant performed an action that changes "
            "PawPal+ data (for example marking, adding, deleting, or rescheduling a task)."
        )

    records = retrieval_result.get("records", [])
    known_descriptions = _known_task_descriptions(records)

    vet_hits = _detect_vet_language(lowered, known_descriptions)
    if vet_hits:
        issues.append(
            "The answer contains veterinary diagnosis or treatment language: "
            + ", ".join(vet_hits)
        )

    if _looks_fabricated(answer, lowered, retrieval_result):
        issues.append(
            "The answer appears to invent specific pet names, task names, "
            "times, or conflicts that are not present in the retrieved data."
        )

    intent = retrieval_result.get("intent")
    if intent == INTENT_CONFLICTS:
        claims_no_conflicts = _claims_no_conflicts(lowered)
        # A "no conflicts" phrase can contain the substring "conflicts were
        # found" (e.g. "no conflicts were found"), so treat the two claims as
        # mutually exclusive rather than checking them independently.
        claims_conflict_exists = (not claims_no_conflicts) and _claims_conflict_exists(lowered)

        if records and claims_no_conflicts:
            issues.append(
                "The answer claims there are no conflicts, but the retrieved "
                "data shows scheduling conflicts."
            )
        if not records and claims_conflict_exists:
            issues.append(
                "The answer claims a conflict exists, but the retrieved data "
                "shows no scheduling conflicts."
            )

    if _detect_completion_contradiction(lowered, records):
        issues.append(
            "The answer contradicts the completion status of a retrieved task."
        )

    return _build_validation_result(issues)


def _build_validation_result(issues):
    confidence = max(0.0, 1.0 - _ISSUE_DEDUCTION * len(issues))
    valid = len(issues) == 0
    return {
        "valid": valid,
        "issues": issues,
        "confidence": round(confidence, 2),
        "fallback_recommended": not valid,
    }


# ---------------------------------------------------------------------------
# Helpers: prohibited action claims
# ---------------------------------------------------------------------------


def _detect_prohibited_action_claim(lowered_answer):
    """Return True if the answer claims the assistant itself changed data."""
    return bool(_FIRST_PERSON_ACTION_PATTERN.search(lowered_answer))


# ---------------------------------------------------------------------------
# Helpers: veterinary guardrail
# ---------------------------------------------------------------------------


def _detect_vet_language(lowered_answer, known_descriptions):
    """Return the list of vet trigger phrases found, ignoring any phrase that
    is just part of a task description already present in the retrieved data."""
    hits = []
    for phrase in _VET_PHRASES:
        if phrase not in lowered_answer:
            continue
        if any(phrase in description for description in known_descriptions):
            continue
        hits.append(phrase)
    return hits


# ---------------------------------------------------------------------------
# Helpers: known data extracted from the retrieval result
# ---------------------------------------------------------------------------


def _flatten_task_records(records):
    """Flatten both plain task records and conflict-group records into a
    single list of task records."""
    flat = []
    for record in records:
        if isinstance(record, dict) and "tasks" in record:
            flat.extend(record["tasks"])
        else:
            flat.append(record)
    return flat


def _known_pet_names(retrieval_result):
    names = set()
    detected_pet = retrieval_result.get("detected_pet")
    if detected_pet:
        names.add(detected_pet.lower())
    for task in _flatten_task_records(retrieval_result.get("records", [])):
        if task.get("pet_name"):
            names.add(task["pet_name"].lower())
    return names


def _known_task_descriptions(records):
    descriptions = set()
    for task in _flatten_task_records(records):
        if task.get("description"):
            descriptions.add(task["description"].lower())
    return descriptions


# ---------------------------------------------------------------------------
# Helpers: fabricated data when no records were retrieved
# ---------------------------------------------------------------------------


def _looks_fabricated(answer, lowered_answer, retrieval_result):
    """Only relevant when retrieval found no records: flag specific-sounding
    details (times, unexpected proper nouns, conflict talk) that could not
    have come from the (empty) retrieved data."""
    records = retrieval_result.get("records", [])
    if records:
        return False

    intent = retrieval_result.get("intent")

    if _TIME_PATTERN.search(answer):
        return True

    if intent != INTENT_CONFLICTS and "conflict" in lowered_answer:
        return True

    known_pet_names = _known_pet_names(retrieval_result)
    if _mentions_unknown_capitalized_word(answer, known_pet_names):
        return True

    return False


def _mentions_unknown_capitalized_word(answer, known_pet_names):
    """Look for capitalized words that appear mid-sentence (so they read as
    proper nouns rather than sentence-starting capitalization) and are not a
    known pet name or a common word used in fallback/answer phrasing."""
    sentences = re.split(r"(?<=[.!?])\s+", answer.strip())
    for sentence in sentences:
        words = sentence.split()
        for index, word in enumerate(words):
            if index == 0:
                continue
            clean = word.strip(string.punctuation)
            if not clean or not clean[0].isupper():
                continue
            lowered_clean = clean.lower()
            if lowered_clean.endswith("'s"):
                lowered_clean = lowered_clean[:-2]
            if lowered_clean in _COMMON_CAPITALIZED_WORDS:
                continue
            if lowered_clean in known_pet_names:
                continue
            return True
    return False


# ---------------------------------------------------------------------------
# Helpers: conflict claims
# ---------------------------------------------------------------------------


def _claims_no_conflicts(lowered_answer):
    return any(phrase in lowered_answer for phrase in _NO_CONFLICT_PHRASES)


def _claims_conflict_exists(lowered_answer):
    return any(phrase in lowered_answer for phrase in _CONFLICT_EXISTS_PHRASES)


# ---------------------------------------------------------------------------
# Helpers: completion-state contradictions
# ---------------------------------------------------------------------------


def _detect_completion_contradiction(lowered_answer, records):
    """Return True if the answer directly states that a retrieved completed
    task is incomplete, or that a retrieved incomplete task is completed."""
    for task in _flatten_task_records(records):
        description = task.get("description")
        if not description:
            continue

        pattern = re.compile(
            re.escape(description.lower())
            + r"\s+(?:is|has been|was)\s+(not\s+)?(complete|completed|incomplete)\b"
        )
        match = pattern.search(lowered_answer)
        if not match:
            continue

        negated = match.group(1) is not None
        word = match.group(2)
        if word == "incomplete":
            claimed_complete = negated
        else:
            claimed_complete = not negated

        if claimed_complete != task.get("completed"):
            return True

    return False
