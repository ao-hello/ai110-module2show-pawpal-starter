import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Owner & Pet setup ────────────────────────────────────────────────────────

with st.expander("Owner & Pet Setup", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        owner_name = st.text_input("Owner name", value="Jordan")
        available_minutes = st.number_input(
            "Available minutes today", min_value=10, max_value=480, value=120
        )
    with col2:
        pet_name = st.text_input("Pet name", value="Mochi")
        species = st.selectbox("Species", ["dog", "cat", "other"])

    if st.button("Create / Reset Owner & Pet"):
        pet = Pet(name=pet_name, species=species, age=0)
        st.session_state.owner = Owner(
            name=owner_name, pets=[pet], available_minutes=int(available_minutes)
        )
        st.session_state.pop("tasks", None)
        st.success(f"Owner '{owner_name}' and pet '{pet_name}' created.")

    if "owner" not in st.session_state:
        pet = Pet(name=pet_name, species=species, age=0)
        st.session_state.owner = Owner(
            name=owner_name, pets=[pet], available_minutes=int(available_minutes)
        )

# ── Add tasks ────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Add a Task")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["high", "medium", "low"])
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])

if st.button("Add task"):
    new_task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        frequency=frequency,
    )
    st.session_state.owner.pets[0].add_task(new_task)
    st.success(f"Added '{task_title}'")

# ── Recurring task reset ──────────────────────────────────────────────────────

if st.button("Reset daily recurring tasks (new day)"):
    for pet in st.session_state.owner.pets:
        pet.reset_recurring_tasks()
    st.success("All completed daily tasks have been reset.")

# ── Filter tasks ──────────────────────────────────────────────────────────────

st.divider()
st.subheader("Filter Tasks")

scheduler = Scheduler(owner=st.session_state.owner)

with st.expander("Filter options"):
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        filter_pet = st.text_input("By pet name (blank = all)", value="")
    with f_col2:
        filter_priority = st.selectbox("By priority", ["(any)", "high", "medium", "low"])
    with f_col3:
        filter_frequency = st.selectbox(
            "By frequency", ["(any)", "daily", "weekly", "as-needed"]
        )
    with f_col4:
        filter_status = st.selectbox(
            "By status", ["(any)", "pending only", "completed only"]
        )

    filtered = scheduler.filter_tasks(
        pet_name=filter_pet.strip() or None,
        priority=None if filter_priority == "(any)" else filter_priority,
        frequency=None if filter_frequency == "(any)" else filter_frequency,
        completed=(
            None
            if filter_status == "(any)"
            else filter_status == "completed only"
        ),
    )

    if filtered:
        st.write(f"**{len(filtered)} task(s) match your filter:**")
        st.table(
            [
                {
                    "title": t.title,
                    "duration (min)": t.duration_minutes,
                    "priority": t.priority,
                    "frequency": t.frequency,
                    "completed": t.completed,
                }
                for t in filtered
            ]
        )
    else:
        all_tasks = st.session_state.owner.get_all_tasks()
        if all_tasks:
            st.info("No tasks match the current filter.")
        else:
            st.info("No tasks yet — add one above.")

# ── Pending task table ────────────────────────────────────────────────────────

st.divider()
st.subheader("All Pending Tasks")

pending = st.session_state.owner.pets[0].get_pending_tasks()
if pending:
    st.table(
        [
            {
                "title": t.title,
                "duration (min)": t.duration_minutes,
                "priority": t.priority,
                "frequency": t.frequency,
            }
            for t in pending
        ]
    )
else:
    st.info("No pending tasks.")

# ── Build schedule ────────────────────────────────────────────────────────────

st.divider()
st.subheader("Build Schedule")

day_start = st.text_input("Day start time (HH:MM)", value="08:00")

if st.button("Generate schedule"):
    try:
        datetime_check = __import__("datetime").datetime.strptime(day_start, "%H:%M")
    except ValueError:
        st.error("Please enter a valid time in HH:MM format (e.g. 08:00).")
        st.stop()

    plan = scheduler.generate_plan(day_start=day_start)

    # Conflicts
    if plan.conflicts:
        st.warning("**Conflicts detected:**")
        for c in plan.conflicts:
            st.write(f"- {c}")

    # Timed schedule table
    if plan.timed_schedule:
        st.success(f"Scheduled {len(plan.timed_schedule)} task(s):")
        st.table(
            [
                {
                    "start": start,
                    "title": task.title,
                    "duration (min)": task.duration_minutes,
                    "priority": task.priority,
                    "frequency": task.frequency,
                }
                for task, start in plan.timed_schedule
            ]
        )
    else:
        st.info("No tasks could be scheduled.")

    # Skipped tasks
    if plan.skipped_tasks:
        st.error(f"Skipped {len(plan.skipped_tasks)} task(s) (not enough time):")
        st.table(
            [
                {
                    "title": t.title,
                    "duration (min)": t.duration_minutes,
                    "priority": t.priority,
                }
                for t in plan.skipped_tasks
            ]
        )

    # Full text reasoning
    with st.expander("Full reasoning"):
        st.text(plan.summary())
