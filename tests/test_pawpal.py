from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

DAY = date(2026, 1, 5)
NEXT_DAY = DAY + timedelta(days=1)


def make_scheduler(budget: int = 480) -> tuple[Scheduler, Pet, Pet]:
    """Return a Scheduler for an owner with two empty pets, Mochi and Bean."""
    owner = Owner("Jordan", available_minutes=budget)
    mochi = Pet("Mochi", "dog")
    bean = Pet("Bean", "cat")
    owner.add_pet(mochi)
    owner.add_pet(bean)
    return Scheduler(owner), mochi, bean


def add(pet, description, time, duration, priority="medium", frequency="once", due=DAY) -> Task:
    """Create a task with an explicit due date, add it to the pet, and return it."""
    task = Task(description, time, duration, priority, frequency, due_date=due)
    pet.add_task(task)
    return task


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


# --- Owner / Pet ---


def test_add_pet_rejects_duplicate_name_case_insensitive():
    """Adding a pet whose name matches an existing pet (any case) raises ValueError."""
    scheduler, _, _ = make_scheduler()
    with pytest.raises(ValueError):
        scheduler.owner.add_pet(Pet("mochi", "cat"))


def test_get_pet_is_case_insensitive():
    """get_pet finds a pet regardless of case and returns None when missing."""
    scheduler, mochi, _ = make_scheduler()
    assert scheduler.owner.get_pet("MOCHI") is mochi
    assert scheduler.owner.get_pet("Rex") is None


def test_get_all_tasks_spans_every_pet():
    """get_all_tasks returns tasks from all pets."""
    scheduler, mochi, bean = make_scheduler()
    add(mochi, "Walk", "08:00", 30)
    add(bean, "Feed", "09:00", 10)
    assert {t.description for t in scheduler.owner.get_all_tasks()} == {"Walk", "Feed"}


def test_remove_task_removes_only_that_task():
    """remove_task deletes the task with the given id and keeps the others."""
    _, mochi, _ = make_scheduler()
    walk = add(mochi, "Walk", "08:00", 30)
    bath = add(mochi, "Bath", "10:00", 30)
    mochi.remove_task(walk.task_id)
    assert mochi.get_tasks() == [bath]


def test_find_task_returns_pet_and_task_or_none():
    """find_task returns the owning pet with the task, or None for an unknown id."""
    scheduler, _, bean = make_scheduler()
    feed = add(bean, "Feed", "09:00", 10)
    assert scheduler.owner.find_task(feed.task_id) == (bean, feed)
    assert scheduler.owner.find_task("nope") is None


# --- Sorting ---


def test_sort_by_time_orders_out_of_order_tasks():
    """Tasks added out of order come back in ascending time order."""
    scheduler, mochi, _ = make_scheduler()
    add(mochi, "C", "09:00", 10)
    add(mochi, "A", "07:30", 10)
    add(mochi, "B", "08:00", 10)
    assert [t.time for t in scheduler.sort_by_time()] == ["07:30", "08:00", "09:00"]


def test_sort_by_time_breaks_ties_by_priority():
    """Two tasks at the same time sort high priority before low."""
    scheduler, mochi, bean = make_scheduler()
    add(mochi, "Low one", "08:00", 10, priority="low")
    add(bean, "High one", "08:00", 10, priority="high")
    assert [t.description for t in scheduler.sort_by_time()] == ["High one", "Low one"]


def test_sort_by_time_puts_next_day_after_today():
    """A next-day 07:00 task sorts after the same-day 08:00 task."""
    scheduler, mochi, _ = make_scheduler()
    add(mochi, "Tomorrow early", "07:00", 10, due=NEXT_DAY)
    add(mochi, "Today later", "08:00", 10, due=DAY)
    assert [t.description for t in scheduler.sort_by_time()] == ["Today later", "Tomorrow early"]


def test_sort_by_time_with_no_tasks_returns_empty_list():
    """Sorting an owner with no tasks returns an empty list."""
    scheduler, _, _ = make_scheduler()
    assert scheduler.sort_by_time() == []


def test_sort_and_filter_compose():
    """sort_by_time accepts the output of filter_tasks."""
    scheduler, mochi, bean = make_scheduler()
    add(mochi, "Late", "10:00", 10)
    add(mochi, "Early", "07:00", 10)
    add(bean, "Other", "08:00", 10)
    result = scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi"))
    assert [t.description for t in result] == ["Early", "Late"]


# --- Filtering ---


def test_filter_by_pet_name_is_case_insensitive():
    """filter_tasks matches the pet name regardless of case."""
    scheduler, mochi, bean = make_scheduler()
    add(mochi, "Walk", "08:00", 10)
    add(bean, "Feed", "09:00", 10)
    assert [t.description for t in scheduler.filter_tasks(pet_name="mOcHi")] == ["Walk"]


def test_filter_by_completed_status():
    """filter_tasks separates completed from pending tasks."""
    scheduler, mochi, _ = make_scheduler()
    done = add(mochi, "Done", "08:00", 10)
    add(mochi, "Pending", "09:00", 10)
    done.mark_complete()
    assert [t.description for t in scheduler.filter_tasks(completed=True)] == ["Done"]
    assert [t.description for t in scheduler.filter_tasks(completed=False)] == ["Pending"]


def test_filters_combine_and_none_means_no_filter():
    """Pet and completed filters combine; None leaves tasks unfiltered."""
    scheduler, mochi, bean = make_scheduler()
    add(mochi, "Mochi pending", "08:00", 10)
    done = add(mochi, "Mochi done", "09:00", 10)
    add(bean, "Bean pending", "10:00", 10)
    done.mark_complete()
    both = scheduler.filter_tasks(pet_name="Mochi", completed=False)
    assert [t.description for t in both] == ["Mochi pending"]
    assert len(scheduler.filter_tasks()) == 3


# --- Recurrence ---


def test_completing_daily_task_creates_next_day_copy():
    """Completing a daily task keeps it and adds an equal task due the next day."""
    scheduler, mochi, _ = make_scheduler()
    walk = add(mochi, "Walk", "08:00", 30, priority="high", frequency="daily")

    new_task = scheduler.mark_task_complete(walk.task_id)

    assert walk.completed is True
    assert new_task is not None
    assert new_task.due_date == NEXT_DAY
    assert new_task.completed is False
    assert new_task.task_id != walk.task_id
    assert (new_task.description, new_task.time, new_task.duration_minutes) == ("Walk", "08:00", 30)
    assert new_task.pet_name == "Mochi"
    assert len(mochi.get_tasks()) == 2


def test_completing_weekly_task_creates_copy_seven_days_later():
    """Completing a weekly task adds a copy due 7 days later."""
    scheduler, mochi, _ = make_scheduler()
    bath = add(mochi, "Bath", "10:00", 30, frequency="weekly")
    new_task = scheduler.mark_task_complete(bath.task_id)
    assert new_task.due_date == DAY + timedelta(days=7)


def test_completing_once_task_creates_no_copy():
    """Completing a one-off task returns None and adds nothing."""
    scheduler, mochi, _ = make_scheduler()
    vet = add(mochi, "Vet", "10:00", 60)
    assert scheduler.mark_task_complete(vet.task_id) is None
    assert vet.completed is True
    assert len(mochi.get_tasks()) == 1
    assert vet.next_occurrence() is None


def test_completing_twice_does_not_duplicate_next_occurrence():
    """A second completion of the same task returns None and adds no extra copy."""
    scheduler, mochi, _ = make_scheduler()
    walk = add(mochi, "Walk", "08:00", 30, frequency="daily")
    scheduler.mark_task_complete(walk.task_id)
    assert scheduler.mark_task_complete(walk.task_id) is None
    assert len(mochi.get_tasks()) == 2


def test_completing_unknown_task_id_returns_none():
    """An unknown task id is ignored and returns None."""
    scheduler, _, _ = make_scheduler()
    assert scheduler.mark_task_complete("missing") is None


# --- Conflicts ---


def test_overlap_on_same_pet_gives_one_exact_warning():
    """Two overlapping tasks on one pet produce a single same-pet warning."""
    scheduler, mochi, _ = make_scheduler()
    add(mochi, "Walk", "08:00", 30)
    add(mochi, "Bath", "08:15", 30)
    assert scheduler.detect_conflicts() == [
        "Conflict (same pet: Mochi): Walk 08:00-08:30 overlaps Bath 08:15-08:45"
    ]


def test_overlap_across_pets_is_labelled_cross_pet():
    """Overlapping tasks on different pets get the cross-pet label, earlier task first."""
    scheduler, mochi, bean = make_scheduler()
    add(mochi, "Walk", "08:00", 30)
    add(bean, "Feed", "08:10", 10)
    assert scheduler.detect_conflicts() == [
        "Conflict (cross-pet: Mochi, Bean): Walk 08:00-08:30 overlaps Feed 08:10-08:20"
    ]


def test_same_start_time_is_a_conflict():
    """Two tasks starting at exactly the same time conflict."""
    scheduler, mochi, bean = make_scheduler()
    add(mochi, "Walk", "08:00", 30)
    add(bean, "Feed", "08:00", 10)
    assert len(scheduler.detect_conflicts()) == 1


def test_back_to_back_tasks_do_not_conflict():
    """A task starting exactly when another ends is not a conflict."""
    scheduler, mochi, _ = make_scheduler()
    add(mochi, "Walk", "08:00", 30)
    add(mochi, "Bath", "08:30", 30)
    assert scheduler.detect_conflicts() == []


def test_back_to_back_tasks_do_not_conflict_reverse_order():
    """Back-to-back tasks are not a conflict when the later task is added first."""
    scheduler, mochi, _ = make_scheduler()
    add(mochi, "Bath", "08:30", 30)
    add(mochi, "Walk", "08:00", 30)
    assert scheduler.detect_conflicts() == []


def test_same_time_on_different_days_does_not_conflict():
    """Tasks at the same time on different due dates do not conflict."""
    scheduler, mochi, _ = make_scheduler()
    add(mochi, "Walk", "08:00", 30, due=DAY)
    add(mochi, "Walk", "08:00", 30, due=NEXT_DAY)
    assert scheduler.detect_conflicts() == []


def test_completed_tasks_are_ignored_by_conflict_detection():
    """A completed task no longer conflicts with an overlapping pending task."""
    scheduler, mochi, _ = make_scheduler()
    walk = add(mochi, "Walk", "08:00", 30)
    add(mochi, "Bath", "08:15", 30)
    walk.mark_complete()
    assert scheduler.detect_conflicts() == []


def test_three_mutually_overlapping_tasks_give_three_warnings():
    """Each overlapping pair is reported exactly once."""
    scheduler, mochi, _ = make_scheduler()
    add(mochi, "A", "08:00", 60)
    add(mochi, "B", "08:10", 60)
    add(mochi, "C", "08:20", 60)
    assert len(scheduler.detect_conflicts()) == 3


def test_detect_conflicts_with_no_tasks_returns_empty_list():
    """No tasks means no warnings."""
    scheduler, _, _ = make_scheduler()
    assert scheduler.detect_conflicts() == []


# --- Daily plan / budget ---


def test_plan_includes_only_pending_tasks_due_that_day():
    """Tasks due on other days and completed tasks are left out of the plan."""
    scheduler, mochi, _ = make_scheduler()
    today = add(mochi, "Today", "08:00", 10, due=DAY)
    add(mochi, "Tomorrow", "09:00", 10, due=NEXT_DAY)
    done = add(mochi, "Done", "10:00", 10, due=DAY)
    done.mark_complete()
    planned, skipped = scheduler.build_daily_plan(DAY)
    assert planned == [today]
    assert skipped == []


def test_plan_selects_by_priority_then_time_within_budget():
    """With room for one task, the high-priority task wins over an earlier low one."""
    scheduler, mochi, _ = make_scheduler(budget=30)
    add(mochi, "Early low", "07:00", 30, priority="low")
    high = add(mochi, "Later high", "09:00", 30, priority="high")
    planned, skipped = scheduler.build_daily_plan(DAY)
    assert planned == [high]
    assert [t.description for t in skipped] == ["Early low"]


def test_plan_total_never_exceeds_budget():
    """The planned minutes stay within the owner's available minutes."""
    scheduler, mochi, _ = make_scheduler(budget=50)
    for i, minutes in enumerate([30, 25, 20, 10]):
        add(mochi, f"T{i}", f"{8 + i:02d}:00", minutes)
    planned, _ = scheduler.build_daily_plan(DAY)
    assert sum(t.duration_minutes for t in planned) <= 50


def test_plan_skips_oversized_task_and_keeps_going():
    """A task too big for the remaining budget is skipped, and later smaller ones still fit."""
    scheduler, mochi, _ = make_scheduler(budget=60)
    add(mochi, "First", "08:00", 40, priority="high")
    big = add(mochi, "Too big", "09:00", 40, priority="medium")
    small = add(mochi, "Small", "10:00", 15, priority="low")
    planned, skipped = scheduler.build_daily_plan(DAY)
    assert small in planned
    assert skipped == [big]


def test_plan_accepts_task_that_exactly_fills_budget():
    """A task whose duration equals the remaining budget is planned."""
    scheduler, mochi, _ = make_scheduler(budget=30)
    task = add(mochi, "Exact", "08:00", 30)
    planned, skipped = scheduler.build_daily_plan(DAY)
    assert planned == [task]
    assert skipped == []


def test_plan_with_zero_budget_skips_everything():
    """A zero-minute budget plans nothing."""
    scheduler, mochi, _ = make_scheduler(budget=0)
    add(mochi, "Walk", "08:00", 10)
    planned, skipped = scheduler.build_daily_plan(DAY)
    assert planned == []
    assert len(skipped) == 1


def test_plan_keeps_overlapping_tasks_and_conflicts_warn():
    """Overlapping tasks are both planned; the conflict is only a warning."""
    scheduler, mochi, bean = make_scheduler()
    add(mochi, "Walk", "08:00", 30)
    add(bean, "Feed", "08:10", 10)
    planned, _ = scheduler.build_daily_plan(DAY)
    assert len(planned) == 2
    assert len(scheduler.detect_conflicts(planned)) == 1


def test_plan_with_no_tasks_is_empty():
    """An owner with no tasks gets an empty plan."""
    scheduler, _, _ = make_scheduler()
    assert scheduler.build_daily_plan(DAY) == ([], [])


# --- explain_plan ---


def test_explain_plan_with_nothing_due():
    """With no planned or skipped tasks the explanation says nothing is due."""
    scheduler, _, _ = make_scheduler()
    assert scheduler.explain_plan([], []) == ["No tasks due."]


def test_explain_plan_has_one_line_per_task_and_mentions_budget():
    """Each planned and skipped task gets a line; skipped lines cite the budget."""
    scheduler, mochi, _ = make_scheduler(budget=30)
    add(mochi, "Fits", "08:00", 30, priority="high")
    add(mochi, "Too long", "09:00", 20, priority="low")
    planned, skipped = scheduler.build_daily_plan(DAY)
    lines = scheduler.explain_plan(planned, skipped)
    assert len(lines) == 2
    assert lines[0].startswith("Planned: Fits")
    assert lines[1].startswith("Skipped: Too long")
    assert "30-minute budget" in lines[1]
