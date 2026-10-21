# CLAUDE.md — PawPal+ project context

This file is the shared plan for every AI session on this repo. Read it fully before making changes.

## Project
PawPal+ is a pet-care planner (CodePath AI110, Module 2). Python OOP logic layer + Streamlit UI.
Workflow is **CLI-first**: logic in `pawpal_system.py` must work and be verified via `main.py` and pytest before `app.py` is wired up.

## How we work
- The human (Kyle) is lead architect. Propose, then implement; Kyle reviews every diff and makes every commit and push. **Never commit or push.**
- One phase per chat session. Stay inside the current phase's scope.
- Do **not** write `reflection.md` in Kyle's voice. You may list facts he can use (what you suggested, what changed, what tests show).
- If a suggestion deviates from the design below, say so explicitly so Kyle can accept or reject it (this feeds the reflection).
- Prefer readable over clever. If a "Pythonic" version is harder to follow, offer both.

## Files the grader expects
| File | Purpose |
|---|---|
| `pawpal_system.py` | All backend classes (logic layer) |
| `main.py` | CLI demo: 1 Owner, 2+ Pets, 3+ Tasks at different times, prints "Today's Schedule" |
| `tests/test_pawpal.py` | pytest suite; run with `python -m pytest` |
| `diagrams/uml.mmd` | Mermaid class diagram — **canonical file the grader reads**; must match final code |
| `README.md` | Overview, classes, Smarter Scheduling table, run/test instructions, sample CLI output and pytest output as fenced code blocks, Demo Walkthrough, confidence level (1–5 stars) |
| `reflection.md` | Kyle writes this |
| `ai_interactions.md` | Stretch: Agent Workflow + Prompt Comparison sections |
| `app.py` | Streamlit UI, imports from `pawpal_system.py` |

## Conventions
- Python 3.14. `@dataclass` for `Task` and `Pet` (Owner may be a dataclass too).
- 1-line docstrings on every method; type hints everywhere.
- Times are zero-padded `"HH:MM"` strings; convert with a helper (`_to_minutes`) for math. Dates are `datetime.date`.
- Priority is a string: `"low" | "medium" | "high"`, ranked via `PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}`.
- Frequency is a string: `"once" | "daily" | "weekly"`, mapped via `FREQUENCY_DAYS = {"daily": 1, "weekly": 7}`.
- Conflict detection returns warning strings; it never raises.
- No new dependencies without asking (exception: `tabulate` for the formatting stretch).

## Design (approved decisions A–L)
**Task** (dataclass): `task_id` (uuid4 hex[:8], default factory), `description`, `time`, `duration_minutes`, `priority`, `frequency`, `due_date`, `completed=False`, `pet_name=""`.
Methods: `mark_complete()`, `next_occurrence() -> Task | None` (new task, new id, due_date + timedelta(FREQUENCY_DAYS); None for "once").

**Pet** (dataclass): `name`, `species`, `age`, `tasks: list[Task]`.
Methods: `add_task(task)` (stamps `task.pet_name = self.name`), `remove_task(task_id)`, `get_tasks()`.

**Owner**: `name`, `available_minutes` (daily time budget), `pets: list[Pet]`.
Methods: `add_pet(pet)`, `get_pet(name)`, `get_all_tasks()` (every task across every pet).

**Scheduler**: holds `owner`. **Always reads tasks via `owner.get_all_tasks()`**, never from a single pet (rubric: multi-pet).
Every method that takes `tasks` treats it as optional: `None` means "all owner tasks", so calls compose, e.g. `sort_by_time(filter_tasks(pet_name="Mochi"))`.
- `sort_by_time(tasks)` — `sorted(..., key=lambda t: t.time)`
- `filter_tasks(tasks, pet_name=None, completed=None)`
- `detect_conflicts(tasks)` — flags **overlapping time ranges** (start + duration), across all pets; label each warning same-pet vs cross-pet.
- `mark_task_complete(task_id)` — marks complete, **keeps the completed task** (history), and if recurring adds `next_occurrence()` to the same pet; returns the new task or None.
- `build_daily_plan(day)` — only tasks due on `day` and not completed; greedy: priority first, then time; add until `available_minutes` is used up. Returns `(planned, skipped)`.
- `explain_plan(planned, skipped)` — human-readable reasons (why included / why skipped).

Relationships: Owner 1 → * Pet (aggregation); Pet 1 → * Task (composition); Scheduler → Owner (uses).

Known tradeoffs (for reflection): greedy plan can miss a better combination; `pet_name` duplicated on Task for simple filtering; time stored as text, not datetime (rejected a single `datetime` field to follow the assignment's HH:MM sorting); task list grows because completed tasks are kept.

## Phase plan
1. **Design** — UML draft (`diagrams/uml.mmd`), class skeletons in `pawpal_system.py` (attributes + empty stubs). Ask AI to review the skeleton for missing relationships.
2. **Core implementation** — implement the four classes; `main.py` demo with readable output; tests: `mark_complete()` changes status, `add_task()` increases count.
3. **UI integration** — import into `app.py`; store `Owner` in `st.session_state` (create only if missing); wire "Add pet" and "Add task" forms to class methods. Replace the starter's dict-based task list.
4. **Algorithms** — sorting, filtering, recurrence (timedelta), conflict detection; update `main.py` with out-of-order and overlapping tasks; README "Smarter Scheduling" table naming each method.
5. **Testing** — sorting correctness, daily recurrence creates the next-day task, conflict detection flags overlaps, plus edge cases (pet with no tasks, exact same time, plan only uses tasks due that day, budget exhausted). Light input validation in `__post_init__`.
6. **Polish** — Streamlit shows sorted plan, `st.warning` for conflicts, `st.table`/`st.success`; update `uml.mmd` to final; README Features + Demo Walkthrough + CLI sample.

### Stretch (all five planned, after the core works)
- **SF1 Agent mode:** `Scheduler.next_available_slot(duration, day)`; document in `ai_interactions.md` → Agent Workflow.
- **SF2 Persistence:** `Owner.save_to_json(path)` / `Owner.load_from_json(path)` via `dataclasses.asdict` + manual loader (dates ↔ ISO strings); `data.json`; README section.
- **SF3 Priority scheduling:** `sort_by_priority_then_time(tasks)`; README CLI examples.
- **SF4 Formatting:** `tabulate` tables + emoji/status markers in CLI; README section naming the library/functions.
- **SF5 Prompt comparison:** same recurring-task prompt to Opus vs Sonnet; table in `ai_interactions.md`.

## Commands
```
python -m venv .venv          # once
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
python main.py
python -m pytest
streamlit run app.py
```
Note: `pytest --cov` in the starter README needs `pytest-cov`, which is not in requirements.txt. Either add it or remove that line.
