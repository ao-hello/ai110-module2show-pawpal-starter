from dataclasses import dataclass, field
from datetime import datetime, timedelta

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "high", "medium", or "low"
    description: str = ""
    frequency: str = "daily"  # "daily", "weekly", "as-needed"
    scheduled_time: str = ""  # optional preferred start time in "HH:MM" format
    due_date: str = ""        # optional due date in "YYYY-MM-DD" format
    completed: bool = False

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def next_occurrence(self) -> "Task":
        """Return a new Task instance for the next scheduled occurrence.

        How timedelta is used:
          - timedelta(days=1)  advances the date by exactly one day (daily tasks).
          - timedelta(weeks=1) advances by exactly seven days (weekly tasks).
          - Python's date arithmetic handles month/year rollovers automatically,
            so e.g. 2024-01-31 + timedelta(days=1) correctly gives 2024-02-01.

        'as-needed' tasks have no fixed recurrence, so calling this on them
        raises ValueError to make the mistake explicit rather than silently
        returning a task with a wrong date.
        """
        if self.frequency == "as-needed":
            raise ValueError(
                f"Task '{self.title}' is 'as-needed' and has no next occurrence."
            )

        if self.due_date:
            base = datetime.strptime(self.due_date, "%Y-%m-%d")
        else:
            base = datetime.today()

        if self.frequency == "daily":
            next_date = base + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = base + timedelta(weeks=1)
        else:
            # Unknown frequency — default to +1 day so nothing breaks silently
            next_date = base + timedelta(days=1)

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            description=self.description,
            frequency=self.frequency,
            scheduled_time=self.scheduled_time,
            due_date=next_date.strftime("%Y-%m-%d"),
            completed=False,
        )


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

    def reset_recurring_tasks(self):
        """Re-activate completed recurring tasks (call at the start of each new day).

        Algorithm: linear scan — O(n) where n = number of tasks for this pet.
        Only resets tasks whose frequency is 'daily'; 'weekly' and 'as-needed'
        tasks are left untouched so they don't auto-regenerate every day.
        """
        for task in self.tasks:
            if task.frequency == "daily" and task.completed:
                task.completed = False


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
    def __init__(self, scheduled_tasks: list, skipped_tasks: list,
                 explanation: str, conflicts: list,
                 timed_schedule: list = None):
        """Store the results of a scheduling run.

        timed_schedule: list of (Task, start_time_str) tuples, e.g. [(<Task>, "08:00"), ...]
        conflicts: list of warning strings detected before scheduling
        """
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.explanation = explanation
        self.conflicts = conflicts
        self.timed_schedule = timed_schedule or []

    def summary(self) -> str:
        """Return a formatted string showing scheduled and skipped tasks with reasoning."""
        lines = ["=== Today's PawPal+ Schedule ===\n"]

        if self.conflicts:
            lines.append("⚠ Conflicts detected:")
            for warning in self.conflicts:
                lines.append(f"  ! {warning}")
            lines.append("")

        if self.timed_schedule:
            lines.append("Scheduled tasks (with start times):")
            for task, start_time in self.timed_schedule:
                lines.append(
                    f"  {start_time}  {task.title} "
                    f"({task.duration_minutes} min) [{task.priority} priority]"
                )
        elif self.scheduled_tasks:
            lines.append("Scheduled tasks:")
            for task in self.scheduled_tasks:
                lines.append(
                    f"  - {task.title} ({task.duration_minutes} min) [{task.priority} priority]"
                )
        else:
            lines.append("No tasks scheduled.")

        if self.skipped_tasks:
            lines.append("\nSkipped tasks:")
            for task in self.skipped_tasks:
                lines.append(
                    f"  - {task.title} ({task.duration_minutes} min) [{task.priority} priority]"
                )

        lines.append(f"\nReasoning:\n{self.explanation}")
        return "\n".join(lines)


class Scheduler:
    """Retrieves pending tasks from the owner's pets and builds a daily plan."""

    def __init__(self, owner: Owner):
        self.owner = owner

    # ------------------------------------------------------------------
    # Recurring task automation
    # ------------------------------------------------------------------
    def mark_task_complete(self, pet: Pet, task: Task) -> Task | None:
        """Mark a task complete and, if it recurs, add its next occurrence to the pet.

        Why this lives on Scheduler (not Task):
          Task.mark_complete() only flips a flag — it has no reference to the
          Pet that owns it, so it cannot append to pet.tasks.  Scheduler sits
          above both Pet and Task and can coordinate between them.

        How timedelta is used (inside Task.next_occurrence):
          - daily  → base_date + timedelta(days=1)
          - weekly → base_date + timedelta(weeks=1)
          timedelta handles all month/year rollovers automatically.

        Returns:
            The newly created Task if one was scheduled, or None for
            'as-needed' tasks (which don't recur automatically).
        """
        task.mark_complete()

        if task.frequency == "as-needed":
            return None

        next_task = task.next_occurrence()
        pet.add_task(next_task)
        return next_task

    # ------------------------------------------------------------------
    # Algorithm 1a: Sort tasks by scheduled_time (HH:MM string)
    # ------------------------------------------------------------------
    def sort_by_time(self, tasks: list) -> list:
        """Return tasks sorted by their scheduled_time in ascending order.

        How the lambda works:
          - datetime.strptime(t.scheduled_time, "%H:%M") parses the "HH:MM"
            string into a datetime object that Python can compare with < / >.
          - Tasks with no scheduled_time get sorted to the end via datetime.max.

        Complexity: O(n log n) — same Timsort as all Python sorts.

        Example:
            tasks with times ["14:00", "08:30", "11:00"]
            → sorted to   ["08:30", "11:00", "14:00"]
        """
        def time_key(task):
            if task.scheduled_time:
                return datetime.strptime(task.scheduled_time, "%H:%M")
            return datetime.max  # tasks without a time sink to the bottom

        return sorted(tasks, key=time_key)

    # ------------------------------------------------------------------
    # Algorithm 1b: Multi-key sort (priority + duration tie-break)
    # ------------------------------------------------------------------
    def _sort_tasks(self, tasks: list) -> list:
        """Sort tasks by priority first, then by duration (shorter tasks first).

        Using a two-key tuple keeps the sort stable and readable.
        Complexity: O(n log n) — Python's Timsort.

        Secondary sort by duration means that when two tasks share the same
        priority, the shorter one is scheduled first, maximising the number
        of tasks that fit in the available window (greedy packing).
        """
        return sorted(
            tasks,
            key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.duration_minutes),
        )

    # ------------------------------------------------------------------
    # Algorithm 2: Filter tasks
    # ------------------------------------------------------------------
    def filter_tasks(self, pet_name: str = None, priority: str = None,
                     frequency: str = None, completed: bool = None) -> list:
        """Return tasks matching all supplied filters (None = no filter on that field).

        Algorithm: single linear pass — O(n).
        Each keyword argument adds one condition to the filter chain; only
        tasks satisfying every supplied condition are returned.

        Args:
            pet_name:  only return tasks belonging to this pet
            priority:  "high" | "medium" | "low"
            frequency: "daily" | "weekly" | "as-needed"
            completed: True → only completed tasks; False → only pending
        """
        results = []
        for pet in self.owner.pets:
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.tasks:
                if priority and task.priority != priority:
                    continue
                if frequency and task.frequency != frequency:
                    continue
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results

    # ------------------------------------------------------------------
    # Algorithm 3: Conflict detection
    # ------------------------------------------------------------------
    def detect_conflicts(self, tasks: list) -> list:
        """Return a list of human-readable conflict warning strings.

        Checks performed (all O(n)):
        1. Total duration exceeds available time — would force skips.
        2. Duplicate task titles — likely a data entry mistake.
        3. High-priority tasks that alone exceed available time — will
           always be skipped even though they are urgent.
        """
        warnings = []

        total = sum(t.duration_minutes for t in tasks)
        if total > self.owner.available_minutes:
            over = total - self.owner.available_minutes
            warnings.append(
                f"Total task time ({total} min) exceeds available time "
                f"({self.owner.available_minutes} min) by {over} min — some tasks will be skipped."
            )

        seen_titles = set()
        for t in tasks:
            lower = t.title.lower()
            if lower in seen_titles:
                warnings.append(f"Duplicate task detected: '{t.title}'")
            seen_titles.add(lower)

        for t in tasks:
            if t.priority == "high" and t.duration_minutes > self.owner.available_minutes:
                warnings.append(
                    f"High-priority task '{t.title}' ({t.duration_minutes} min) "
                    f"exceeds total available time ({self.owner.available_minutes} min) "
                    f"and will always be skipped."
                )

        # Check 4: time-slot overlaps across all tasks with a scheduled_time.
        #
        # Strategy: for every pair of timed tasks, check whether their windows
        # overlap.  Two intervals [A_start, A_end) and [B_start, B_end) overlap
        # when A_start < B_end AND B_start < A_end.
        #
        # This is O(n²) over timed tasks — acceptable for a day's worth of pet
        # care tasks (typically < 20).  It returns a warning string instead of
        # raising an exception so the scheduler can continue and surface all
        # conflicts at once rather than stopping at the first one.
        timed = [t for t in tasks if t.scheduled_time]
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                a, b = timed[i], timed[j]
                a_start = datetime.strptime(a.scheduled_time, "%H:%M")
                a_end   = a_start + timedelta(minutes=a.duration_minutes)
                b_start = datetime.strptime(b.scheduled_time, "%H:%M")
                b_end   = b_start + timedelta(minutes=b.duration_minutes)

                if a_start < b_end and b_start < a_end:
                    warnings.append(
                        f"Time-slot conflict: '{a.title}' "
                        f"({a.scheduled_time}–{a_end.strftime('%H:%M')}) overlaps "
                        f"'{b.title}' "
                        f"({b.scheduled_time}–{b_end.strftime('%H:%M')})."
                    )

        return warnings

    # ------------------------------------------------------------------
    # Algorithm 4: Assign start times
    # ------------------------------------------------------------------
    def _assign_start_times(self, scheduled: list, day_start: str = "08:00") -> list:
        """Return list of (Task, start_time_str) tuples with wall-clock start times.

        Algorithm: sequential accumulation — O(n).
        Starting from day_start, each task's end time becomes the next
        task's start time.  No gaps or breaks are inserted (extend this
        later if you want a lunch-break slot, etc.).

        Args:
            scheduled:  ordered list of Task objects
            day_start:  "HH:MM" string for the first task's start time
        """
        current = datetime.strptime(day_start, "%H:%M")
        result = []
        for task in scheduled:
            result.append((task, current.strftime("%H:%M")))
            current += timedelta(minutes=task.duration_minutes)
        return result

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    def generate_plan(self, day_start: str = "08:00") -> Plan:
        """Sort, conflict-check, and greedily schedule tasks within available time."""
        pending = self.owner.get_pending_tasks()

        # Algorithm 1 — multi-key sort
        sorted_tasks = self._sort_tasks(pending)

        # Algorithm 3 — conflict detection (runs on full pending list)
        conflicts = self.detect_conflicts(sorted_tasks)

        scheduled = []
        skipped = []
        time_remaining = self.owner.available_minutes

        for task in sorted_tasks:
            if task.duration_minutes <= time_remaining:
                scheduled.append(task)
                time_remaining -= task.duration_minutes
            else:
                skipped.append(task)

        # Algorithm 4 — assign start times
        timed_schedule = self._assign_start_times(scheduled, day_start)

        explanation = self._build_explanation(scheduled, skipped, time_remaining)
        return Plan(scheduled, skipped, explanation, conflicts, timed_schedule)

    def _build_explanation(self, scheduled: list, skipped: list, time_remaining: int) -> str:
        """Build a human-readable explanation of why each task was included or skipped."""
        lines = [
            f"{self.owner.name} has {self.owner.available_minutes} minute(s) available today. "
            "Tasks were sorted by priority (high → medium → low), then by duration "
            "(shorter first within the same priority) and scheduled greedily until time ran out."
        ]

        if scheduled:
            lines.append("\nIncluded:")
            for task in scheduled:
                lines.append(
                    f"  - '{task.title}' was scheduled "
                    f"({task.priority} priority, {task.duration_minutes} min)."
                )

        if skipped:
            lines.append("\nSkipped:")
            for task in skipped:
                lines.append(
                    f"  - '{task.title}' was skipped ({task.priority} priority, "
                    f"{task.duration_minutes} min) — not enough time remaining."
                )

        lines.append(f"\n{time_remaining} minute(s) left unused after scheduling.")
        return "\n".join(lines)
