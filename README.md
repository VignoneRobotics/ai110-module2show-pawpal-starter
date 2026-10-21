# 🐾 PawPal+

PawPal+ is a pet-care planner for a busy owner. You add your pets and their care tasks (walks, feeding, meds, grooming), and it builds a daily plan that fits your time budget, puts the most important tasks first, flags tasks that overlap, and explains why each task was planned or skipped. It is built as a Python logic layer (`pawpal_system.py`) with a CLI demo (`main.py`), a pytest suite, and a Streamlit UI (`app.py`).

## ✨ Features

- **Multiple pets per owner**, each with its own task list; the scheduler always works across all pets.
- **Tasks** with an `HH:MM` time, duration, priority (low/medium/high), frequency (once/daily/weekly) and due date, validated on creation (bad times, unknown values, zero durations and tasks that run past midnight are rejected).
- **Daily plan within a time budget:** picks tasks by priority, skips any task that doesn't fit and keeps going, and explains every decision.
- **Sorting** by time or by priority, and **filtering** by pet and by done/pending.
- **Conflict warnings** for overlapping tasks (same pet or across pets), with a suggested free slot for each.
- **Recurring tasks:** completing a daily or weekly task creates the next one; completing it late skips the missed dates and keeps the original schedule.
- **Next free slot** finder for a task of any length.
- **Saves your data** to `data.json`, so pets and tasks survive restarting the app.
- **Formatted CLI output** with tables and status/priority markers.

## 🚀 Getting started

```bash
python -m venv .venv
source .venv/bin/activate      # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python main.py                 # CLI demo
python -m pytest               # run the tests
streamlit run app.py           # the app
```

## 🧱 System design

The final class diagram is in [`diagrams/uml.mmd`](diagrams/uml.mmd).

- **Task** (dataclass): one care activity. Validates itself on creation, can mark itself complete, and creates its next occurrence if it repeats (`next_occurrence(today)`).
- **Pet** (dataclass): a pet and its tasks. `add_task()` stamps each task with the pet's name.
- **Owner** (dataclass): name, daily time budget (`available_minutes`) and pets. Rejects duplicate pet names, provides `get_all_tasks()` and `find_task()`, and saves/loads itself as JSON.
- **Scheduler**: the "brain". It reads every task through `owner.get_all_tasks()`, so every feature covers all pets. It sorts, filters, finds conflicts and free slots, completes tasks, and builds and explains the daily plan.

**Relationships:** an Owner has many Pets, each Pet has many Tasks, and the Scheduler uses the Owner.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time` | Due date, then `HH:MM` time, priority, description. Zero-padded times sort correctly as text, and next-day copies sort after today's tasks. |
| Sorting by priority | `Scheduler.sort_by_priority` | Within each day: priority first, then time. |
| Filtering | `Scheduler.filter_tasks` | By `pet_name` (case-insensitive) and/or `completed`; `None` skips a filter. Composes with sorting: `sort_by_time(filter_tasks(pet_name="Mochi"))`. |
| Conflict detection | `Scheduler.find_conflict_pairs`, `Scheduler.detect_conflicts` | Checks each pair once (`itertools.combinations`) for overlapping ranges on the same day (`a_start < b_end and b_start < a_end`), ignoring completed tasks. Back-to-back is not a conflict. Returns same-pet / cross-pet warnings and never raises. |
| Recurring tasks | `Task.next_occurrence`, `Scheduler.mark_task_complete` | Completing a daily/weekly task keeps it as history and adds a copy with a new id on the same pet. If completed late, missed dates are skipped and the copy lands on the next scheduled date after today. "once", unknown ids and already-completed tasks return None. |
| Next free slot | `Scheduler.next_available_slot` | Walks the gaps between the day's pending tasks (07:00-22:00 by default) and returns the first start time where the duration fits, or None. |
| Daily plan | `Scheduler.build_daily_plan`, `Scheduler.explain_plan` | Tasks due that day and not completed, picked by priority then time; a task that doesn't fit the remaining budget is skipped and the plan continues. Overlaps are warnings only. `explain_plan` gives a reason for every planned and skipped task. |

## 🖥️ Sample Output

Excerpt of `python main.py` (one owner, two pets, nine tasks, 75-minute budget; the full output also shows every sorted and filtered view):

```
========================================================
Today's Schedule - 2026-10-21
Owner: Kyle | Pets: Mochi, Bean
Time available: 75 min
========================================================

Planned (in time order):
╭────────────┬────────┬───────┬──────────────────┬───────┬────────────┬────────────╮
│ date       │ time   │ pet   │ task             │   min │ priority   │ status     │
├────────────┼────────┼───────┼──────────────────┼───────┼────────────┼────────────┤
│ 2026-10-21 │ 07:30  │ Mochi │ Morning walk     │    30 │ 🔴 high    │ ⏳ pending │
├────────────┼────────┼───────┼──────────────────┼───────┼────────────┼────────────┤
│ 2026-10-21 │ 08:00  │ Bean  │ Breakfast        │    15 │ 🔴 high    │ ⏳ pending │
├────────────┼────────┼───────┼──────────────────┼───────┼────────────┼────────────┤
│ 2026-10-21 │ 12:00  │ Bean  │ Clean litter box │    10 │ 🟡 medium  │ ⏳ pending │
├────────────┼────────┼───────┼──────────────────┼───────┼────────────┼────────────┤
│ 2026-10-21 │ 12:05  │ Mochi │ Training         │    20 │ 🟡 medium  │ ⏳ pending │
╰────────────┴────────┴───────┴──────────────────┴───────┴────────────┴────────────╯

Conflicts within the planned tasks:
  ⚠️ Conflict (cross-pet: Bean, Mochi): Clean litter box 12:00-12:10 overlaps Training 12:05-12:25

Skipped:
╭────────────┬────────┬───────┬────────────────┬───────┬────────────┬────────────╮
│ date       │ time   │ pet   │ task           │   min │ priority   │ status     │
├────────────┼────────┼───────┼────────────────┼───────┼────────────┼────────────┤
│ 2026-10-21 │ 17:00  │ Mochi │ Evening walk   │    25 │ 🟡 medium  │ ⏳ pending │
├────────────┼────────┼───────┼────────────────┼───────┼────────────┼────────────┤
│ 2026-10-21 │ 17:15  │ Mochi │ Bath           │    30 │ 🟡 medium  │ ⏳ pending │
├────────────┼────────┼───────┼────────────────┼───────┼────────────┼────────────┤
│ 2026-10-21 │ 19:00  │ Bean  │ Laser playtime │    40 │ 🟢 low     │ ⏳ pending │
╰────────────┴────────┴───────┴────────────────┴───────┴────────────┴────────────╯

Why:
  - Planned: Morning walk (Mochi) at 07:30, 30 min, high priority - fits in the 75-minute budget.
  - Planned: Breakfast (Bean) at 08:00, 15 min, high priority - fits in the 75-minute budget.
  - Planned: Clean litter box (Bean) at 12:00, 10 min, medium priority - fits in the 75-minute budget.
  - Planned: Training (Mochi) at 12:05, 20 min, medium priority - fits in the 75-minute budget.
  - Skipped: Evening walk (Mochi) at 17:00 needs 25 min; did not fit in the 75-minute budget (planned tasks use 75).
  - Skipped: Bath (Mochi) at 17:15 needs 30 min; did not fit in the 75-minute budget (planned tasks use 75).
  - Skipped: Laser playtime (Bean) at 19:00 needs 40 min; did not fit in the 75-minute budget (planned tasks use 75).

Planned 75 of 75 min.

Next available slot (today, window 07:00-22:00):
   30 min -> 07:00
   45 min -> 08:15
  240 min -> 12:25
  300 min -> (none)
```

## 🧪 Testing PawPal+

```bash
python -m pytest        # full suite
python -m pytest -v     # one line per test
```

### What the tests cover

All 81 tests live in `tests/test_pawpal.py`, use fixed dates with an explicit `due_date` (nothing depends on today's date), and are grouped like the file:

- **Validation:** bad `HH:MM` times (such as `7:30` and `25:00`), unknown priority or frequency, duration of 0 or less, and tasks that run past midnight. A task ending exactly at 24:00 is allowed.
- **Owner / Pet:** duplicate pet names rejected (case-insensitive), `get_pet`, `get_all_tasks` across pets, `remove_task`, `find_task`.
- **Sorting:** chronological order, priority tie-break, next-day tasks after today's, an empty owner, sorting a filtered list, and priority-first sorting.
- **Filtering:** by pet (case-insensitive), by completion status, and both combined.
- **Recurrence:** daily (+1 day) and weekly (+7 days), "once" creates nothing, no duplicate on double completion, unknown ids, and late completion (skips missed dates, keeps the weekday, the "next date equals today" boundary).
- **Conflicts:** exact warning text for same-pet and cross-pet overlaps, same start time, back-to-back tasks in both insertion orders, different days and completed tasks ignored, each pair reported once, and `find_conflict_pairs` ordering.
- **Daily plan and `explain_plan`:** only pending tasks due that day, priority selection within the budget, an oversized task skipped while later ones still fit, exact-fit and zero budgets, overlapping tasks planned with a warning.
- **Persistence:** a save/load round trip keeps pets, tasks, ids, dates and completed status; a missing file and invalid task data raise errors.
- **Next free slot:** empty day, a gap between tasks, an exact back-to-back fit, no room, completed tasks and other days ignored, and the window end.

**Mutation check:** temporarily changing `<` to `<=` in the overlap check left all tests passing, because the back-to-back test only added the earlier task first. I added `test_back_to_back_tasks_do_not_conflict_reverse_order`, confirmed it fails against the broken code, then restored the code.

Sample test output (middle trimmed):

```
============================= test session starts ==============================
collecting ... collected 81 items

tests/test_pawpal.py::test_mark_complete_sets_completed_true PASSED      [  1%]
tests/test_pawpal.py::test_add_task_increases_count_and_stamps_pet_name PASSED [  2%]
tests/test_pawpal.py::test_task_rejects_bad_time[7:30] PASSED            [  3%]
...
tests/test_pawpal.py::test_next_slot_respects_window_end PASSED          [ 97%]
tests/test_pawpal.py::test_next_slot_skips_past_task_that_starts_before_window PASSED [ 98%]
tests/test_pawpal.py::test_next_slot_rejects_non_positive_duration PASSED [100%]

============================== 81 passed ==============================
```

**Confidence Level:** ★★★★☆

4/5: 81 tests cover the core behaviors and edge cases, and a deliberate mutation confirmed they catch real bugs; one star off because the Streamlit UI is only tested by hand and the daily plan is greedy rather than optimal.

## 🌟 Stretch features

### Agent mode (SF1): next available slot
`Scheduler.next_available_slot(duration_minutes, day, window_start="07:00", window_end="22:00")` was built by Claude Code in agent (auto) mode across four files. The Streamlit app suggests a free slot under each conflict warning and has a "Find a free slot" tool. What the agent did, and what I had to correct, is in [`ai_interactions.md`](ai_interactions.md#agent-workflow-sf7).

### Data persistence (SF2)
`Owner.save_to_json(path)` and `Owner.load_from_json(path)` save the whole household (pets, tasks, ids, dates, completed status) using Python's built-in `json` and `dataclasses.asdict`, with dates stored as ISO strings. Loading rebuilds every task with `Task(**data)`, so the same validation runs and a bad file is rejected instead of loaded. The app loads `data.json` on startup and saves after every change; `data.json` is git-ignored. `main.py` shows a round trip with a temporary file:

```
Save/load round trip (temp file):
  Saved 2 pets and 9 tasks to a temp file.
  Loaded 2 pets and 9 tasks back.
  Loaded owner equals original (ids, dates, completed): True
```

### Priority-based scheduling (SF3)
`Scheduler.sort_by_priority(tasks)` sorts by priority first, then time, within each day (dates still come first, so next week's high-priority task never jumps ahead of today's). The daily plan also selects by priority. Example where the two orders differ:

```
sort_by_time:     ['07:00 Play fetch (low)', '08:00 Breakfast (medium)', '18:00 Heartworm pill (high)']
sort_by_priority: ['18:00 Heartworm pill (high)', '08:00 Breakfast (medium)', '07:00 Play fetch (low)']
```

### Professional formatting (SF4)
The CLI uses the [`tabulate`](https://pypi.org/project/tabulate/) library (`tabulate[widechars]`, which adds `wcwidth` so emoji columns line up). `format_tasks()` in `main.py` renders every task list with `tablefmt="rounded_grid"`, priorities as 🔴 high / 🟡 medium / 🟢 low, status as ✅ done / ⏳ pending, and `print_conflicts()` prefixes warnings with ⚠️. Emoji stay in the display layer only; `pawpal_system.py` produces plain ASCII text. `main.py` switches stdout to UTF-8 so the output doesn't crash when piped on Windows. The Streamlit app uses `st.table`, `st.success`, `st.warning` and `st.info` with the same markers.

### Prompt / model comparison (SF5)
I gave Claude Opus 5.5 and Claude Sonnet 5.5 the same prompt about late-completed recurring tasks and combined the best of both answers. The comparison table and decision are in [`ai_interactions.md`](ai_interactions.md#prompt-comparison-sf11).

## 📸 Demo Walkthrough

Run `streamlit run app.py`. A browser tab opens at `localhost:8501`.

1. **Set up the owner.** At the top, type the owner's name (for example "Kyle") and set the daily time budget, for example 75 minutes. Changes are saved to `data.json` right away.
2. **Add pets.** Under "Add a pet", add "Mochi" (dog) and "Bean" (cat). Adding "mochi" again shows a red error instead of crashing, because pet names must be unique.
3. **Add tasks.** Under "Add a task", pick a pet and enter a description, time, duration, priority and frequency. Due dates default to today. For the demo, add a high-priority 07:30 walk for Mochi, a high-priority 08:00 breakfast for Bean, a daily 12:00 litter-box task for Bean, a 12:05 training session for Mochi (it overlaps the litter box), and a long low-priority 19:00 playtime. Entering 23:30 with a 45-minute duration shows an error, because tasks can't run past midnight.
4. **Browse the task list.** The "Task list" table is always sorted by date and time. Use the Pet and Status dropdowns to show one pet's tasks or only pending/done tasks.
5. **Complete a recurring task.** Under "Mark a task complete", pick the daily litter-box task and click "Mark complete". A green message confirms it and names tomorrow's new copy, which appears in the task list; the finished task stays listed as ✅ Done.
6. **Find a free slot.** Under "Find a free slot", enter a duration (for example 45 minutes) to see the first gap in today's schedule where it fits.
7. **Generate the schedule.** Click "Generate schedule". Conflict warnings appear first (Training overlaps the litter box, across two pets), each with a 💡 suggested free time for the later task. Below them is the plan in time order, a "Skipped tasks" table for anything that didn't fit the budget, and a "Why this plan?" expander that explains each decision.
8. **Restart the app.** Stop it with Ctrl+C and run `streamlit run app.py` again. Your owner, pets and tasks are reloaded from `data.json`.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
