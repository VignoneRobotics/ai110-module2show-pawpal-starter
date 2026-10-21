from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Create the single Owner once; later reruns reuse the stored object.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan")
owner: Owner = st.session_state.owner

st.title("🐾 PawPal+")

owner.available_minutes = int(
    st.number_input("Daily time budget (minutes)", min_value=1, max_value=1440, value=owner.available_minutes)
)

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
                    st.success(f"Added task to {pet.name}.")
                except ValueError as err:
                    st.error(str(err))

all_tasks = owner.get_all_tasks()
if all_tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "pet": t.pet_name,
                "task": t.description,
                "time": t.time,
                "duration_minutes": t.duration_minutes,
                "priority": t.priority,
                "frequency": t.frequency,
                "due": t.due_date.isoformat(),
            }
            for t in all_tasks
        ]
    )

st.divider()

st.subheader("Build Schedule")
if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    planned, skipped = scheduler.build_daily_plan(date.today())
    for line in scheduler.explain_plan(planned, skipped):
        st.write(line)
