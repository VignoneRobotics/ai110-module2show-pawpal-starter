from datetime import date
from pathlib import Path

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

DATA_FILE = Path(__file__).parent / "data.json"

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Create the single Owner once (from data.json if it exists); later reruns reuse the stored object.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
    if DATA_FILE.exists():
        try:
            st.session_state.owner = Owner.load_from_json(DATA_FILE)
        except ValueError as err:
            st.warning(f"Could not read {DATA_FILE.name} ({err}); starting fresh.")
owner: Owner = st.session_state.owner
scheduler = Scheduler(owner)


def save() -> None:
    """Write the current owner to data.json."""
    owner.save_to_json(DATA_FILE)


def task_rows(tasks: list[Task]) -> list[dict]:
    """Return table rows (one dict per task) for st.table."""
    return [
        {
            "date": t.due_date.isoformat(),
            "time": t.time,
            "pet": t.pet_name,
            "task": t.description,
            "minutes": t.duration_minutes,
            "priority": t.priority,
            "frequency": t.frequency,
            "status": "✅ Done" if t.completed else "⏳ Pending",
        }
        for t in tasks
    ]


st.title("🐾 PawPal+")

# One-shot message saved by "Mark complete" before its rerun.
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

name_col, budget_col = st.columns(2)
with name_col:
    # A blank name keeps the current one.
    new_name = st.text_input("Owner name", value=owner.name).strip() or owner.name
with budget_col:
    new_budget = int(
        st.number_input("Daily time budget (minutes)", min_value=1, max_value=1440, value=owner.available_minutes)
    )
if new_name != owner.name or new_budget != owner.available_minutes:
    owner.name = new_name
    owner.available_minutes = new_budget
    save()

st.divider()

st.subheader("Add a pet")
with st.form("add_pet_form", clear_on_submit=True):
    pet_name = st.text_input("Pet name")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Age", min_value=0, max_value=50, value=1)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Pet name is required.")
        else:
            try:
                owner.add_pet(Pet(name=pet_name.strip(), species=species, age=int(age)))
                save()
                st.success(f"Added {pet_name.strip()}.")
            except ValueError as err:
                st.error(str(err))

st.subheader("Add a task")
if not owner.pets:
    st.info("Add a pet first.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        chosen_pet = st.selectbox("Pet", [p.name for p in owner.pets])
        description = st.text_input("Task description", value="Morning walk")
        col1, col2 = st.columns(2)
        with col1:
            task_time = st.time_input("Time", value=None)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])
        due = st.date_input("Due date", value=date.today())
        if st.form_submit_button("Add task"):
            if not description.strip() or task_time is None:
                st.error("Description and time are required.")
            else:
                pet = owner.get_pet(chosen_pet)
                try:
                    pet.add_task(
                        Task(
                            description=description.strip(),
                            time=task_time.strftime("%H:%M"),
                            duration_minutes=int(duration),
                            priority=priority,
                            frequency=frequency,
                            due_date=due,
                        )
                    )
                    save()
                    st.success(f"Added task to {pet.name}.")
                except ValueError as err:
                    st.error(str(err))

st.divider()

# Placed above the task list so the table below reflects a completion on the same run.
st.subheader("Mark a task complete")
pending = scheduler.sort_by_time(scheduler.filter_tasks(completed=False))
if not pending:
    st.info("No pending tasks.")
else:
    labels = {t.task_id: f"{t.due_date.isoformat()} {t.time} - {t.pet_name}: {t.description}" for t in pending}
    chosen_id = st.selectbox("Pending task", list(labels), format_func=labels.get)
    if st.button("Mark complete"):
        next_task = scheduler.mark_task_complete(chosen_id)
        save()
        if next_task is not None:
            st.session_state["flash"] = (
                f"Completed. Next {next_task.frequency} occurrence of "
                f"'{next_task.description}' ({next_task.pet_name}) added for {next_task.due_date.isoformat()}."
            )
        else:
            st.session_state["flash"] = "Completed. No next occurrence (one-time task)."
        st.rerun()  # rebuild the dropdown; the message is shown at the top of the next run

st.subheader("Task list")
if not owner.get_all_tasks():
    st.info("No tasks yet.")
else:
    filter_pet_col, filter_status_col = st.columns(2)
    with filter_pet_col:
        pet_filter = st.selectbox("Pet", ["All"] + [p.name for p in owner.pets], key="filter_pet")
    with filter_status_col:
        status_filter = st.selectbox("Status", ["All", "Pending", "Done"], key="filter_status")
    visible = scheduler.sort_by_time(
        scheduler.filter_tasks(
            pet_name=None if pet_filter == "All" else pet_filter,
            completed={"All": None, "Pending": False, "Done": True}[status_filter],
        )
    )
    if visible:
        st.table(task_rows(visible))
    else:
        st.info("No tasks match these filters.")

st.subheader("Find a free slot")
slot_minutes = int(st.number_input("Task duration (minutes)", min_value=1, max_value=240, value=30, key="slot_minutes"))
free_slot = scheduler.next_available_slot(slot_minutes, date.today())
if free_slot is not None:
    st.success(f"Next free slot today: {free_slot}")
else:
    st.warning("No free slot today for that duration.")

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule"):
    st.session_state["show_plan"] = True

# Recomputed every run while the flag is set, so the plan reflects new tasks and completions.
if st.session_state.get("show_plan"):
    planned, skipped = scheduler.build_daily_plan(date.today())

    conflicts = scheduler.detect_conflicts(planned)
    if conflicts:
        # Warnings are built from the pairs, so the two lists line up one to one.
        pairs = scheduler.find_conflict_pairs(planned)
        for warning, (_, later) in zip(conflicts, pairs):
            st.warning(warning)
            slot = scheduler.next_available_slot(later.duration_minutes, later.due_date)
            if slot is not None:
                st.info(f"💡 Suggestion: move '{later.description}' to {slot}.")
            else:
                st.info(f"💡 No free slot left for '{later.description}' that day.")
        st.warning("Consider moving one of these tasks")
    else:
        st.success("No conflicts")

    if planned:
        st.table(task_rows(scheduler.sort_by_time(planned)))
    else:
        st.info("No tasks planned for today.")

    if skipped:
        st.subheader("Skipped tasks")
        st.caption("These did not fit the remaining time budget.")
        st.table(task_rows(skipped))

    with st.expander("Why this plan?"):
        for line in scheduler.explain_plan(planned, skipped):
            st.write(line)
