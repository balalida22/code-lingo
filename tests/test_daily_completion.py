import contextlib
import io
from pathlib import Path
import random
import tempfile
import unittest

from codelingo.cli import App, Terminal, LeaveSession
from codelingo.course import load_course
from codelingo.exams import Exam
from codelingo.store import Store
from test_engine import Clock


class DailyCompletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.course=load_course()
    def setUp(self):
        self.clock=Clock();self.store=Store(':memory:',self.clock)
        self.app=App(self.course,self.store,Terminal(True),1)
    def tearDown(self):self.store.close()
    def learn_first(self):
        original=self.app.ask
        self.app.ask=lambda q,mode:original(q,mode,demo_answer='correct')
        with contextlib.redirect_stdout(io.StringIO()):self.app.learn('variables',warmup=False)
        self.app.ask=original

    def test_questions_and_short_practice_do_not_complete_daily_goal(self):
        original=self.app.ask
        self.app.ask=lambda q,mode:original(q,mode,demo_answer='correct')
        with contextlib.redirect_stdout(io.StringIO()):self.app.practice(limit=5)
        self.assertEqual(self.store.stats()['daily'],0)
        self.assertEqual(self.store.stats()['streak'],0)
        self.assertGreater(self.store.player()['xp'],0)

    def test_lesson_completion_counts_once_not_per_question(self):
        self.learn_first()
        self.assertEqual(self.store.stats()['daily'],1)
        self.assertEqual(self.store.stats()['streak'],1)
        self.store.complete('python:variables',[self.course.key(q['id']) for q in self.course.lessons[0]['questions']])
        self.assertEqual(self.store.stats()['daily'],1)

    def test_final_submission_secures_goal_before_feedback_is_dismissed(self):
        lesson=self.course.lessons[0]
        self.app.begin_session('learn',lesson['questions'])
        for template in lesson['questions']:
            q=self.app.prepare_question(template)
            self.app.grade(q,self.app.solution(q),'learn')
        self.assertEqual(self.store.stats()['daily'],1)
        self.assertTrue(self.store.is_complete('python:variables'))

    def test_replay_counts_after_all_twelve_questions_on_a_new_day(self):
        self.learn_first();self.clock.advance(86400)
        original=self.app.ask;seen=[]
        def answer(q,mode):
            seen.append(q['id'])
            result=original(q,mode,demo_answer='correct')
            if len(seen)<12:self.assertEqual(self.store.stats()['daily'],0)
            return result
        self.app.ask=answer
        with contextlib.redirect_stdout(io.StringIO()):self.app.learn('variables')
        self.assertEqual(len(seen),12)
        self.assertEqual(self.store.stats()['daily'],1)
        self.assertEqual(self.store.stats()['streak'],2)

    def test_interrupted_replay_does_not_count(self):
        self.learn_first();self.clock.advance(86400)
        original=self.app.ask;count=0
        def answer(q,mode):
            nonlocal count
            count+=1
            if count==4:raise LeaveSession
            return original(q,mode,demo_answer='correct')
        self.app.ask=answer
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(LeaveSession):self.app.learn('variables')
        self.assertEqual(self.store.stats()['daily'],0)

    def test_finished_failed_exam_counts_but_does_not_unlock(self):
        exam=Exam(self.course,self.store,'Basics',random.Random(1))
        for _ in exam.questions:exam.submit('[wrong]')
        self.assertEqual(self.store.stats()['daily'],0)
        result=exam.finish()
        self.assertFalse(result['passed'])
        self.assertEqual(self.store.stats()['daily'],1)
        self.assertEqual(self.store.stats()['streak'],1)
        self.assertFalse(self.store.is_complete('python:variables'))

    def test_passed_exam_counts_once_for_whole_section(self):
        exam=Exam(self.course,self.store,'Basics',random.Random(1))
        for q in exam.questions:exam.submit(self.app.solution(q))
        self.assertTrue(exam.finish()['passed'])
        self.assertEqual(self.store.stats()['daily'],1)
        with self.assertRaises(ValueError):exam.finish()
        self.assertEqual(self.store.stats()['daily'],1)

    def test_abandoned_exam_does_not_count(self):
        exam=Exam(self.course,self.store,'Basics',random.Random(1))
        exam.submit('[wrong]');exam.abort();exam.save_attempts()
        self.assertEqual(self.store.stats()['daily'],0)

    def test_exam_counts_on_finish_date_across_midnight(self):
        exam=Exam(self.course,self.store,'Basics',random.Random(1))
        for _ in exam.questions:exam.submit('[wrong]')
        yesterday=self.store.today();self.clock.advance(86400)
        exam.finish()
        self.assertEqual(self.store.stats()['daily'],1)
        self.assertFalse(self.store.db.execute('SELECT 1 FROM daily_completions WHERE day=?',(yesterday,)).fetchone())

    def test_migration_preserves_previous_streak_days_not_todays_card_goal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'progress.sqlite3';s=Store(path,self.clock)
            self.clock.advance(-86400)
            for i in range(5):s.record(str(i),'ok',True,'learn')
            self.clock.advance(86400)
            for i in range(5):s.record(str(i),'ok',True,'learn')
            # Simulate the old database before completion-goal migration.
            with s.db:
                s.db.execute("DELETE FROM migrations WHERE name='completion_daily_goal'")
                s.db.execute('DELETE FROM daily_completions')
            s.close();s=Store(path,self.clock)
            self.assertEqual(s.stats()['streak'],1)
            self.assertEqual(s.stats()['daily'],0)
            s.complete('first',[str(i) for i in range(5)])
            self.assertEqual(s.stats()['streak'],2)
            self.assertEqual(s.stats()['daily'],1)
            s.close();s=Store(path,self.clock)
            self.assertEqual(s.stats()['daily'],1)
            s.close()


if __name__=='__main__':unittest.main()
