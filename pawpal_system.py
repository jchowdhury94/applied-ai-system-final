"""PawPal+ logic layer.

Core PawPal+ backend, based on diagrams/uml.mmd. Implements the Owner, Pet,
Task, and Scheduler classes, providing task management, recurring task
generation, schedule generation, and conflict detection, along with helper
methods used by the Streamlit application and the AI retrieval pipeline.
"""

from datetime import date, timedelta

FREQUENCY_INTERVAL_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


def _parse_time(time_str):
    """Convert a "HH:MM" (or "H:MM") time string into minutes since midnight."""
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def _safe_parse_time(time_str):
    """Parse a time string into minutes since midnight, or None if it is invalid."""
    try:
        return _parse_time(time_str)
    except (ValueError, AttributeError):
        return None


def _time_sort_key(task):
    """Sort key ordering valid times first (by minutes), invalid times last."""
    minutes = _safe_parse_time(task.time)
    return (minutes is None, minutes or 0)


class Pet:
    """Represents a pet and the care tasks associated with it."""

    def __init__(self, name, species, age, needs):
        """Initialize a pet with its basic info and an empty task list."""
        self.name = name
        self.species = species
        self.age = age
        self.needs = needs
        self.tasks = []

    def update_pet_info(self):
        """Update the pet's stored information (not yet implemented)."""
        pass

    def add_task(self, task):
        """Add a care task to this pet's task list."""
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, description):
        """Remove any task matching the given description."""
        self.tasks = [task for task in self.tasks if task.description != description]

    def complete_task(self, description):
        """Find the task matching the given description, mark it complete, and
        add its next occurrence to this pet's task list if it recurs."""
        for task in self.tasks:
            if task.description == description:
                next_task = task.mark_complete()
                if next_task is not None:
                    self.add_task(next_task)
                return task
        return None

    def get_tasks(self, completed=None):
        """Return this pet's list of tasks, optionally filtered by completion state."""
        if completed is None:
            return self.tasks
        return [task for task in self.tasks if task.completed == completed]

    def get_summary(self):
        """Return a short summary string describing the pet and its task count."""
        return f"{self.name} the {self.species}, age {self.age} - {len(self.tasks)} task(s)"


class Task:
    """Represents a single care task with a schedule and completion state."""

    def __init__(self, description, time, frequency, completed=False, due_date=None):
        """Initialize a task with its description, time, frequency, completion state, and due date."""
        self.description = description
        self.time = time
        self.frequency = frequency
        self.completed = completed
        self.due_date = due_date if due_date is not None else date.today()
        self.last_completed = None
        self.pet = None

    def mark_complete(self):
        """Mark this task as completed, record the completion date, and return a
        new Task for the next occurrence if this task recurs (daily/weekly/monthly),
        or None if it does not recur."""
        self.completed = True
        self.last_completed = date.today()

        if self.frequency == "daily":
            next_due_date = self.due_date + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due_date = self.due_date + timedelta(days=7)
        elif self.frequency == "monthly":
            next_due_date = self.due_date + timedelta(days=FREQUENCY_INTERVAL_DAYS["monthly"])
        else:
            return None

        return Task(self.description, self.time, self.frequency, due_date=next_due_date)

    def mark_incomplete(self):
        """Mark this task as not completed."""
        self.completed = False

    def is_due(self, reference_date):
        """Return True if this task is due on the given date, based on its frequency."""
        if self.last_completed is None:
            return True
        interval_days = FREQUENCY_INTERVAL_DAYS.get(self.frequency, 1)
        return (reference_date - self.last_completed).days >= interval_days

    def update_task(self, description=None, time=None, frequency=None):
        """Update any provided fields (description, time, frequency) on this task."""
        if description is not None:
            self.description = description
        if time is not None:
            self.time = time
        if frequency is not None:
            self.frequency = frequency

    def get_summary(self):
        """Return a short summary string describing the task and its status."""
        status = "completed" if self.completed else "not completed"
        return f"{self.description} - {self.frequency}, {self.time} ({status})"


class Owner:
    """Represents a pet owner, their scheduling preferences, and their pets."""

    def __init__(self, available_time, preferred_times, task_priorities):
        """Initialize an owner with their scheduling preferences and an empty pet list."""
        self.available_time = available_time
        self.preferred_times = preferred_times
        self.task_priorities = task_priorities
        self.pets = []

    def update_preferences(self):
        """Update the owner's scheduling preferences (not yet implemented)."""
        pass

    def add_pet(self, pet):
        """Add a pet to this owner's list of pets."""
        self.pets.append(pet)

    def remove_pet(self, name):
        """Remove the pet matching the given name."""
        self.pets = [pet for pet in self.pets if pet.name != name]

    def get_pet(self, name):
        """Return the pet matching the given name, or None if not found."""
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

    def get_all_tasks(self, pet_name=None, completed=None):
        """Return a combined list of tasks across pets, optionally filtered by pet name and/or completion state."""
        pets = self.pets if pet_name is None else [pet for pet in self.pets if pet.name == pet_name]
        tasks = []
        for pet in pets:
            tasks.extend(pet.get_tasks(completed=completed))
        return tasks


class Scheduler:
    """Builds and displays a daily task schedule for an owner's pets."""

    def __init__(self, owner, date=None):
        """Initialize a scheduler for the given owner and optional date."""
        self.owner = owner
        self.date = date
        self.selected_tasks = []
        self.explanation = ""
        self.conflicts = []
        self.unparsed_tasks = []

    def generate_plan(self, pet_name=None, completed=None):
        """Order the owner's tasks by pending status and time, storing the result."""
        tasks = self.owner.get_all_tasks(pet_name=pet_name, completed=completed)
        pending = sorted((t for t in tasks if not t.completed), key=_time_sort_key)
        completed = sorted((t for t in tasks if t.completed), key=_time_sort_key)

        self.selected_tasks = pending + completed
        self.explanation = (
            f"{len(pending)} task(s) still pending, "
            f"{len(completed)} already completed, "
            f"ordered by time."
        )

        self.find_conflicts()
        for warning in self.get_conflict_warnings():
            self.explanation += f" {warning}"

        return self.selected_tasks

    def find_conflicts(self):
        """Group pending tasks by (due date, time) and store any groups sharing a slot in self.conflicts."""
        by_slot = {}
        self.unparsed_tasks = []
        for task in self.selected_tasks:
            if task.completed:
                continue
            minutes = _safe_parse_time(task.time)
            if minutes is None:
                self.unparsed_tasks.append(task)
                continue
            by_slot.setdefault((task.due_date, minutes), []).append(task)

        self.conflicts = [tasks for tasks in by_slot.values() if len(tasks) > 1]
        return self.conflicts

    def get_conflict_warnings(self):
        """Return human-readable warning strings for conflicting time slots and unparseable task times."""
        warnings = []
        for tasks in self.conflicts:
            details = ", ".join(
                f"{t.description} ({t.pet.name})" if t.pet else t.description
                for t in tasks
            )
            warnings.append(f"Conflict at {tasks[0].time}: {details}.")

        for task in self.unparsed_tasks:
            pet_label = f" ({task.pet.name})" if task.pet else ""
            warnings.append(
                f"Could not check '{task.description}'{pet_label} for conflicts: invalid time '{task.time}'."
            )

        return warnings

    def show_plan(self):
        """Return a formatted, human-readable string of the generated schedule."""
        title = f"Daily Schedule - {self.date}" if self.date else "Daily Schedule"
        width = max(40, len(title) + 4)
        lines = ["=" * width, title.center(width), "=" * width, ""]

        if not self.selected_tasks:
            lines.append("  No tasks scheduled.")
        else:
            num_width = len(str(len(self.selected_tasks)))
            desc_width = max(len("Task"), *(len(t.description) for t in self.selected_tasks))
            freq_width = max(len("Frequency"), *(len(t.frequency) for t in self.selected_tasks))

            header = (
                f"  {'#':>{num_width}}  {'Time':<5} {'Task'.ljust(desc_width)}  "
                f"{'Frequency'.ljust(freq_width)}  Completed"
            )
            lines.append(header)
            lines.append("  " + "-" * (len(header) - 2))

            for i, task in enumerate(self.selected_tasks, start=1):
                completed = "Yes" if task.completed else "No"
                lines.append(
                    f"  {str(i).rjust(num_width)}  {task.time:<5} "
                    f"{task.description.ljust(desc_width)}  "
                    f"{task.frequency.ljust(freq_width)}  {completed}"
                )

        lines.append("")
        lines.append("-" * width)
        if self.explanation:
            lines.append(self.explanation)

        return "\n".join(lines)
