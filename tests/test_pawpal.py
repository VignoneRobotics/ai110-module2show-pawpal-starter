from datetime import date

import pytest

from pawpal_system import Pet, Task

DAY = date(2026, 1, 5)


def test_mark_complete_sets_completed_true():
    """mark_complete() flips a new task from not completed to completed."""
    task = Task("Morning walk", "07:30", 30, due_date=DAY)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_count_and_stamps_pet_name():
    """Pet.add_task() adds the task and sets its pet_name to the pet's name."""
    pet = Pet("Mochi", "dog")
    task = Task("Brush coat", "18:00", 20, due_date=DAY)
    assert len(pet.get_tasks()) == 0
    assert task.pet_name == ""

    pet.add_task(task)

    assert len(pet.get_tasks()) == 1
    assert task.pet_name == "Mochi"


# --- Validation ---


@pytest.mark.parametrize("bad_time", ["7:30", "25:00", "24:00", "12:60", "0730", "07:3", "ab:cd", ""])
def test_task_rejects_bad_time(bad_time):
    """A time that is not zero-padded HH:MM within 00:00-23:59 raises ValueError."""
    with pytest.raises(ValueError, match="time"):
        Task("Walk", bad_time, 30, due_date=DAY)


def test_task_rejects_unknown_priority():
    """An unknown priority string raises ValueError."""
    with pytest.raises(ValueError, match="priority"):
        Task("Walk", "08:00", 30, priority="urgent", due_date=DAY)


def test_task_rejects_unknown_frequency():
    """An unknown frequency string raises ValueError."""
    with pytest.raises(ValueError, match="frequency"):
        Task("Walk", "08:00", 30, frequency="monthly", due_date=DAY)


@pytest.mark.parametrize("bad_duration", [0, -5])
def test_task_rejects_non_positive_duration(bad_duration):
    """A duration of zero or less raises ValueError."""
    with pytest.raises(ValueError, match="uration"):
        Task("Walk", "08:00", bad_duration, due_date=DAY)


def test_task_rejects_running_past_midnight():
    """A task whose start + duration passes 24:00 raises ValueError."""
    with pytest.raises(ValueError, match="midnight"):
        Task("Late walk", "23:30", 45, due_date=DAY)


def test_task_allows_ending_exactly_at_midnight():
    """A task that ends exactly at 24:00 is valid."""
    task = Task("Late walk", "23:30", 30, due_date=DAY)
    assert task.time == "23:30"


def test_task_accepts_normal_values():
    """A typical task constructs without error."""
    task = Task("Walk", "08:00", 30, priority="high", frequency="daily", due_date=DAY)
    assert task.priority == "high"
