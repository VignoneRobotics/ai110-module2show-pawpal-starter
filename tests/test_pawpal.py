from datetime import date

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
