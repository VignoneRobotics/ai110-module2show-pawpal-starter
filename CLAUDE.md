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
Methods: `add_pet(pet)` (raises `ValueError` on a duplicate pet name), `get_pet(name) -> Pet | None`, `get_all_tasks()` (every task across every pet), `find_task(task_id) -> tuple[Pet, Task] | None` (task plus its owning pet).

**Scheduler**: holds `owner`. **Always reads tasks via `owner.get_all_tasks()`**, never from a single pet (rubric: multi-pet).
Every method that takes `tasks` treats it as optional: `None` means "all owner tasks", so calls compose, e.g. `sort_by_time(filter_tasks(pet_name="Mochi"))`.
- `sort_by_time(tasks)` — `sorted(..., key=lambda t: (t.due_date, t.time, PRIORITY_RANK[t.priority], t.description))` — date first so recurring next-day copies sort chronologically; deterministic tie-break. Same-day order is unchanged.
- `filter_tasks(tasks, pet_name=None, completed=None)`
- `detect_conflicts(tasks)` — flags **overlapping time ranges** (start + duration), across all pets; label each warning same-pet vs cross-pet.
- `mark_task_complete(task_id)` — looks up via `owner.find_task`; marks complete, **keeps the completed task** (history), and if recurring adds `next_occurrence()` to the same pet; returns the new task or None. If the task is already completed (or not found), do nothing and return None (no duplicate next occurrence).
- `build_daily_plan(day)` — only tasks due on `day` and not completed; greedy first-fit: order by priority, then time; if a task doesn't fit the remaining budget, **skip it and continue** (never `break`). Returns `(planned, skipped)`. It does **not** drop overlapping tasks — conflicts are warnings only (callers run `detect_conflicts(planned)`).
- `explain_plan(planned, skipped)` — human-readable reasons. Recomputes from `self.owner.available_minutes` by walking `planned` in order. The only skip reason is "didn't fit the remaining budget" (not-due tasks are never in `skipped`), so no extra parameters are needed.

Relationships: Owner 1 → * Pet (aggregation); Pet 1 → * Task (composition); Scheduler → Owner (uses).

Known tradeoffs (for reflection): plan and conflict checks are separate (an overlapping pair can both be planned, with a warning); greedy plan can miss a better combination; `pet_name` duplicated on Task for simple filtering; time stored as text, not datetime (rejected a single `datetime` field to follow the assignment's HH:MM sorting); task list grows because completed tasks are kept.

## Design change log (facts for reflection 1b — Kyle writes the reflection)
- After the Phase 1 skeleton review (Sonnet 5.5): **accepted** adding `Owner.find_task` (scheduler needed the owning pet); **accepted** skip-and-continue for the budget; **chose** warn-only conflicts; **partly rejected** the suggestion that `explain_plan` needs the day or that `build_daily_plan` must return reasons — with warn-only conflicts the only skip reason is the budget, so it can be recomputed and signatures stay unchanged.

## Phase plan
1. **Design** — UML draft (`diagrams/uml.mmd`), class skeletons in `pawpal_system.py` (attributes + empty stubs). Ask AI to review the skeleton for missing relationships.
2. **Core implementation** — implement the four classes (incl. duplicate-pet-name rejection, `find_task`, `next_occurrence` from `due_date` not `date.today()`, double-complete guard); `main.py` demo with readable output; tests: `mark_complete()` changes status, `add_task()` increases count.
3. **UI integration** — import into `app.py`; store `Owner` in `st.session_state` (create only if missing); wire "Add pet" and "Add task" forms to class methods. Replace the starter's dict-based task list.
### Phase 4 algorithm decisions (approved M–S + review items)
- **M Conflict algorithm:** simple pairwise double loop (`for i ... for j in range(i+1, n)`), each pair checked once, no duplicate warnings. A sort-and-sweep version is evaluated in Step 5 as the "simplify/performance" comparison; keep whichever Kyle chooses.
- **N Overlap rule:** `a_start < b_end and b_start < a_end` (minutes via `_to_minutes`). Back-to-back (end == start) is **not** a conflict.
- **O Scope:** only compare tasks with the **same `due_date`** that are **not completed**.
- **P Warning format:** `Conflict (same pet: Mochi): Walk 08:00–08:30 overlaps Bath 08:15–08:45` / `Conflict (cross-pet: Mochi, Bean): ...`.
- **Q Recurrence:** `next_occurrence` uses `dataclasses.replace(self, task_id=<new uuid>, completed=False, due_date=self.due_date + timedelta(days=FREQUENCY_DAYS[freq]))`. Must override `task_id` (replace copies it otherwise). Returns None for "once".
- **R Filtering:** `None` = don't filter on that field; filters combine; `pet_name` match is case-insensitive (same as `Owner.get_pet`).
- **S Scope:** don't touch `app.py` in Phase 4. `main.py` uses `sort_by_time` (remove the inline `sorted()`), shows out-of-order tasks, a filtered view, a completed daily task with its next-day copy, and same-pet + cross-pet conflict warnings.
- **Display order:** `build_daily_plan` still *selects* by priority, but callers *display* `sort_by_time(planned)`; `explain_plan` output stays in selection order. No signature change.
- **Conflicts on the plan:** callers run `detect_conflicts(planned)` (CLI in Phase 4, `st.warning` in Phase 6).
- **Sort-key fix (after Step 3):** recurring copies exposed that a time-only key put tomorrow's 07:00 before today's 08:00, so `due_date` became the first key. CLI `format_task` shows due date and done/pending so same-time tasks on different days are distinguishable.
- **Rejected:** "overdue" filter (scope creep, signature change) — candidate for reflection 4b "next steps". Optimal/knapsack planning — greedy is the documented tradeoff.

4. **Algorithms** — sorting, filtering, recurrence (timedelta), conflict detection; update `main.py` with out-of-order and overlapping tasks; README "Smarter Scheduling" table naming each method.
5. **Testing** — tests always pass `due_date` explicitly (default is `date.today()`, which makes tests date-dependent). Sorting correctness, daily recurrence creates the next-day task, conflict detection flags overlaps, plus edge cases (pet with no tasks, exact same time, plan only uses tasks due that day, budget exhausted). Light input validation in `__post_init__`: valid HH:MM, known priority/frequency, positive duration, and reject tasks that run past midnight (start + duration > 24:00).
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
