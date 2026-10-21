"""CLI demo for PawPal+: builds one owner with two pets and prints today's schedule."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def format_task(task: Task) -> str:
    """Return a one-line description of a task for the schedule."""
    status = "done" if task.completed else "pending"
    return (
        f"  {task.due_date.isoformat()} {task.time}  {task.description} ({task.pet_name})"
        f"  {task.duration_minutes} min  {task.priority}  [{status}]"
    )


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

    scheduler = Scheduler(owner)

    # Complete a daily task: it stays as history and spawns tomorrow's copy.
    next_brush = scheduler.mark_task_complete(brush.task_id)
    repeat_call = scheduler.mark_task_complete(brush.task_id)

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
    for task in owner.get_all_tasks():
        print(format_task(task))

    print("\nAll tasks sorted by time:")
    for task in scheduler.sort_by_time():
        print(format_task(task))

    print("\nMochi's tasks only (by time):")
    for task in scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi")):
        print(format_task(task))

    print("\nPending tasks only (by time):")
    for task in scheduler.sort_by_time(scheduler.filter_tasks(completed=False)):
        print(format_task(task))

    print("\nPlanned (in time order):")
    for task in scheduler.sort_by_time(planned):
        print(format_task(task))

    print("\nSkipped:")
    if skipped:
        for task in skipped:
            print(format_task(task))
    else:
        print("  (none)")

    print("\nWhy:")
    for line in scheduler.explain_plan(planned, skipped):
        print(f"  - {line}")

    used = sum(t.duration_minutes for t in planned)
    print(f"\nPlanned {used} of {owner.available_minutes} min.")


if __name__ == "__main__":
    main()
