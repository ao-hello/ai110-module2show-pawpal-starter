# PawPal+ 🐾

**PawPal+** is a Streamlit app that helps busy pet owners plan their daily pet care. Enter your pet's tasks, set your available time, and PawPal+ builds a priority-sorted schedule — flagging conflicts before they become problems.

---

## 📸 Demo

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

## ✨ Features

### Priority-Based Scheduling
Tasks are sorted by priority (high → medium → low) and then by duration within each priority level (shorter tasks first). This greedy approach ensures the most urgent care items are always scheduled first, and the most tasks possible fit within available time.

### Sort by Preferred Time
Any task can be given a preferred start time (HH:MM). The filter view sorts tasks with a preferred time chronologically using `datetime.strptime`, and tasks without a preferred time appear at the bottom.

### Smart Filtering
Filter your task list by any combination of pet name, priority level, frequency, or completion status. All filters are applied in a single pass — only tasks matching every condition are shown.

### Conflict Detection
Before building the schedule, PawPal+ checks for four types of problems and displays an actionable warning for each:
- **Over budget** — total task time exceeds available minutes; lower-priority tasks will be skipped
- **Duplicate tasks** — same task title added more than once (likely a data entry mistake)
- **Unreachable high-priority task** — a high-priority task is longer than total available time and will always be skipped
- **Time-slot overlap** — two tasks with preferred times whose windows overlap (detected using the interval formula: `A_start < B_end AND B_start < A_end`)

### Daily Recurrence
Completing a recurring task automatically schedules its next occurrence. Daily tasks reappear tomorrow; weekly tasks reappear in seven days. Tasks marked `as-needed` do not recur.

### Timed Schedule View
After generating a plan, each scheduled task is shown with a wall-clock start time. Tasks run back-to-back starting from a configurable day-start time (default 08:00).

---

## 🚀 Getting Started

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

---

## 🧪 Testing

```bash
uv run pytest tests/test_pawpal.py -v
```

| Test | What it verifies |
|------|-----------------|
| `test_mark_complete_changes_status` | A task's `completed` flag flips to `True` after `mark_complete()` |
| `test_add_task_increases_pet_task_count` | Adding a task to a pet correctly grows the task list |
| `test_sort_tasks_by_priority` | Tasks are sorted high → medium → low priority |
| `test_daily_task_creates_next_occurrence` | Completing a daily task generates a new task dated +1 day |
| `test_detect_time_slot_conflict` | Overlapping scheduled times produce a conflict warning |

**Confidence level:** ⭐⭐⭐⭐✨ 4.5 / 5 — all 5 tests pass. Edge cases like zero available time and empty task lists are not yet covered.

---

## 🗂 Architecture

The system is built around five classes:

| Class | Responsibility |
|-------|---------------|
| `Task` | A single care item with title, duration, priority, frequency, and optional preferred time |
| `Pet` | Owns a list of tasks; handles pending/completed filtering and daily resets |
| `Owner` | Holds available minutes and a list of pets |
| `Scheduler` | Core logic — sorts, filters, detects conflicts, and generates the daily plan |
| `Plan` | Output object — scheduled tasks with start times, skipped tasks, conflicts, and a reasoning summary |

See `uml_final.png` for the full class diagram.
