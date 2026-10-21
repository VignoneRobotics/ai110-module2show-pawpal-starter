# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Implementation

The logic layer lives in `pawpal_system.py` as four classes; `main.py` is a CLI demo of them.

- **Task** (dataclass): one care activity with a description, `"HH:MM"` time, duration, priority, frequency, due date, completed flag, and the owning pet's name. `mark_complete()` sets the completed flag.
- **Pet** (dataclass): a pet and its list of tasks. `add_task()` stamps each task with the pet's name.
- **Owner**: a person with a daily time budget (`available_minutes`) and a list of pets. It rejects duplicate pet names and provides `get_all_tasks()` and `find_task()`.
- **Scheduler**: holds an owner and builds the plan. `build_daily_plan(day)` takes tasks due that day that are not completed, orders them by priority then time, and adds each one that fits the remaining time budget. `explain_plan()` gives a reason for every planned and skipped task.

**How they connect:** an Owner has many Pets, each Pet has many Tasks, and the Scheduler reads every task through `owner.get_all_tasks()`, so a plan covers all of the owner's pets.

```bash
python main.py       # print today's schedule
python -m pytest     # run the tests
```

## 🖥️ Sample Output

Output of `python main.py` (one owner, two pets, five tasks, 75-minute budget):

```
========================================================
Today's Schedule - 2026-10-20
Owner: Kyle | Pets: Mochi, Bean
Time available: 75 min
========================================================

Planned (in time order):
  07:30  Morning walk (Mochi)  30 min  high
  08:00  Breakfast (Bean)  15 min  high
  12:00  Clean litter box (Bean)  10 min  medium
  18:00  Brush coat (Mochi)  20 min  low

Skipped:
  19:00  Laser playtime (Bean)  40 min  low

Why:
  - Planned: Morning walk (Mochi) at 07:30, 30 min, high priority - fits in the 75-minute budget.
  - Planned: Breakfast (Bean) at 08:00, 15 min, high priority - fits in the 75-minute budget.
  - Planned: Clean litter box (Bean) at 12:00, 10 min, medium priority - fits in the 75-minute budget.
  - Planned: Brush coat (Mochi) at 18:00, 20 min, low priority - fits in the 75-minute budget.
  - Skipped: Laser playtime (Bean) at 19:00 needs 40 min; did not fit in the 75-minute budget (planned tasks use 75).

Planned 75 of 75 min.
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting | `Scheduler.sort_by_time` | Orders by due date, then "HH:MM" time, priority, description. Same-day order is unchanged; recurring next-day copies sort after today's tasks. |
| Filtering | `Scheduler.filter_tasks` | Filters by `pet_name` (case-insensitive) and/or `completed`; `None` skips a filter. Composes with sorting: `sort_by_time(filter_tasks(pet_name="Mochi"))`. |
| Conflict detection | `Scheduler.detect_conflicts` | Pairwise check of overlapping ranges (`a_start < b_end and b_start < a_end`) on the same due date, ignoring completed tasks. Back-to-back is not a conflict. Returns same-pet / cross-pet warning strings and never raises. |
| Recurring tasks | `Task.next_occurrence`, `Scheduler.mark_task_complete` | Completing a daily/weekly task keeps it as history and adds a copy with a new id, due date + 1 or 7 days, on the same pet. "once", unknown ids, and already-completed tasks return None, so no duplicates. |
| Daily plan | `Scheduler.build_daily_plan`, `Scheduler.explain_plan` | Takes tasks due that day and not completed, picks by priority then time, skips any task that does not fit the remaining budget and continues. Overlaps are warnings only (run `detect_conflicts(planned)`). `explain_plan` gives a reason for each planned and skipped task. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
