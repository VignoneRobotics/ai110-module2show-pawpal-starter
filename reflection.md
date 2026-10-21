# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I started from three things a user needs to do: add a pet, schedule a care task (when, how long, how important, how often it repeats), and see today's plan across all their pets, sorted, with conflicts flagged and a reason for each choice.

My initial UML had four classes:
- **Task** (dataclass): one care activity. It holds a description, an `HH:MM` time, a duration, a priority, a frequency (once/daily/weekly), a due date, whether it's done, and the pet's name. It can mark itself done and create its next occurrence if it repeats.
- **Pet** (dataclass): name, species, age and its own list of tasks. It adds, removes and lists those tasks.
- **Owner**: name, a daily time budget in minutes, and a list of pets. It is the single place to get every task across every pet (`get_all_tasks`).
- **Scheduler**: the "brain". It holds the Owner and reads tasks only through it, so it always works across multiple pets. It sorts, filters, detects overlapping tasks, completes tasks (creating the next one for repeating tasks), and builds a daily plan that fits the time budget, with an explanation.

Relationships: an Owner has many Pets, a Pet has many Tasks, and the Scheduler uses the Owner.

**b. Design changes**

Yes. After generating the skeleton I asked Claude to review it against my design notes, and I checked its findings in a separate planning chat.
- **Added `Owner.find_task(task_id)`.** `mark_task_complete` only receives a task ID, but to create the next occurrence of a repeating task it has to know which pet owns it.
- **Skip and keep going.** If a task doesn't fit the remaining time, the plan skips it and moves on instead of stopping, so one long task can't block several short ones.
- **Sort by date first.** Once completing a daily task created tomorrow's copy, sorting by time alone put tomorrow's 07:00 task before today's 08:00. I made the due date the first sort key.
- **Recurrence after late completion.** Originally the next copy was always `due_date + 1 or 7 days`, so a task completed weeks late produced a copy that was already overdue. I changed it to skip the missed dates and keep the original schedule (this came out of the model comparison in `ai_interactions.md`).
- **Conflict pairing moved into the logic layer** (`find_conflict_pairs`) after the agent duplicated the overlap rule inside `app.py`.

I partly rejected one suggestion: the AI said `explain_plan` would need the day passed in, or that `build_daily_plan` would have to return its reasons. Because conflicts only produce warnings, the only reason a task is skipped is the time budget, so `explain_plan` can recompute that and I kept the original method signatures.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:
- **Which day** a task is due and whether it's already done (only pending tasks due that day are planned).
- **The owner's daily time budget** (`available_minutes`).
- **Priority** (high, medium, low), then **time of day** as the tie-breaker.
- **Clock overlaps** between tasks, for the same pet or across pets.

I decided priority matters most because missing a high-priority task (medication, feeding) has real consequences, while missing a low-priority one (playtime) doesn't. The time budget is a hard limit, since the owner simply doesn't have more time. Overlaps are treated as information rather than a hard rule: two overlapping tasks can sometimes be done together (feeding two cats at once), so the owner decides.

**b. Tradeoffs**

The daily plan is **greedy**: it takes tasks in priority order and adds each one that still fits the budget. It can miss a combination that fills the time better (for example, two medium tasks that would have fit where one long one was chosen). That is reasonable here because the owner cares more about the most important tasks getting done than about using every minute, a greedy plan is easy to explain line by line, and an optimal search would be much harder to understand and test for a small benefit.

A second, smaller tradeoff: I kept the conflict check as a simple pairwise loop (`itertools.combinations`) instead of a faster sort-and-sweep version the AI offered. The faster version's correctness depended on a sorting argument that's harder to verify, and with tens of tasks the speed difference doesn't matter.

---

## 3. AI Collaboration

**a. How you used AI**

I used two AI setups with different jobs. In a planning chat (Claude Opus 5.5 in the Claude app, linked to my repo) I made the design decisions: classes, method responsibilities, tradeoffs, and which stretch features to build. I recorded them in a `CLAUDE.md` file that Claude Code loads automatically in every session, so I didn't have to re-explain the design each time. Then I used Claude Sonnet 5.5 in VS Code to write the skeleton, the logic, the demo, the UI and the tests, usually in Plan mode so I approved a plan before any edits, and with a fresh session for most phases.

The most helpful prompts were tightly scoped by phase: they named exactly which methods to implement, which to leave as stubs, and which files not to touch, and asked for a plan first. Asking the assistant to review a file against `CLAUDE.md` with a specific question ("Any missing relationships or likely logic bottlenecks?") produced much more useful feedback than a general "review my code". Asking it to suggest test cases before writing them, and to show tests failing before implementing validation, also worked well.

**b. Judgment and verification**

- After the core implementation, the assistant's summary claimed `find_task` "goes beyond the CLAUDE.md design" and hadn't been added to the UML. I checked both files and it was already in each. The assistant hadn't re-read the file. Since then I check its summaries against the actual files.
- In the model comparison, Sonnet proposed defaulting to `date.today()` inside the logic layer. I rejected that because it would make my tests depend on the real date, and used Opus's optional `today` parameter instead.
- When the agent built the free-slot feature, it deleted my `data.json` without checking it and duplicated the overlap logic in `app.py`. I had the logic moved back into the scheduler.

To verify, I read every diff in the Source Control tab before committing, ran `python -m pytest` and `python main.py` after each change, checked the demo output by hand (for example 30 + 15 + 10 + 20 = 75 minutes, so the 40-minute task being skipped was right), and clicked through the Streamlit app myself.

**c. AI strategy**

- **Most effective features:** Plan mode (a plan to approve before any edit), the diff view, and `CLAUDE.md` as shared context across sessions.
- **Separate chat sessions per phase** kept each session focused on one job and stopped it from carrying assumptions forward. The cost was that a new session only knew what was in `CLAUDE.md`, which is why I kept that file updated after every design decision.
- **Being the lead architect** meant the AI proposed and I decided: I accepted, changed or rejected its suggestions, and I was the one who caught where it was wrong. The AI wrote most of the code quickly, but the design decisions and the checking were mine.

---

## 4. Testing and Verification

**a. What you tested**

The suite has 81 tests covering input validation, owner/pet behavior, sorting by time and by priority, filtering, recurrence (daily, weekly, once, double completion, late completion), conflict detection (same pet, across pets, same start time, back-to-back, different days, completed tasks), the daily plan and its explanation, JSON save/load, and the free-slot finder. All tests use fixed dates so they never depend on today's date.

These tests matter because the scheduler's value is in the details: an off-by-one in the overlap rule, a duplicate next occurrence, or a wrong sort order would quietly produce a wrong plan. To check that the tests catch real bugs, I deliberately changed `<` to `<=` in the overlap check. Every test still passed, because the back-to-back test only added tasks earlier-first. I added a reverse-order test, confirmed it failed against the broken code, then restored the code.

**b. Confidence**

★★★★☆ (4/5). The core behaviors and edge cases are covered and the mutation check showed the tests catch real bugs. One star off because the Streamlit UI is only tested by hand and the plan is greedy rather than optimal.

Next I would test: tasks that span two days, very large numbers of tasks, a plan for a future day, the UI flows with Streamlit's testing tools, and an "overdue tasks" view so missed tasks don't silently disappear.

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the design-first workflow. Deciding the classes and tradeoffs up front and writing them into `CLAUDE.md` meant every later session built on the same plan, and changes (like the date-first sort and the late-completion fix) were deliberate decisions rather than accidents. I'm also happy with the test suite, especially finding a real gap with the mutation check.

**b. What you would improve**

I would plan for more than one day at a time and add an "overdue" view, so tasks missed in the past are visible instead of skipped. I would also make conflict handling smarter, for example offering to move a task automatically, and add automated UI tests.

**c. Key takeaway**

AI is fast at writing code but it doesn't hold the whole system in its head: it made confident claims that were wrong, skipped instructions, and took actions I didn't ask for. The design, the context it works from, and the verification have to come from me. Writing the design down and checking every diff and test result is what made working with AI reliable.
