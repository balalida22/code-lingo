from datetime import datetime, timedelta
import contextlib
import io
import tempfile
from pathlib import Path
import unittest
from codelingo.store import Store
from codelingo.cli import App, Terminal
from codelingo.course import load_course
from codelingo.tui import TuiApp


class StreakRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026,9,14,12).timestamp()
        self.store = Store(':memory:', lambda: self.now)

    def tearDown(self):
        self.store.close()

    def prior_streak(self, missed):
        today = datetime.fromtimestamp(self.now).date()
        for days_ago in range(missed+1, missed+4):
            at = datetime.combine(today-timedelta(days=days_ago), datetime.min.time()).timestamp()
            self.store._completion_event('lesson', 'python:first', at)
        self.store.db.commit()

    def work(self, lessons, reviews):
        for i in range(lessons):
            self.store._completion_event('lesson', f'python:lesson{i}')
        for i in range(reviews):
            self.store.db.execute('INSERT INTO attempts(qid,at,answer,correct,mode) VALUES(?,?,?,?,?)',
                (f'rust:q{i}',self.now,'a',1,'review'))
        self.store.db.commit()

    def test_one_day_requires_both_targets_and_claim_is_idempotent(self):
        self.prior_streak(1)
        self.work(2,9)
        self.assertFalse(self.store.restore_streak())
        self.work(2,10)
        self.assertEqual(self.store.streak_recovery()['reviews'],10)
        before=self.store.stats()['daily']
        self.assertTrue(self.store.restore_streak())
        self.assertEqual(self.store.stats()['streak'],5)
        self.assertEqual(self.store.stats()['daily'],before)
        self.assertFalse(self.store.restore_streak())
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM streak_repairs').fetchone()[0],1)
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM completed').fetchone()[0],0)

    def test_two_days_doubles_targets(self):
        self.prior_streak(2)
        self.work(2,10)
        p=self.store.streak_recovery()
        self.assertEqual((p['target_lessons'],p['target_reviews']),(4,20))
        self.assertFalse(self.store.restore_streak())
        self.work(4,20)
        self.assertTrue(self.store.restore_streak())
        self.assertEqual(self.store.stats()['streak'],6)

    def test_no_prior_streak_or_long_gap_cannot_repair(self):
        self.work(4,20)
        self.assertFalse(self.store.restore_streak())
        self.prior_streak(3)
        self.assertFalse(self.store.restore_streak())
        self.assertEqual(self.store.streak_recovery()['missed'],3)

    def test_current_streak_does_not_need_repair(self):
        self.prior_streak(0)
        self.work(2,10)
        self.assertFalse(self.store.streak_recovery()['eligible'])
        self.assertFalse(self.store.restore_streak())

    def test_wrong_practice_and_old_reviews_do_not_count(self):
        self.prior_streak(1)
        for correct,mode,at in [(0,'review',self.now),(1,'practice',self.now),
                               (1,'review',self.now-86400),(1,'review',self.now+86400)]:
            self.store.db.execute('INSERT INTO attempts(qid,at,answer,correct,mode) VALUES(?,?,?,?,?)',
                                  ('python:q',at,'a',correct,mode))
        self.assertEqual(self.store.streak_recovery()['reviews'],0)

    def test_section_exam_counts_once_not_each_unlocked_lesson(self):
        self.prior_streak(1)
        for state in ['passed','failed','active']:
            cursor=self.store.db.execute('INSERT INTO exams(course,section,questions,state,at) VALUES(?,?,?,?,?)',
                                         ('python','Basics','[]',state,self.now))
            self.store._completion_event('exam',str(cursor.lastrowid))
        self.assertEqual(self.store.streak_recovery()['lessons'],1)

    def test_expiry_on_following_day(self):
        self.prior_streak(2)
        self.now+=86400
        self.assertFalse(self.store.streak_recovery()['eligible'])

    def test_restart_preserves_claim_and_next_day_continuation(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'progress.db'
            self.prior_streak(1);self.work(2,10)
            backup=Store(file,lambda:self.now)
            self.store.db.backup(backup.db);backup.close()
            backup=Store(file,lambda:self.now)
            self.assertTrue(backup.restore_streak());backup.close()
            self.now+=86400
            backup=Store(file,lambda:self.now)
            backup._completion_event('lesson','ruby:first');backup.db.commit()
            self.assertEqual(backup.stats()['streak'],6)
            backup.close()

    def test_tui_recovery_review_action_and_plain_progress(self):
        self.prior_streak(1)
        class Picker:
            choices=iter([2,None])
            def choose(self,*args,**kwargs):return next(self.choices)
        app=TuiApp(load_course(),self.store,Picker(),1)
        reviews=[]
        app.action=lambda f:f()
        app.review=lambda **kwargs:reviews.append(kwargs)
        app.pick_streak_recovery()
        self.assertEqual(reviews,[{'limit':20,'early':True}])
        app=App(load_course(),self.store,Terminal(True))
        with contextlib.redirect_stdout(io.StringIO()) as out:app.recover_streak()
        self.assertIn('Lessons/exams: 0/2',out.getvalue())
        self.assertIn('questions: 0/10',out.getvalue())
