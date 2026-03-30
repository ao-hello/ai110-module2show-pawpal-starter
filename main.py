from pawpal_system import Task, Pet, Owner, Scheduler

# --- Pets ---
mochi = Pet(name="Mochi", species="cat", age=3)
ranger = Pet(name="Ranger", species="dog", age=5)

# --- Tasks for Mochi ---
mochi.add_task(Task(
    title="Brush fur",
    duration_minutes=10,
    priority="low",
    description="Brush Mochi's coat to reduce shedding.",
    frequency="weekly",
))
mochi.add_task(Task(
    title="Refill water fountain",
    duration_minutes=5,
    priority="high",
    description="Clean and refill Mochi's water fountain.",
    frequency="daily",
))

# --- Tasks for Ranger ---
ranger.add_task(Task(
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    description="30-minute walk around the block.",
    frequency="daily",
))
ranger.add_task(Task(
    title="Administer flea medication",
    duration_minutes=5,
    priority="medium",
    description="Apply monthly flea and tick treatment.",
    frequency="monthly",
))
ranger.add_task(Task(
    title="Play fetch",
    duration_minutes=20,
    priority="low",
    description="Backyard fetch session for exercise and enrichment.",
    frequency="daily",
))

# --- Owner ---
jordan = Owner(name="Jordan", pets=[mochi, ranger], available_minutes=60)

# --- Schedule ---
scheduler = Scheduler(owner=jordan)
plan = scheduler.generate_plan()

print(plan.summary())
