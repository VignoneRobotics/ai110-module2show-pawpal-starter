# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Add a "next available slot" feature (SF1) in agent mode: a `Scheduler.next_available_slot(duration, day, window_start, window_end)` method that walks the gaps between a day's pending tasks and returns the first start time where the task fits, wired into the Streamlit UI, the CLI demo, and the test suite. I approved its plan in auto mode so it could edit several files without stopping.

**What did the agent do?**

- **Files changed:** `pawpal_system.py` (new method plus a time-formatting helper), `app.py` (a "Find a free slot" input and a 💡 suggestion under each conflict warning), `main.py` (a demo section), and `tests/test_pawpal.py` (8 new tests: empty day, a gap between tasks, an exact back-to-back fit, no room, ignoring completed tasks and other days, and the window end).
- **Commands run:** `python main.py`, `python -m pytest` (73 passed), a headless Streamlit check, `git status`, and `rm -f data.json`.

**What did you have to verify or fix manually?**

- I reviewed every diff in the Source Control tab, re-ran the tests and the demo myself, and checked the free-slot suggestions in the browser.
- The agent deleted my `data.json` with `rm -f` without checking what was in it. It only held test data, but it showed me that auto mode can take destructive actions I didn't ask for, so I review its command list as well as the diffs.
- The agent duplicated the overlap logic inside `app.py` to find which tasks conflict. I had it move that into the logic layer instead (`find_conflict_pairs`), so the UI and the scheduler can't drift apart.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | Claude Opus 5.5 (VS Code extension, Plan mode) | Claude Sonnet 5.5 (VS Code extension, Plan mode) |
| **Prompt** | Identical for both: "Read CLAUDE.md and pawpal_system.py. Problem: `Task.next_occurrence` sets the next due date to `due_date + FREQUENCY_DAYS`. If a daily or weekly task is completed weeks late, the new copy is already in the past. Propose a fix (policy + code for `next_occurrence`, plus any tests). Explain the tradeoffs. Don't edit files." | (same) |
| **Response summary** | Policy: skip missed dates and keep the original schedule. Added an optional `today` parameter; when it's left out, the old behavior is kept, so the logic layer never reads the real clock. Wrote full code for 5 tests and listed both callers and the docs that would need updating. | The same policy, presented as a clear A/B/C options table. Defaulted to `today or date.today()`. Proposed 7 test cases, including the "next date equals today" boundary and the scheduler path. |
| **What was useful** | It read `CLAUDE.md`, the tests and the callers before answering. Its design keeps tests independent of the real date. It flagged every doc that would go stale. | The options table made the trade-offs easy to compare. Its boundary and scheduler-path test cases were ones Opus didn't list. |
| **Problems noticed** | Forgetting to pass `today` silently gives the old behavior. | It read only `pawpal_system.py`, against the prompt. Reading the real clock by default would make tests depend on the date, which breaks a project rule in `CLAUDE.md`, and it admitted existing tests "may break." |
| **Decision** | ✅ Used its signature and its "no real clock in the logic layer" rule | ✅ Used its boundary and scheduler-path tests |

**Which approach did you use in your final implementation and why?**

A combination. Both models independently proposed the same policy (skip missed dates, keep the original schedule), which gave me confidence it was the right behavior. I took Opus's design: `today` is an optional parameter and the logic layer never reads the real clock, because Sonnet's `date.today()` default would have made my tests depend on the current date. I added Sonnet's boundary and scheduler-path tests. I also chose the simpler `while` loop over the arithmetic formula both offered, because it's easier to read and the speed difference doesn't matter at this scale. The main lesson: Sonnet skipped reading `CLAUDE.md`, so it missed a project rule. Opus's more careful context-gathering mattered more than raw capability on this task.
