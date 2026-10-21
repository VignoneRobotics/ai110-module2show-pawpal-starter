"""PawPal+ logic layer: Task, Pet, Owner, Scheduler (Phase 1 skeleton)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
FREQUENCY_DAYS = {"daily": 1, "weekly": 7}


def _to_minutes(time_str: str) -> int:
    """Convert a zero-padded "HH:MM" string to minutes since midnight."""


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

    def mark_complete(self) -> None:
        """Mark this task as completed."""

    def next_occurrence(self) -> Task | None:
        """Return a new task for the next recurrence, or None if frequency is "once"."""


@dataclass
class Pet:
    """A pet and the tasks that belong to it."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and stamp it with the pet's name."""

    def remove_task(self, task_id: str) -> None:
        """Remove the task with the given id from this pet."""

    def get_tasks(self) -> list[Task]:
        """Return all tasks belonging to this pet."""


@dataclass
class Owner:
    """A pet owner with a daily time budget and a list of pets."""

    name: str
    available_minutes: int = 480
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""

    def get_pet(self, name: str) -> Pet | None:
        """Return the pet with the given name, or None if not found."""

    def get_all_tasks(self) -> list[Task]:
        """Return every task across every pet."""


@dataclass
class Scheduler:
    """Builds sorted, filtered, conflict-checked plans from an owner's tasks."""

    owner: Owner

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Return tasks sorted by their "HH:MM" time."""

    def filter_tasks(
        self,
        tasks: list[Task] | None = None,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Return tasks matching the given pet name and completion status."""

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[str]:
        """Return warning strings for tasks with overlapping time ranges."""

    def mark_task_complete(self, task_id: str) -> Task | None:
        """Complete a task, add its next occurrence if recurring, and return it or None."""

    def build_daily_plan(self, day: date) -> tuple[list[Task], list[Task]]:
        """Return (planned, skipped) tasks for the day, within the owner's time budget."""

    def explain_plan(self, planned: list[Task], skipped: list[Task]) -> list[str]:
        """Return human-readable reasons for each included and skipped task."""
