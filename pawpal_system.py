from dataclasses import dataclass, field

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "high", "medium", or "low"
    description: str = ""
    frequency: str = "daily"  # e.g. "daily", "weekly", "as-needed"
    completed: bool = False

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True


@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task):
        """Attach a Task to this pet's task list."""
        self.tasks.append(task)

    def get_pending_tasks(self) -> list:
        """Return tasks that have not been marked complete."""
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    name: str
    pets: list  # list of Pet objects this owner is responsible for
    available_minutes: int

    def add_pet(self, pet: Pet):
        """Add a Pet to this owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list:
        """Return every task across all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.tasks)
        return all_tasks

    def get_pending_tasks(self) -> list:
        """Return all incomplete tasks across all pets."""
        pending = []
        for pet in self.pets:
            pending.extend(pet.get_pending_tasks())
        return pending


class Plan:
    def __init__(self, scheduled_tasks: list, skipped_tasks: list, explanation: str):
        """Store the results of a scheduling run."""
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.explanation = explanation

    def summary(self) -> str:
        """Return a formatted string showing scheduled and skipped tasks with reasoning."""
        lines = ["=== Today's PawPal+ Schedule ===\n"]

        if self.scheduled_tasks:
            lines.append("Scheduled tasks:")
            for task in self.scheduled_tasks:
                lines.append(f"  - {task.title} ({task.duration_minutes} min) [{task.priority} priority]")
        else:
            lines.append("No tasks scheduled.")

        if self.skipped_tasks:
            lines.append("\nSkipped tasks:")
            for task in self.skipped_tasks:
                lines.append(f"  - {task.title} ({task.duration_minutes} min) [{task.priority} priority]")

        lines.append(f"\nReasoning:\n{self.explanation}")
        return "\n".join(lines)


class Scheduler:
    """Retrieves pending tasks from the owner's pets and builds a daily plan."""

    def __init__(self, owner: Owner):
        """Initialize the scheduler with an Owner whose pets' tasks will be planned."""
        self.owner = owner

    def generate_plan(self) -> Plan:
        """Sort pending tasks by priority and greedily schedule them within available time."""
        # Pull tasks directly from the owner → pets chain
        pending = self.owner.get_pending_tasks()
        sorted_tasks = sorted(pending, key=lambda t: PRIORITY_ORDER.get(t.priority, 99))

        scheduled = []
        skipped = []
        time_remaining = self.owner.available_minutes

        for task in sorted_tasks:
            if task.duration_minutes <= time_remaining:
                scheduled.append(task)
                time_remaining -= task.duration_minutes
            else:
                skipped.append(task)

        explanation = self._build_explanation(scheduled, skipped, time_remaining)
        return Plan(scheduled, skipped, explanation)

    def _build_explanation(self, scheduled: list, skipped: list, time_remaining: int) -> str:
        """Build a human-readable explanation of why each task was included or skipped."""
        lines = []

        lines.append(
            f"{self.owner.name} has {self.owner.available_minutes} minute(s) available today. "
            f"Tasks were sorted by priority (high → medium → low) and scheduled greedily until time ran out."
        )

        if scheduled:
            lines.append("\nIncluded:")
            for task in scheduled:
                lines.append(f"  - '{task.title}' was scheduled ({task.priority} priority, {task.duration_minutes} min).")

        if skipped:
            lines.append("\nSkipped:")
            for task in skipped:
                lines.append(
                    f"  - '{task.title}' was skipped ({task.priority} priority, {task.duration_minutes} min) "
                    f"— not enough time remaining."
                )

        lines.append(f"\n{time_remaining} minute(s) left unused after scheduling.")
        return "\n".join(lines)
