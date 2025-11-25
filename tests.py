from django.test import TestCase
from .scoring import analyze_tasks


class ScoringTests(TestCase):
    def test_urgent_task_scores_higher(self):
        tasks = [
            {
                "id": 1,
                "title": "Due sooner",
                "due_date": "2099-01-01",
                "estimated_hours": 2,
                "importance": 5,
                "dependencies": [],
            },
            {
                "id": 2,
                "title": "Due later",
                "due_date": "2099-02-01",
                "estimated_hours": 2,
                "importance": 5,
                "dependencies": [],
            },
        ]
        scored = analyze_tasks(tasks, strategy="deadline_driven")
        self.assertEqual(scored[0]["title"], "Due sooner")

    def test_high_importance_scores_higher(self):
        tasks = [
            {
                "id": 1,
                "title": "Low importance",
                "due_date": None,
                "estimated_hours": 2,
                "importance": 3,
                "dependencies": [],
            },
            {
                "id": 2,
                "title": "High importance",
                "due_date": None,
                "estimated_hours": 2,
                "importance": 9,
                "dependencies": [],
            },
        ]
        scored = analyze_tasks(tasks, strategy="high_impact")
        self.assertEqual(scored[0]["title"], "High importance")

    def test_dependency_task_scores_higher(self):
        tasks = [
            {
                "id": 1,
                "title": "Base task",
                "due_date": None,
                "estimated_hours": 2,
                "importance": 5,
                "dependencies": [],
            },
            {
                "id": 2,
                "title": "Depends on base",
                "due_date": None,
                "estimated_hours": 2,
                "importance": 5,
                "dependencies": [1],
            },
        ]
        scored = analyze_tasks(tasks, strategy="smart_balance")
        self.assertEqual(scored[0]["title"], "Base task")
