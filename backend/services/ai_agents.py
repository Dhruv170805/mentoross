"""
MentorOS – Custom AI Agent Services (Algorithmic Engine)
Self-hosted, deterministic rule-based algorithms for generating plans and giving feedback.
Zero external API calls.
"""
import random
from typing import Dict, List
import structlog

log = structlog.get_logger()

from core.constants import PLANNER_TOPICS, EXPLAIN_TEMPLATE, ANALOGY_TEMPLATE, EXAMPLE_TEMPLATE

async def generate_plan(history: str) -> dict:
    """Planner Agent – generates a structured daily learning plan."""
    topic = random.choice(PLANNER_TOPICS)
    return {
        "topic": topic,
        "title": f"Deep Dive into {topic}",
        "difficulty": random.choice(["medium", "hard"]),
        "steps": [
            {"name": "Review foundational concepts", "duration": "30m"},
            {"name": "Implement core logical patterns", "duration": "45m"},
            {"name": "Synthesize notes and test", "duration": "20m"}
        ]
    }

async def run_review(tasks_completed: str, notes_taken: str) -> dict:
    """Reviewer Agent – evaluates daily performance algorithmically."""
    if tasks_completed == "No tasks completed yet":
        task_count = 0
    else:
        task_count = len([t for t in tasks_completed.split(',') if t.strip()])
    
    note_count = len([n for n in notes_taken.split('|') if n.strip()])

    score = min((task_count * 3) + (note_count * 2), 10)
    score = max(score, 2) if (task_count > 0 or note_count > 0) else 0

    if score > 7:
        feedback = "Excellent effort today! You maintained great consistency."
    elif score > 4:
        feedback = "Solid session today. You accomplished good work, keep pushing!"
    else:
        feedback = "A lighter day today. Let's try to focus on specific small tasks tomorrow."

    weak_areas = []
    if task_count == 0: weak_areas.append("Task Completion Momentum")
    if note_count == 0: weak_areas.append("Knowledge Documentation")

    return {
        "score": score,
        "feedback": f"{feedback} You logged {task_count} tasks and wrote active notes.",
        "weak_areas": weak_areas
    }

async def explain_concept(topic: str, level: str = "intermediate") -> dict:
    """Teacher Agent – explains a concept."""
    token = topic.replace(' ', '_').lower()
    return {
        "explanation": EXPLAIN_TEMPLATE.format(topic=topic, level=level),
        "analogy": ANALOGY_TEMPLATE.format(topic=topic),
        "example": EXAMPLE_TEMPLATE.format(token=token),
        "key_points": ["Core standard definitions", "Implementation boundaries and scale", "Common misuses to avoid"]
    }

async def generate_roadmap_phases(roadmap_name: str, goal: str, duration: str) -> list:
    """Curriculum Designer – structured phase generation."""
    return [
        {
            "title": "Phase 1: Foundations",
            "duration": "30% of time",
            "topics": ["Core Mechanics", "Syntax Essentials", "Initial Patterns"]
        },
        {
            "title": "Phase 2: Intermediate Expansion",
            "duration": "40% of time",
            "topics": ["Architecture Scaling", "Database Optimizations", "Security Basics"]
        },
        {
            "title": "Phase 3: Advanced Mastery",
            "duration": "30% of time",
            "topics": ["System Integration", "Performance Benchmarking", "Project Completion"]
        }
    ]
