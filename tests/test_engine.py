import contextlib
import copy
from datetime import datetime
import io
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from codelingo.cli import App, LeaveSession, Terminal, main
from codelingo.course import Course, check_answer, load_course
from codelingo.store import Store
from codelingo.templates import render


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 9, 12).timestamp()

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.store = Store(":memory:", self.clock)
        self.course = load_course()
        self.app = App(self.course, self.store, Terminal(True), 1)

    def tearDown(self):
        self.store.close()

    def record(self, correct=True, mode="learn", qid="python:variables-1", combo=0):
        return self.store.record(qid, "answer", correct, mode, combo)

    def test_course_answers_and_validation(self):
        self.assertEqual(len(self.course.questions), 216)
        for template in self.course.questions.values():
            q = render(template, random.Random(0))
            if q["kind"] == "write":
                for answer in q["accepted"]:
                    self.assertTrue(check_answer(q, answer), q["id"])
            else:
                for answer in q["options"]:
                    self.assertEqual(check_answer(q, answer), answer == q["answer"])

    def test_bad_course_rejected(self):
        data = copy.deepcopy(self.course.data)
        data["lessons"][0]["requires"] = ["variables"]
        with self.assertRaises(ValueError):
            Course(data)
        data = copy.deepcopy(self.course.data)
        data["lessons"][0]["questions"][0]["answer"] = "unknown"
        with self.assertRaises(ValueError):
            Course(data)

    def test_writing_normalizes_syntax_without_running_code(self):
        q = self.course.questions["variables-5"]
        self.assertTrue(check_answer(q, " print( name ) "))
        self.assertFalse(check_answer(q, 'print("name")'))
        self.assertFalse(check_answer(q, 'print(name); open("owned", "w")'))
        self.assertFalse(check_answer(q, 'print('))
        self.assertFalse(check_answer(q, 'x' * 2001))
        q = self.course.questions["classes-5"]
        self.assertTrue(check_answer(q, "Job('test')"))

    def test_mistake_review_intervals_and_lapse(self):
        key = "python:variables-1"
        self.record(False)
        self.assertEqual(self.store.due({key}), [])
        self.clock.advance(600)
        self.assertEqual(self.store.due({key}), [key])
        for days in (1, 3, 7, 14, 30, 30):
            self.record(True, "review")
            due = self.store.db.execute("SELECT due FROM reviews").fetchone()[0]
            self.assertEqual(due, self.clock() + days * 86400)
            self.clock.advance(days * 86400)
        self.record(False, "review")
        row = self.store.db.execute("SELECT * FROM reviews").fetchone()
        self.assertEqual(row["stage"], 0)
        self.assertEqual(row["due"], self.clock() + 600)

    def test_early_review_does_not_postpone_due(self):
        self.record(False)
        due = self.store.db.execute("SELECT due FROM reviews").fetchone()[0]
        self.clock.advance(100)
        self.record(True, "review")
        self.assertEqual(self.store.db.execute("SELECT due FROM reviews").fetchone()[0], due)
        self.assertEqual(self.store.player()["hearts"], 5)

    def test_learning_correction_keeps_review(self):
        self.record(False)
        self.record(True)
        self.assertTrue(self.store.passed("python:variables-1"))
        self.assertEqual(len(self.store.due({"python:variables-1"}, early=True)), 1)

    def test_zero_hearts_and_recovery(self):
        for _ in range(5):
            self.record(False)
        self.assertEqual(self.store.player()["hearts"], 0)
        with self.assertRaisesRegex(ValueError, "No hearts"):
            self.record(True)
        self.record(False, "review")
        self.assertEqual(self.store.player()["hearts"], 0)
        self.record(True, "review")
        self.assertEqual(self.store.player()["hearts"], 1)
        self.assertFalse(self.store.passed("python:variables-1"))

    def test_heart_refill_preserves_fractional_time(self):
        for _ in range(3):
            self.record(False)
        self.clock.advance(1801)
        self.assertEqual(self.store.player()["hearts"], 3)
        self.clock.advance(1799)
        self.assertEqual(self.store.player()["hearts"], 4)
        self.clock.advance(100000)
        self.assertEqual(self.store.player()["hearts"], 5)
        self.record(False)
        self.assertEqual(self.store.player()["hearts"], 4)

    def test_credit_combo_and_no_double_xp(self):
        combo = 0
        for i in range(3):
            result = self.record(qid=f"q{i}", combo=combo)
            combo = result["combo"]
        self.assertEqual(result["xp"], 15)
        self.assertEqual(self.store.player()["xp"], 35)
        self.assertEqual(self.record(qid="q2")["xp"], 0)
        self.assertEqual(self.record(False, combo=3)["combo"], 0)

    def test_daily_goal_and_streak_expiry(self):
        for i in range(5):
            self.record(qid=f"q{i}")
        self.assertEqual(self.store.stats()["daily"], 0)
        self.store.complete('lesson-day1', [f'q{i}' for i in range(5)])
        self.assertEqual(self.store.stats()["streak"], 1)
        self.clock.advance(86400)
        self.assertEqual(self.store.stats()["daily"], 0)
        self.assertEqual(self.store.stats()["streak"], 1)
        for i in range(5):
            self.record(qid=f"q{i}")
        self.store.complete('lesson-day2', [f'q{i}' for i in range(5)])
        self.assertEqual(self.store.stats()["streak"], 2)
        self.clock.advance(2 * 86400)
        self.assertEqual(self.store.stats()["streak"], 0)

    def test_practice_cannot_unlock_lessons(self):
        lesson = self.course.lessons[0]
        for q in lesson["questions"]:
            self.record(True, "practice", self.course.key(q["id"]))
        self.assertFalse(self.store.complete("python:variables", [self.course.key(q["id"]) for q in lesson["questions"]]))
        self.assertFalse(self.app.unlocked(self.course.lessons[1]))

    def test_invalid_choice_and_hint_do_not_cost_hearts(self):
        self.app.rng.shuffle = lambda values: None
        with patch("builtins.input", side_effect=["?", "wrong", "0", "", "A"]), contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(self.app.ask(self.course.lessons[0]["questions"][0], "learn"))
        self.assertEqual(self.store.player()["hearts"], 5)
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0], 1)

    def test_exit_resume_and_reading_before_writing(self):
        self.app.rng.shuffle = lambda values: None
        with patch("builtins.input", side_effect=["B"] + ["A"] * 7 + [":q"]), contextlib.redirect_stdout(io.StringIO()) as out:
            with self.assertRaises(LeaveSession):
                self.app.learn(warmup=False)
        self.assertNotIn("WRITE  ·", out.getvalue())
        self.assertEqual(self.store.db.execute("SELECT COUNT(*) FROM progress WHERE passed=1").fetchone()[0], 7)
        with contextlib.redirect_stdout(io.StringIO()):
            original = self.app.ask
            self.app.ask = lambda q, mode: original(q, mode, demo_answer="correct")
            self.app.learn(warmup=False)
        self.assertTrue(self.store.is_complete("python:variables"))
        self.assertTrue(self.app.unlocked(self.course.lessons[1]))
        self.assertEqual(len(self.store.mistakes(self.app.keys)), 1)

    def test_walk_entire_curriculum(self):
        self.app.rng.shuffle = lambda values: None
        original = self.app.ask
        self.app.ask = lambda q, mode: original(q, mode, demo_answer="correct")
        for lesson in self.course.lessons:
            with contextlib.redirect_stdout(io.StringIO()):
                self.app.learn(lesson["id"], warmup=False)
            self.assertTrue(self.store.is_complete(self.course.lesson_key(lesson["id"])))
        self.assertEqual(self.store.stats()["daily"], 18)
        self.assertEqual(self.store.player()["hearts"], 5)

    def test_persistence_and_namespaced_courses(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "progress.sqlite3"
            s = Store(path, self.clock)
            s.record("python:a", "wrong", False, "learn")
            s.record("python:b", "right", True, "learn")
            s.active_lesson("python", "numpy")
            s.close()
            s = Store(path, self.clock)
            self.assertTrue(s.passed("python:b"))
            self.assertEqual(s.active_lesson("python"), "numpy")
            self.assertFalse(s.passed("rust:b"))
            self.assertEqual(s.player()["hearts"], 4)
            self.assertEqual(s.due({"rust:a"}, early=True), [])
            self.assertEqual(s.due({"python:a"}, early=True), ["python:a"])
            s.close()

    def test_resume_selected_specialized_branch(self):
        for lesson in self.course.lessons[:10]:
            for q in lesson["questions"]:
                self.record(qid=self.course.key(q["id"]))
            self.store.complete(self.course.lesson_key(lesson["id"]), [self.course.key(q["id"]) for q in lesson["questions"]])
        self.app.rng.shuffle = lambda values: None
        with patch("builtins.input", side_effect=["A", ":q"]), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(LeaveSession):
                self.app.learn("numpy", warmup=False)
        with contextlib.redirect_stdout(io.StringIO()):
            original = self.app.ask
            self.app.ask = lambda q, mode: original(q, mode, demo_answer="correct")
            self.app.learn(warmup=False)
        self.assertTrue(self.store.is_complete("python:numpy"))
        self.assertFalse(self.store.is_complete("python:mutation"))

    def test_cli_demo_is_isolated_and_invalid_lesson_reports_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--data-dir", tmp, "--plain", "demo"]), 0)
            self.assertEqual(list(Path(tmp).iterdir()), [])
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--data-dir", tmp, "learn", "nonexistent"]), 1)


class ContentEvidenceTests(unittest.TestCase):
    """Execute only bundled, authored examples; never learner submissions."""

    def test_core_print_examples_against_python(self):
        course = load_course()
        cases = {
            "variables-1": "9", "variables-2": "city", "variables-3": "6", "variables-4": "jobs 3",
            "arithmetic-1": "14", "arithmetic-2": "2 1", "arithmetic-3": "4.0", "arithmetic-4": "-3",
            "strings-1": "o", "strings-2": "txt", "strings-3": "ADA", "strings-4": "4 files",
            "conditions-1": "wait", "conditions-2": "high", "conditions-4": "",
            "containers-1": "30", "containers-2": "None", "containers-3": "False", "containers-4": "480",
            "loops-1": "1\n2\n3", "loops-2": "1 a\n2 b", "loops-3": "ok", "loops-4": "found",
            "functions-1": "Hi Jo", "functions-3": "1", "modules-1": "3",
            "errors-1": "0", "errors-2": "bad input", "errors-3": "work\ncleanup",
            "mutation-1": "2", "mutation-2": "1", "mutation-3": "[1, 9]", "mutation-4": "2",
            "classes-1": "build", "classes-2": "0", "classes-3": "8000", "classes-4": "many",
            "iteration-2": "6", "iteration-3": "[]", "decorators-1": "6", "decorators-4": "ready",
        }
        for qid, expected in cases.items():
            with self.subTest(qid=qid):
                run = subprocess.run([sys.executable, "-I", "-c", course.questions[qid]["code"]], text=True, capture_output=True, timeout=5)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertEqual(run.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
