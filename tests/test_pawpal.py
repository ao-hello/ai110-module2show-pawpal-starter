from pawpal_system import Task, Pet, Owner, Scheduler


def test_mark_complete_changes_status():
    task = Task(title="Morning walk", duration_minutes=30, priority="high")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="cat", age=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task(title="Brush fur", duration_minutes=10, priority="low"))
    assert len(pet.tasks) == 1


def test_sort_tasks_by_priority():
    scheduler = Scheduler(owner=Owner(name="Alex", pets=[], available_minutes=120))
    tasks = [
        Task(title="Bath", duration_minutes=20, priority="low"),
        Task(title="Meds", duration_minutes=10, priority="high"),
        Task(title="Walk", duration_minutes=15, priority="medium"),
    ]
    sorted_tasks = scheduler._sort_tasks(tasks)
    assert [t.priority for t in sorted_tasks] == ["high", "medium", "low"]


def test_daily_task_creates_next_occurrence():
    pet = Pet(name="Mochi", species="cat", age=3)
    task = Task(title="Feed", duration_minutes=5, priority="high",
                frequency="daily", due_date="2026-03-31")
    pet.add_task(task)

    owner = Owner(name="Alex", pets=[pet], available_minutes=60)
    scheduler = Scheduler(owner=owner)
    scheduler.mark_task_complete(pet, task)

    assert len(pet.tasks) == 2
    assert pet.tasks[1].due_date == "2026-04-01"
    assert pet.tasks[1].completed is False


def test_detect_time_slot_conflict():
    owner = Owner(name="Alex", pets=[], available_minutes=120)
    scheduler = Scheduler(owner=owner)
    tasks = [
        Task(title="Walk", duration_minutes=30, priority="high", scheduled_time="08:00"),
        Task(title="Feed", duration_minutes=30, priority="high", scheduled_time="08:15"),
    ]
    warnings = scheduler.detect_conflicts(tasks)
    assert any("conflict" in w.lower() or "overlaps" in w.lower() for w in warnings)
