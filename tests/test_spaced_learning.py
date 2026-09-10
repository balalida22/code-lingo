"""Clock-driven review regressions and upgrades of existing learning history."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest

from codelingo.cli import App, Terminal
from codelingo.course import load_course
from codelingo.store import Store
from test_engine import Clock


class SpacedLearningTests(unittest.TestCase):
    def test_correct_learning_intervals_and_lapse(self):
        clock = Clock()
        store = Store(':memory:', clock)
        self.addCleanup(store.close)
        store.record('rust:a', 'yes', True, 'learn')
        self.assertEqual(store.due({'rust:a'}), [])
        for days in (1, 3, 7, 14, 30, 30):
            self.assertEqual(store.db.execute('SELECT due FROM reviews').fetchone()[0], clock()+days*86400)
            clock.advance(days*86400)
            self.assertEqual(store.due({'rust:a'}), ['rust:a'])
            store.record('rust:a', 'yes', True, 'review')
        store.record('rust:a', 'no', False, 'review')
        self.assertEqual(store.db.execute('SELECT due FROM reviews').fetchone()[0], clock()+600)
        self.assertTrue(store.passed('rust:a'))

    def test_early_success_and_exam_do_not_reset_schedule(self):
        clock = Clock()
        store = Store(':memory:', clock)
        self.addCleanup(store.close)
        store.record('c:a', 'yes', True, 'exam')
        due = store.db.execute('SELECT due FROM reviews').fetchone()[0]
        for mode in ('learn', 'practice', 'review', 'exam'):
            clock.advance(60)
            store.record('c:a', 'yes', True, mode)
            self.assertEqual(store.db.execute('SELECT due FROM reviews').fetchone()[0], due)
        self.assertEqual(store.stats()['daily'], 0)
        self.assertEqual(store.due({'rust:a'}, early=True), [])

    def test_upgrade_backfills_once_and_keeps_existing_mistakes(self):
        clock = Clock()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'progress.db'
            store = Store(path, clock)
            store.record('python:a', 'yes', True, 'learn')
            store.record('python:b', 'no', False, 'learn')
            store.record('python:exam', 'yes', True, 'exam')
            with store.db:
                store.db.execute("DELETE FROM migrations WHERE name='learned_card_reviews'")
                store.db.execute("DELETE FROM reviews WHERE qid IN ('python:a','python:exam')")
            player = store.player()
            store.close()
            clock.advance(2*86400)
            store = Store(path, clock)
            self.assertEqual(set(store.due({'python:a','python:b'})), {'python:a','python:b'})
            self.assertEqual(store.db.execute("SELECT stage FROM reviews WHERE qid='python:b'").fetchone()[0], 0)
            self.assertEqual(store.due({'python:exam'}), ['python:exam'])
            self.assertEqual(store.player()['xp'], player['xp'])
            store.record('python:a', 'yes', True, 'review')
            due = store.db.execute("SELECT due FROM reviews WHERE qid='python:a'").fetchone()[0]
            store.close()
            store = Store(path, clock)
            self.assertEqual(store.db.execute("SELECT due FROM reviews WHERE qid='python:a'").fetchone()[0], due)
            store.close()

    def test_due_review_uses_new_variant_without_unlocking_or_daily_credit(self):
        clock = Clock()
        store = Store(':memory:', clock)
        self.addCleanup(store.close)
        app = App(load_course('rust'), store, Terminal(True), 17)
        template = app.course.questions['bindings-read-1']
        first = app.prepare_question(template)
        app.grade(first, App.solution(first), 'learn')
        clock.advance(86400)
        seen = []
        def answer(q, mode):
            variant = app.prepare_question(q)
            seen.append(variant)
            return app.grade(variant, App.solution(variant), mode)
        app.ask = answer
        with contextlib.redirect_stdout(io.StringIO()):
            app.review()
        self.assertEqual(len(seen), 1)
        self.assertNotEqual(first['code'], seen[0]['code'])
        self.assertEqual(app.progress.counts, (1,0,0))
        self.assertFalse(store.is_complete('rust:bindings'))
        self.assertEqual(store.stats()['daily'], 0)
