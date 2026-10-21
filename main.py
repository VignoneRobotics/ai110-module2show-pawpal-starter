"""CLI demo for PawPal+: builds one owner with two pets and prints today's schedule."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def format_task(task: Task) -> str:
    """Return a one-line description of a task for the schedule."""
    return (
        f"  {task.time}  {task.description} ({task.pet_name})"
        f"  {task.duration_minutes} min  {task.priority}"
    )


def main() -> None:
    """Build sample data, plan today, and print the schedule with explanations."""
    today = date.today()

    owner = Owner("Kyle", available_minutes=75)
    mochi = Pet("Mochi", "dog", 4)
    bean = Pet("Bean", "cat", 2)
    owner.add_pet(mochi)
    owner.add_pet(bean)

    mochi.add_task(Task("Morning walk", "07:30", 30, "high", due_date=today))
    mochi.add_task(Task("Brush coat", "18:00", 20, "low", due_date=today))
    bean.add_task(Task("Breakfast", "08:00", 15, "high", due_date=today))
    bean.add_task(Task("Clean litter box", "12:00", 10, "medium", due_date=today))
    bean.add_task(Task("Laser playtime", "19:00", 40, "low", due_date=today))

    scheduler = Scheduler(owner)
    planned, skipped = scheduler.build_daily_plan(today)

    print("=" * 56)
    print(f"Today's Schedule - {today.isoformat()}")
    print(f"Owner: {owner.name} | Pets: {', '.join(p.name for p in owner.pets)}")
    print(f"Time available: {owner.available_minutes} min")
    print("=" * 56)

    print("\nPlanned (in time order):")
    # Phase 4: replace this inline sort with scheduler.sort_by_time(planned)
    for task in sorted(planned, key=lambda t: t.time):
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
