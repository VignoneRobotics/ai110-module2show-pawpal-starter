"""CLI demo for PawPal+: builds one owner with two pets and prints today's schedule."""

import sys
import tempfile
from datetime import date
from pathlib import Path

from tabulate import tabulate

from pawpal_system import Owner, Pet, Scheduler, Task

# Piped Windows output defaults to cp1252, which cannot encode the emoji below.
sys.stdout.reconfigure(encoding="utf-8")

PRIORITY_ICONS = {"high": "🔴 high", "medium": "🟡 medium", "low": "🟢 low"}
HEADERS = ["date", "time", "pet", "task", "min", "priority", "status"]


def format_tasks(tasks: list[Task]) -> str:
    """Return the tasks as a rounded_grid table with emoji priority and status."""
    rows = [
        [
            t.due_date.isoformat(),
            t.time,
            t.pet_name,
            t.description,
            t.duration_minutes,
            PRIORITY_ICONS[t.priority],
            "✅ done" if t.completed else "⏳ pending",
        ]
        for t in tasks
    ]
    return tabulate(rows, headers=HEADERS, tablefmt="rounded_grid")


def print_conflicts(warnings: list[str]) -> None:
    """Print each conflict warning prefixed with a warning sign, or "(none)"."""
    for warning in warnings:
        print(f"  ⚠️ {warning}")
    if not warnings:
        print("  (none)")


def round_trip_demo(owner: Owner) -> None:
    """Save the owner to a temp JSON file, load it back, and report whether it matches."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "owner.json"
        owner.save_to_json(path)
        loaded = Owner.load_from_json(path)
    print(f"  Saved {len(owner.pets)} pets and {len(owner.get_all_tasks())} tasks to a temp file.")
    print(f"  Loaded {len(loaded.pets)} pets and {len(loaded.get_all_tasks())} tasks back.")
    print(f"  Loaded owner equals original (ids, dates, completed): {loaded == owner}")


def main() -> None:
    """Build sample data, plan today, and print the schedule with explanations."""
    today = date.today()

    owner = Owner("Kyle", available_minutes=75)
    mochi = Pet("Mochi", "dog", 4)
    bean = Pet("Bean", "cat", 2)
    owner.add_pet(mochi)
    owner.add_pet(bean)

    # Added deliberately out of time order.
    bean.add_task(Task("Laser playtime", "19:00", 40, "low", due_date=today))
    brush = Task("Brush coat", "18:00", 20, "low", frequency="daily", due_date=today)
    mochi.add_task(brush)
    bean.add_task(Task("Clean litter box", "12:00", 10, "medium", due_date=today))
    mochi.add_task(Task("Evening walk", "17:00", 25, "medium", due_date=today))
    bean.add_task(Task("Breakfast", "08:00", 15, "high", due_date=today))
    mochi.add_task(Task("Morning walk", "07:30", 30, "high", due_date=today))
    # Morning walk 07:30-08:00 and Breakfast 08:00-08:15 are back-to-back: NOT a conflict.
    # Same-pet overlap: Bath 17:15-17:45 vs Evening walk 17:00-17:25 (both Mochi).
    mochi.add_task(Task("Bath", "17:15", 30, "medium", due_date=today))
    # Cross-pet overlap: Training 12:05-12:25 (Mochi) vs Clean litter box 12:00-12:10 (Bean).
    mochi.add_task(Task("Training", "12:05", 20, "medium", due_date=today))

    scheduler = Scheduler(owner)

    # Complete a daily task: it stays as history and spawns tomorrow's copy.
    next_brush = scheduler.mark_task_complete(brush.task_id, today=today)
    repeat_call = scheduler.mark_task_complete(brush.task_id, today=today)

    planned, skipped = scheduler.build_daily_plan(today)

    print("=" * 56)
    print(f"Today's Schedule - {today.isoformat()}")
    print(f"Owner: {owner.name} | Pets: {', '.join(p.name for p in owner.pets)}")
    print(f"Time available: {owner.available_minutes} min")
    print("=" * 56)

    print("\nRecurring task demo (Brush coat, daily):")
    print(f"  Completed: id={brush.task_id} due={brush.due_date} completed={brush.completed}")
    if next_brush is not None:
        print(
            f"  Next copy: id={next_brush.task_id} due={next_brush.due_date} "
            f"completed={next_brush.completed} pet={next_brush.pet_name}"
        )
    print(f"  Completing it again returns: {repeat_call}")
    print(f"  Mochi now has {len(mochi.tasks)} tasks (completed one is kept).")

    print("\nAll tasks as entered:")
    print(format_tasks(owner.get_all_tasks()))

    print("\nAll tasks sorted by time:")
    print(format_tasks(scheduler.sort_by_time()))

    print("\nSorted by priority (then time):")
    print(format_tasks(scheduler.sort_by_priority()))

    print("\nMochi's tasks only (by time):")
    print(format_tasks(scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi"))))

    print("\nPending tasks only (by time):")
    print(format_tasks(scheduler.sort_by_time(scheduler.filter_tasks(completed=False))))

    print("\nPlanned (in time order):")
    print(format_tasks(scheduler.sort_by_time(planned)))

    print("\nConflicts among all pending tasks:")
    print_conflicts(scheduler.detect_conflicts())

    print("\nConflicts within the planned tasks:")
    print_conflicts(scheduler.detect_conflicts(planned))

    print("\nSkipped:")
    if skipped:
        print(format_tasks(skipped))
    else:
        print("  (none)")

    print("\nWhy:")
    for line in scheduler.explain_plan(planned, skipped):
        print(f"  - {line}")

    used = sum(t.duration_minutes for t in planned)
    print(f"\nPlanned {used} of {owner.available_minutes} min.")

    print("\nNext available slot (today, window 07:00-22:00):")
    for minutes in (30, 45, 240, 300):
        slot = scheduler.next_available_slot(minutes, today)
        print(f"  {minutes:>3} min -> {slot or '(none)'}")

    print("\nSave/load round trip (temp file):")
    round_trip_demo(owner)


if __name__ == "__main__":
    main()
