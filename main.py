from pawpal_system import Task, Pet, Owner, Scheduler

# ── Pets ─────────────────────────────────────────────────────────────────────

mochi = Pet(name="Mochi", species="cat", age=3)
ranger = Pet(name="Ranger", species="dog", age=5)

# ── Tasks added INTENTIONALLY out of time order ───────────────────────────────
# Mochi's tasks
mochi.add_task(Task(
    title="Refill water fountain",
    duration_minutes=5,
    priority="high",
    frequency="daily",
    scheduled_time="14:00",   # afternoon
))
mochi.add_task(Task(
    title="Brush fur",
    duration_minutes=10,
    priority="low",
    frequency="weekly",
    scheduled_time="09:00",   # morning — added after the afternoon task
))

# Ranger's tasks
ranger.add_task(Task(
    title="Evening walk",
    duration_minutes=30,
    priority="high",
    frequency="daily",
    scheduled_time="18:30",   # evening — added first
))
ranger.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    frequency="daily",
    scheduled_time="07:00",   # morning — added after evening task
))
ranger.add_task(Task(
    title="Administer flea medication",
    duration_minutes=5,
    priority="medium",
    frequency="weekly",
    scheduled_time="08:00",
))
ranger.add_task(Task(
    title="Play fetch",
    duration_minutes=20,
    priority="low",
    frequency="daily",
    scheduled_time="16:00",
))
ranger.add_task(Task(
    title="Midday snack",
    duration_minutes=5,
    priority="low",
    frequency="daily",
    scheduled_time="12:00",
))

# ── Owner ─────────────────────────────────────────────────────────────────────

jordan = Owner(name="Jordan", pets=[mochi, ranger], available_minutes=90)
scheduler = Scheduler(owner=jordan)

# ── Demo 1: sort_by_time() ────────────────────────────────────────────────────

print("=" * 50)
print("DEMO 1 — All tasks sorted by scheduled time")
print("=" * 50)

all_tasks = jordan.get_all_tasks()
sorted_by_time = scheduler.sort_by_time(all_tasks)

for task in sorted_by_time:
    time_label = task.scheduled_time if task.scheduled_time else "no time set"
    print(f"  {time_label}  |  {task.title:<30}  [{task.priority}]")

# ── Demo 2: filter_tasks() ────────────────────────────────────────────────────

print()
print("=" * 50)
print("DEMO 2 — Filter: Ranger's tasks only")
print("=" * 50)

ranger_tasks = scheduler.filter_tasks(pet_name="Ranger")
for task in scheduler.sort_by_time(ranger_tasks):
    print(f"  {task.scheduled_time}  |  {task.title:<30}  [{task.priority}]")

print()
print("=" * 50)
print("DEMO 3 — Filter: high-priority tasks only (all pets)")
print("=" * 50)

high_priority = scheduler.filter_tasks(priority="high")
for task in scheduler.sort_by_time(high_priority):
    print(f"  {task.scheduled_time}  |  {task.title:<30}  [{task.priority}]")

print()
print("=" * 50)
print("DEMO 4 — Filter: daily tasks only")
print("=" * 50)

daily_tasks = scheduler.filter_tasks(frequency="daily")
for task in scheduler.sort_by_time(daily_tasks):
    print(f"  {task.scheduled_time}  |  {task.title:<30}  [{task.frequency}]")

# ── Demo 5: conflict detection + schedule ────────────────────────────────────

print()
print("=" * 50)
print("DEMO 5 — Conflict detection + full schedule")
print("=" * 50)

plan = scheduler.generate_plan(day_start="07:00")
print(plan.summary())

# ── Demo 6: recurring task reset ─────────────────────────────────────────────

print()
print("=" * 50)
print("DEMO 6 — Recurring task reset")
print("=" * 50)

# Mark all tasks complete to simulate end-of-day
for task in jordan.get_all_tasks():
    task.mark_complete()

print("After marking all tasks complete:")
print(f"  Pending tasks: {len(jordan.get_pending_tasks())}")

# Reset only daily tasks
for pet in jordan.pets:
    pet.reset_recurring_tasks()

print("After reset_recurring_tasks() (daily tasks only):")
pending_after = jordan.get_pending_tasks()
print(f"  Pending tasks: {len(pending_after)}")
for task in pending_after:
    print(f"    - {task.title} ({task.frequency})")

# ── Demo 7: recurring task automation via mark_task_complete() ────────────────

print()
print("=" * 50)
print("DEMO 7 — Recurring task automation (mark_task_complete)")
print("=" * 50)

# Fresh setup so results are predictable
rex = Pet(name="Rex", species="dog", age=2)
rex.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    frequency="daily",
    scheduled_time="07:00",
    due_date="2026-03-30",   # today
))
rex.add_task(Task(
    title="Flea treatment",
    duration_minutes=5,
    priority="medium",
    frequency="weekly",
    scheduled_time="09:00",
    due_date="2026-03-30",
))
rex.add_task(Task(
    title="Vet visit",
    duration_minutes=60,
    priority="high",
    frequency="as-needed",
    scheduled_time="10:00",
    due_date="2026-03-30",
))

sam = Owner(name="Sam", pets=[rex], available_minutes=120)
s = Scheduler(owner=sam)

print("Tasks before completing anything:")
for t in rex.tasks:
    print(f"  {t.due_date}  {t.title:<25} [{t.frequency}]  completed={t.completed}")

# Complete the daily morning walk — should spawn tomorrow's instance
walk = rex.tasks[0]
next_walk = s.mark_task_complete(rex, walk)
print(f"\nCompleted '{walk.title}' (due {walk.due_date})")
print(f"  → Next occurrence auto-created: due {next_walk.due_date}")
#   timedelta(days=1): 2026-03-30 + 1 day = 2026-03-31

# Complete the weekly flea treatment — should spawn next week's instance
flea = rex.tasks[1]
next_flea = s.mark_task_complete(rex, flea)
print(f"\nCompleted '{flea.title}' (due {flea.due_date})")
print(f"  → Next occurrence auto-created: due {next_flea.due_date}")
#   timedelta(weeks=1): 2026-03-30 + 7 days = 2026-04-06

# Complete the as-needed vet visit — no new instance should be created
vet = rex.tasks[2]
result = s.mark_task_complete(rex, vet)
print(f"\nCompleted '{vet.title}' (frequency='as-needed')")
print(f"  → Next occurrence created: {result}")  # should print None

print("\nAll tasks after automation (including newly created ones):")
for t in rex.tasks:
    status = "done" if t.completed else "pending"
    print(f"  {t.due_date}  {t.title:<25} [{t.frequency}]  {status}")

# ── Demo 8: time-slot conflict detection ──────────────────────────────────────

print()
print("=" * 50)
print("DEMO 8 — Time-slot conflict detection")
print("=" * 50)

# Two pets, tasks that intentionally overlap in time
luna = Pet(name="Luna", species="cat", age=1)
luna.add_task(Task(
    title="Breakfast feeding",
    duration_minutes=10,
    priority="high",
    frequency="daily",
    scheduled_time="08:00",   # 08:00–08:10
))
luna.add_task(Task(
    title="Give hairball medication",
    duration_minutes=5,
    priority="high",
    frequency="daily",
    scheduled_time="08:05",   # 08:05–08:10  ← overlaps Breakfast feeding
))
luna.add_task(Task(
    title="Playtime",
    duration_minutes=20,
    priority="low",
    frequency="daily",
    scheduled_time="09:00",   # 09:00–09:20  ← no conflict
))

buddy = Pet(name="Buddy", species="dog", age=4)
buddy.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    frequency="daily",
    scheduled_time="08:00",   # 08:00–08:30  ← overlaps both Luna tasks above
))
buddy.add_task(Task(
    title="Training session",
    duration_minutes=15,
    priority="medium",
    frequency="daily",
    scheduled_time="10:00",   # 10:00–10:15  ← no conflict
))

alex = Owner(name="Alex", pets=[luna, buddy], available_minutes=120)
conflict_scheduler = Scheduler(owner=alex)

all_tasks = alex.get_all_tasks()
conflicts = conflict_scheduler.detect_conflicts(all_tasks)

print(f"Tasks scheduled:")
for t in conflict_scheduler.sort_by_time(all_tasks):
    end = __import__("datetime").datetime.strptime(t.scheduled_time, "%H:%M")
    end = end + __import__("datetime").timedelta(minutes=t.duration_minutes)
    print(f"  {t.scheduled_time}–{end.strftime('%H:%M')}  {t.title}")

print(f"\nConflicts found: {len(conflicts)}")
for w in conflicts:
    print(f"  WARNING: {w}")
