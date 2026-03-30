# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

Phase 3 added four algorithmic improvements to `pawpal_system.py`:

**Sort by time** — `Scheduler.sort_by_time(tasks)`
Tasks with a `scheduled_time` ("HH:MM") are sorted chronologically using a `datetime.strptime` lambda as the sort key. Tasks without a time sink to the bottom.

**Filter tasks** — `Scheduler.filter_tasks(...)`
A single-pass filter that accepts any combination of `pet_name`, `priority`, `frequency`, and `completed` status. Only tasks matching every supplied condition are returned.

**Recurring task automation** — `Scheduler.mark_task_complete(pet, task)`
Marking a task complete automatically creates the next occurrence using `timedelta`: daily tasks reappear tomorrow, weekly tasks reappear in seven days. Tasks with `frequency="as-needed"` do not recur.

**Conflict detection** — `Scheduler.detect_conflicts(tasks)`
Checks for four types of problems and returns warning strings (never crashes):
- Total task time exceeds available time
- Duplicate task titles
- High-priority task that can never fit in available time
- Time-slot overlaps between any two tasks (interval overlap formula: `A_start < B_end AND B_start < A_end`)

## Getting started

### Setup

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
