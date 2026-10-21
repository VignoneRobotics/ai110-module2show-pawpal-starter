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
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
