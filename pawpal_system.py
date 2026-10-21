"""PawPal+ logic layer: Task, Pet, Owner, Scheduler (Phase 1 skeleton)."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}


def _to_minutes(time_str: str) -> int:
    """Convert a zero-padded "HH:MM" string to minutes since midnight."""
    hours, minutes = time_str.split(":")
    return int(hours) * 60 + int(minutes)


def _describe_range(task: Task) -> str:
    """Return "Description HH:MM-HH:MM" for a task's start and end time."""
    end = _to_minutes(task.time) + task.duration_minutes
    return f"{task.description} {task.time}-{end // 60:02d}:{end % 60:02d}"


def _time_range(task: Task) -> tuple[int, int]:
    """Return a task's (start, end) in minutes since midnight."""
    start = _to_minutes(task.time)
    return start, start + task.duration_minutes


def _conflict_warning(first: Task, second: Task) -> str:
    """Return the warning string for two overlapping tasks, earlier one first."""
    if first.pet_name == second.pet_name:
        label = f"same pet: {first.pet_name}"
    else:
        label = f"cross-pet: {first.pet_name}, {second.pet_name}"
    return f"Conflict ({label}): {_describe_range(first)} overlaps {_describe_range(second)}"


@dataclass
class Task:
    """A single pet-care task."""

    description: str
    time: str
    duration_minutes: int
    priority: str = "medium"
    frequency: str = "once"
    due_date: date = field(default_factory=date.today)
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    completed: bool = False
    pet_name: str = ""

    def __post_init__(self) -> None:
        """Reject a malformed time, unknown priority/frequency, bad duration, or a task past midnight."""
        if not re.fullmatch(r"[0-9]{2}:[0-9]{2}", self.time):
            raise ValueError(f"Invalid time {self.time!r}: use zero-padded HH:MM (00:00-23:59)")
        hours, minutes = int(self.time[:2]), int(self.time[3:])
        if hours > 23 or minutes > 59:
            raise ValueError(f"Invalid time {self.time!r}: hour must be 00-23 and minute 00-59")
        if self.priority not in PRIORITY_RANK:
            raise ValueError(
                f"Unknown priority {self.priority!r}: use {', '.join(PRIORITY_RANK)}"
            )
        if self.frequency != "once" and self.frequency not in FREQUENCY_DAYS:
            raise ValueError(
                f"Unknown frequency {self.frequency!r}: use once, {', '.join(FREQUENCY_DAYS)}"
            )
        if self.duration_minutes <= 0:
            raise ValueError(f"Duration must be positive, got {self.duration_minutes}")
        if _to_minutes(self.time) + self.duration_minutes > 24 * 60:
            raise ValueError(
                f"Task {self.description!r} at {self.time} for {self.duration_minutes} min "
                "runs past midnight"
            )

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """Return a new task for the next recurrence, or None if frequency is "once"."""
        if self.frequency not in FREQUENCY_DAYS:
            return None
        return replace(
            self,
            task_id=uuid.uuid4().hex[:8],
            completed=False,
            due_date=self.due_date + timedelta(days=FREQUENCY_DAYS[self.frequency]),
        )


@dataclass
class Pet:
    """A pet and the tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and stamp it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id from this pet."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_tasks(self) -> list[Task]:
        """Return all tasks belonging to this pet."""
        return list(self.tasks)


@dataclass
class Owner:
    """A pet owner with a daily time budget and a list of pets."""

    name: str
    available_minutes: int = 480
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner, rejecting a duplicate name."""
        if self.get_pet(pet.name) is not None:
            raise ValueError(f"Owner already has a pet named {pet.name!r}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name (case-insensitive), or None if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def get_all_tasks(self) -> list[Task]:
        """Return every task across every pet."""
        return [task for pet in self.pets for task in pet.get_tasks()]

    def find_task(self, task_id: str) -> tuple[Pet, Task] | None:
        """Return the (pet, task) pair for the given task id, or None if not found."""
        for pet in self.pets:
            for task in pet.tasks:
                if task.task_id == task_id:
                    return pet, task
        return None


@dataclass
class Scheduler:
    """Builds sorted, filtered, conflict-checked plans from an owner's tasks."""

    owner: Owner

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by due date, then "HH:MM" time, priority, and description."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(
            tasks,
            key=lambda t: (t.due_date, t.time, PRIORITY_RANK[t.priority], t.description),
        )

    def sort_by_priority(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by due date, then priority, "HH:MM" time, and description."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(
            tasks,
            key=lambda t: (t.due_date, PRIORITY_RANK[t.priority], t.time, t.description),
        )

    def filter_tasks(
        self,
        tasks: list[Task] | None = None,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Return tasks matching the given pet name and completion status."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        result = list(tasks)
        if pet_name is not None:
            result = [t for t in result if t.pet_name.lower() == pet_name.lower()]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        return result

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return warning strings for tasks with overlapping time ranges."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        pending = [t for t in tasks if not t.completed]

        warnings: list[str] = []
        for a, b in combinations(pending, 2):  # each pair is checked once
            if a.due_date != b.due_date:
                continue
            a_start, a_end = _time_range(a)
            b_start, b_end = _time_range(b)
            if a_start < b_end and b_start < a_end:
                first, second = (a, b) if a_start <= b_start else (b, a)
                warnings.append(_conflict_warning(first, second))
        return warnings

    def mark_task_complete(self, task_id: str) -> Task | None:
        """Complete a task, add its next occurrence if recurring, and return it or None."""
        found = self.owner.find_task(task_id)
        if found is None:
            return None
        pet, task = found
        if task.completed:
            return None
        task.mark_complete()
        next_task = task.next_occurrence()
        if next_task is not None:
            pet.add_task(next_task)
        return next_task

    def build_daily_plan(self, day: date) -> tuple[list[Task], list[Task]]:
        """Return (planned, skipped) tasks for the day, within the owner's time budget."""
        due = [
            t for t in self.owner.get_all_tasks()
            if t.due_date == day and not t.completed
        ]
        due.sort(key=lambda t: (PRIORITY_RANK[t.priority], _to_minutes(t.time)))

        planned: list[Task] = []
        skipped: list[Task] = []
        remaining = self.owner.available_minutes
        for task in due:
            if task.duration_minutes <= remaining:
                planned.append(task)
                remaining -= task.duration_minutes
            else:
                skipped.append(task)
        return planned, skipped

    def explain_plan(self, planned: list[Task], skipped: list[Task]) -> list[str]:
        """Return human-readable reasons for each included and skipped task."""
        if not planned and not skipped:
            return ["No tasks due."]

        budget = self.owner.available_minutes
        used = sum(t.duration_minutes for t in planned)
        lines = [
            f"Planned: {t.description} ({t.pet_name}) at {t.time}, "
            f"{t.duration_minutes} min, {t.priority} priority - fits in the {budget}-minute budget."
            for t in planned
        ]
        lines += [
            f"Skipped: {t.description} ({t.pet_name}) at {t.time} needs "
            f"{t.duration_minutes} min; did not fit in the {budget}-minute budget "
            f"(planned tasks use {used})."
            for t in skipped
        ]
        return lines
