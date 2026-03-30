from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str
    age: int


@dataclass
class Owner:
    name: str
    available_minutes: int


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "high", "medium", or "low"


class Plan:
    def __init__(self, scheduled_tasks: list, skipped_tasks: list, explanation: str):
        self.scheduled_tasks = scheduled_tasks
        self.skipped_tasks = skipped_tasks
        self.explanation = explanation

    def summary(self) -> str:
        pass


class Scheduler:
    def __init__(self, owner: Owner, pets: list, tasks: list):
        self.owner = owner
        self.pets = pets
        self.tasks = tasks

    def generate_plan(self) -> Plan:
        pass
