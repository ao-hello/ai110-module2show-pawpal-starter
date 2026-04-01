import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

PRIORITY_ICON = {"high": "🔴", "medium": "🟡", "low": "🟢"}


def _priority_label(p: str) -> str:
    return f"{PRIORITY_ICON.get(p, '')} {p}"


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

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["high", "medium", "low"])
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
with col5:
    scheduled_time = st.text_input("Preferred time (HH:MM)", value="", placeholder="e.g. 08:00")

if st.button("Add task"):
    # Validate optional scheduled_time
    import datetime as _dt
    parsed_time = ""
    if scheduled_time.strip():
        try:
            _dt.datetime.strptime(scheduled_time.strip(), "%H:%M")
            parsed_time = scheduled_time.strip()
        except ValueError:
            st.error("Preferred time must be in HH:MM format (e.g. 08:00). Task not added.")
            st.stop()

    new_task = Task(
        title=task_title,
        duration_minutes=int(duration),
        priority=priority,
        frequency=frequency,
        scheduled_time=parsed_time,
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
        # Sort filtered results: tasks with a preferred time by time, rest by priority
        timed = scheduler.sort_by_time([t for t in filtered if t.scheduled_time])
        untimed = scheduler._sort_tasks([t for t in filtered if not t.scheduled_time])
        display_order = timed + untimed

        st.write(f"**{len(display_order)} task(s) match your filter** (sorted by preferred time, then priority):")
        st.table(
            [
                {
                    "priority": _priority_label(t.priority),
                    "title": t.title,
                    "duration (min)": t.duration_minutes,
                    "frequency": t.frequency,
                    "preferred time": t.scheduled_time or "—",
                    "completed": "✅" if t.completed else "⬜",
                }
                for t in display_order
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
st.caption("Sorted by priority (high → medium → low), then by duration within each priority.")

# Use Scheduler's sort so the display matches the scheduling logic
pending = scheduler._sort_tasks(st.session_state.owner.pets[0].get_pending_tasks())
if pending:
    total_pending_min = sum(t.duration_minutes for t in pending)
    avail = st.session_state.owner.available_minutes
    col_a, col_b = st.columns(2)
    col_a.metric("Pending tasks", len(pending))
    col_b.metric(
        "Total time needed",
        f"{total_pending_min} min",
        delta=f"{avail - total_pending_min} min slack" if total_pending_min <= avail else f"{total_pending_min - avail} min over budget",
        delta_color="normal" if total_pending_min <= avail else "inverse",
    )
    st.table(
        [
            {
                "priority": _priority_label(t.priority),
                "title": t.title,
                "duration (min)": t.duration_minutes,
                "frequency": t.frequency,
                "preferred time": t.scheduled_time or "—",
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
        import datetime as _dt2
        _dt2.datetime.strptime(day_start, "%H:%M")
    except ValueError:
        st.error("Please enter a valid time in HH:MM format (e.g. 08:00).")
        st.stop()

    plan = scheduler.generate_plan(day_start=day_start)

    # ── Conflict warnings ────────────────────────────────────────────────────
    # Each conflict type gets its own styled callout with an actionable tip so
    # a pet owner knows exactly what to do — not just that something is wrong.
    if plan.conflicts:
        st.subheader("⚠️ Conflicts Detected")
        for c in plan.conflicts:
            if "always be skipped" in c:
                # A high-priority task that can never fit — most urgent problem
                st.error(
                    f"🚨 **Critical — task will always be skipped:** {c}\n\n"
                    "_What to do: Either shorten this task or increase your available minutes for today._"
                )
            elif "Time-slot conflict" in c:
                # Two tasks with overlapping preferred times
                st.warning(
                    f"🕐 **Time-slot overlap:** {c}\n\n"
                    "_What to do: Edit the preferred time of one of these tasks so they don't overlap._"
                )
            elif "Duplicate task" in c:
                # Same task title added twice — likely a data-entry mistake
                st.warning(
                    f"📋 **Duplicate task:** {c}\n\n"
                    "_What to do: Check your task list and remove the extra copy._"
                )
            else:
                # Total time exceeds available minutes — some tasks will be skipped
                st.warning(
                    f"⏱️ **Over budget:** {c}\n\n"
                    "_What to do: Remove lower-priority tasks, shorten task durations, "
                    "or increase your available minutes. High-priority tasks are protected._"
                )

    # ── Timed schedule table ─────────────────────────────────────────────────
    if plan.timed_schedule:
        st.success(f"✅ Scheduled {len(plan.timed_schedule)} task(s) for today:")
        st.table(
            [
                {
                    "start": start,
                    "priority": _priority_label(task.priority),
                    "title": task.title,
                    "duration (min)": task.duration_minutes,
                    "frequency": task.frequency,
                }
                for task, start in plan.timed_schedule
            ]
        )
    else:
        st.info("No tasks could be scheduled.")

    # ── Skipped tasks ────────────────────────────────────────────────────────
    if plan.skipped_tasks:
        st.error(
            f"⏭️ {len(plan.skipped_tasks)} task(s) skipped — not enough time remaining:"
        )
        st.table(
            [
                {
                    "priority": _priority_label(t.priority),
                    "title": t.title,
                    "duration (min)": t.duration_minutes,
                }
                for t in plan.skipped_tasks
            ]
        )

    # ── Full text reasoning ──────────────────────────────────────────────────
    with st.expander("Full reasoning"):
        st.text(plan.summary())
