"""Structured retrieval phase for PawPal+.

Turns a natural-language question into structured PawPal+ records (using the
existing Owner, Pet, Task, and Scheduler objects) plus a compact text context
that a later language-model prompt can consume. No LLM calls happen here -
intent and pet detection are both plain deterministic string matching, and
nothing in this module ever mutates Owner/Pet/Task/Scheduler state.
"""

from datetime import date

from logger_config import get_logger
from pawpal_system import Scheduler, _safe_parse_time, _time_sort_key

logger = get_logger(__name__)

INTENT_INCOMPLETE_TASKS = "incomplete_tasks"
INTENT_COMPLETED_TASKS = "completed_tasks"
INTENT_PET_TASKS = "pet_tasks"
INTENT_TODAYS_SCHEDULE = "todays_schedule"
INTENT_CONFLICTS = "conflicts"
INTENT_NEXT_TASK = "next_task"
INTENT_UNSUPPORTED = "unsupported"

_INTENT_PHRASES = [
    (INTENT_CONFLICTS, ["conflict"]),
    (INTENT_NEXT_TASK, ["next task", "what's next", "whats next", "next up"]),
    (INTENT_TODAYS_SCHEDULE, ["today's schedule", "todays schedule", "schedule for today", "today's tasks", "todays tasks"]),
    (INTENT_COMPLETED_TASKS, ["completed", "finished task", "finished tasks"]),
    (INTENT_INCOMPLETE_TASKS, ["incomplete task", "incomplete tasks", "pending task", "not completed", "what's left", "whats left", "still need"]),
]


def detect_intent(question):
    """Deterministically classify a question into one of the supported intent values."""
    if question is None:
        return INTENT_UNSUPPORTED

    normalized = question.strip().lower()
    if not normalized:
        return INTENT_UNSUPPORTED

    for intent, phrases in _INTENT_PHRASES:
        if any(phrase in normalized for phrase in phrases):
            return intent

    if "schedule" in normalized:
        return INTENT_TODAYS_SCHEDULE

    if "incomplete" in normalized:
        return INTENT_INCOMPLETE_TASKS

    if "next" in normalized:
        return INTENT_NEXT_TASK

    if "task" in normalized:
        return INTENT_PET_TASKS

    return INTENT_UNSUPPORTED


def detect_pet(question, owner):
    """Return the real stored name of an owner's pet mentioned in the question, or None."""
    if not question or owner is None:
        return None

    normalized = question.strip().lower()
    if not normalized:
        return None

    for pet in owner.pets:
        if pet.name and pet.name.lower() in normalized:
            return pet.name
    return None


def _task_record(task):
    return {
        "pet_name": task.pet.name if task.pet else None,
        "description": task.description,
        "time": task.time,
        "frequency": task.frequency,
        "due_date": task.due_date,
        "completed": task.completed,
    }


def _due_today_incomplete_tasks(owner, reference_date):
    tasks = owner.get_all_tasks(completed=False)
    due = [t for t in tasks if t.due_date is not None and t.due_date <= reference_date]
    return sorted(due, key=_time_sort_key)


def _conflict_records(tasks):
    """Run the existing Scheduler conflict logic over exactly the given tasks."""
    scheduler = Scheduler(owner=None)
    scheduler.selected_tasks = list(tasks)
    scheduler.find_conflicts()

    records = []
    for group in scheduler.conflicts:
        records.append({
            "time": group[0].time,
            "tasks": [_task_record(t) for t in group],
        })
    return records


def _format_task_line(task):
    pet_label = task["pet_name"] or "Unknown pet"
    status = "completed" if task["completed"] else "not completed"
    return f"- {pet_label}: {task['description']} ({task['time']}, {task['frequency']}, due {task['due_date']}, {status})"


def retrieve_context(question, owner, reference_date=None):
    """Validate a question, detect intent/pet, retrieve matching PawPal+ records,
    and return a structured result with a compact text context. Never mutates
    Owner, Pet, Task, or Scheduler state."""
    logger.info("Retrieval started.")
    try:
        result = _retrieve_context(question, owner, reference_date)
    except Exception as exc:
        logger.error("Unexpected retrieval error (%s).", type(exc).__name__)
        raise

    record_count = len(result.get("records") or [])
    if result.get("supported") and record_count == 0:
        logger.info("No matching records were found.")
    logger.info("Retrieval completed with %d record(s).", record_count)
    return result


def _retrieve_context(question, owner, reference_date):
    if reference_date is None:
        reference_date = date.today()

    result = {
        "intent": INTENT_UNSUPPORTED,
        "supported": False,
        "detected_pet": None,
        "records": [],
        "context_text": "",
        "message": "",
        "reference_date": reference_date,
    }

    if question is None or not question.strip():
        logger.info("Blank question received.")
        result["message"] = "The question was blank."
        result["context_text"] = "No question was provided."
        return result

    intent = detect_intent(question)
    result["intent"] = intent
    logger.info("Detected intent: %s", intent)

    if intent == INTENT_UNSUPPORTED:
        logger.info("Unsupported question; no supported intent detected.")
        result["message"] = "This question is not one of the supported PawPal+ question types."
        result["context_text"] = "No supported intent was detected for this question."
        return result

    result["supported"] = True

    if owner is None or not owner.pets:
        result["message"] = "This owner has no pets on record."
        result["context_text"] = "No pets are on record for this owner."
        return result

    detected_pet = detect_pet(question, owner)
    if detected_pet:
        logger.info("Detected pet: %s", detected_pet)
    if intent == INTENT_PET_TASKS:
        result["detected_pet"] = detected_pet
        if detected_pet is None:
            result["message"] = "No pet matching the question was found for this owner."
            result["context_text"] = "No matching pet name was found among this owner's pets."
            return result
    else:
        result["detected_pet"] = detected_pet

    if intent == INTENT_INCOMPLETE_TASKS:
        tasks = owner.get_all_tasks(completed=False)
        tasks = sorted(tasks, key=_time_sort_key)
        records = [_task_record(t) for t in tasks]
        result["records"] = records
        if not records:
            result["message"] = "There are no incomplete tasks."
            result["context_text"] = "No incomplete tasks were found."
        else:
            result["message"] = f"Found {len(records)} incomplete task(s)."
            lines = [f"Incomplete tasks ({len(records)}):"] + [_format_task_line(r) for r in records]
            result["context_text"] = "\n".join(lines)
        return result

    if intent == INTENT_COMPLETED_TASKS:
        tasks = owner.get_all_tasks(completed=True)
        tasks = sorted(tasks, key=_time_sort_key)
        records = [_task_record(t) for t in tasks]
        result["records"] = records
        if not records:
            result["message"] = "There are no completed tasks."
            result["context_text"] = "No completed tasks were found."
        else:
            result["message"] = f"Found {len(records)} completed task(s)."
            lines = [f"Completed tasks ({len(records)}):"] + [_format_task_line(r) for r in records]
            result["context_text"] = "\n".join(lines)
        return result

    if intent == INTENT_PET_TASKS:
        tasks = owner.get_all_tasks(pet_name=detected_pet)
        tasks = sorted(tasks, key=_time_sort_key)
        records = [_task_record(t) for t in tasks]
        result["records"] = records
        if not records:
            result["message"] = f"{detected_pet} has no tasks on record."
            result["context_text"] = f"No tasks were found for {detected_pet}."
        else:
            result["message"] = f"Found {len(records)} task(s) for {detected_pet}."
            lines = [f"Tasks for {detected_pet} ({len(records)}):"] + [_format_task_line(r) for r in records]
            result["context_text"] = "\n".join(lines)
        return result

    if intent == INTENT_TODAYS_SCHEDULE:
        due_tasks = _due_today_incomplete_tasks(owner, reference_date)
        records = [_task_record(t) for t in due_tasks]
        result["records"] = records
        if not records:
            result["message"] = "There are no tasks due for today's schedule."
            result["context_text"] = "No tasks are due for today's schedule."
        else:
            result["message"] = f"Found {len(records)} task(s) for today's schedule."
            lines = [f"Today's schedule ({len(records)}):"] + [_format_task_line(r) for r in records]
            result["context_text"] = "\n".join(lines)
        return result

    if intent == INTENT_NEXT_TASK:
        due_tasks = _due_today_incomplete_tasks(owner, reference_date)
        if not due_tasks:
            result["message"] = "There is no qualifying next task."
            result["context_text"] = "No qualifying next task was found."
            return result
        next_task = due_tasks[0]
        record = _task_record(next_task)
        result["records"] = [record]
        result["message"] = "Found the next task."
        result["context_text"] = "Next task:\n" + _format_task_line(record)
        return result

    if intent == INTENT_CONFLICTS:
        due_tasks = _due_today_incomplete_tasks(owner, reference_date)
        conflict_records = _conflict_records(due_tasks)
        result["records"] = conflict_records
        if not conflict_records:
            result["message"] = "No scheduling conflicts were found."
            result["context_text"] = "No scheduling conflicts were found in today's schedule."
        else:
            result["message"] = f"Found {len(conflict_records)} scheduling conflict(s)."
            lines = [f"Scheduling conflicts ({len(conflict_records)}):"]
            for conflict in conflict_records:
                details = ", ".join(
                    f"{t['pet_name'] or 'Unknown pet'}: {t['description']}" for t in conflict["tasks"]
                )
                lines.append(f"- At {conflict['time']}: {details}")
            result["context_text"] = "\n".join(lines)
        return result

    result["message"] = "This question is not one of the supported PawPal+ question types."
    result["context_text"] = "No supported intent was detected for this question."
    result["supported"] = False
    result["intent"] = INTENT_UNSUPPORTED
    return result
