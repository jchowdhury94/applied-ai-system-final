from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_sets_completed_true():
    task = Task("Feed the cat", "08:00", "daily")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Whiskers", "cat", 3, "low-maintenance")
    task = Task("Feed the cat", "08:00", "daily")
    initial_count = len(pet.get_tasks())

    pet.add_task(task)

    assert len(pet.get_tasks()) == initial_count + 1


def test_complete_task_creates_next_day_occurrence_for_daily_task():
    pet = Pet("Whiskers", "cat", 3, "low-maintenance")
    task = Task("Feed the cat", "08:00", "daily", due_date=date.today())
    pet.add_task(task)

    pet.complete_task("Feed the cat")

    tasks = pet.get_tasks()
    assert len(tasks) == 2

    original_task = next(t for t in tasks if t is task)
    new_task = next(t for t in tasks if t is not task)

    assert original_task.completed is True
    assert new_task.completed is False
    assert new_task.due_date == date.today() + timedelta(days=1)


def test_complete_task_creates_next_month_occurrence_for_monthly_task():
    pet = Pet("Whiskers", "cat", 3, "low-maintenance")
    task = Task("Give heartworm medication", "08:00", "monthly", due_date=date.today())
    pet.add_task(task)

    pet.complete_task("Give heartworm medication")

    tasks = pet.get_tasks()
    assert len(tasks) == 2

    original_task = next(t for t in tasks if t is task)
    new_task = next(t for t in tasks if t is not task)

    assert original_task.completed is True
    assert new_task.completed is False
    assert new_task.due_date == date.today() + timedelta(days=30)


def test_generate_plan_orders_tasks_chronologically():
    owner = Owner(available_time="1 hour", preferred_times=["morning"], task_priorities=[])
    pet = Pet("Whiskers", "cat", 3, "low-maintenance")
    owner.add_pet(pet)

    pet.add_task(Task("Evening walk", "18:00", "daily"))
    pet.add_task(Task("Morning feed", "07:00", "daily"))
    pet.add_task(Task("Morning walk", "08:00", "daily"))

    scheduler = Scheduler(owner)
    selected_tasks = scheduler.generate_plan()

    assert [task.time for task in selected_tasks] == ["07:00", "08:00", "18:00"]


def test_generate_plan_detects_conflict_between_pets():
    owner = Owner(available_time="1 hour", preferred_times=["morning"], task_priorities=[])
    pet1 = Pet("Whiskers", "cat", 3, "low-maintenance")
    pet2 = Pet("Rex", "dog", 5, "high-maintenance")
    owner.add_pet(pet1)
    owner.add_pet(pet2)

    due_date = date.today()
    task1 = Task("Feed the cat", "08:00", "daily", due_date=due_date)
    task2 = Task("Walk the dog", "08:00", "daily", due_date=due_date)
    pet1.add_task(task1)
    pet2.add_task(task2)

    scheduler = Scheduler(owner)
    scheduler.generate_plan()

    assert len(scheduler.conflicts) == 1
    assert set(scheduler.conflicts[0]) == {task1, task2}
