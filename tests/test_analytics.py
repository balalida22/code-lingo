import contextlib
from datetime import datetime
import io
import unittest
from unittest.mock import patch

from codelingo.analytics import snapshot, report
from codelingo.cli import App, Terminal
from codelingo.course import load_course
from codelingo.store import Store
from codelingo.tui import TuiApp, Screen
from test_v2 import FakeWindow, FakeCurses


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 11, 12).timestamp()
        self.store = Store(':memory:', lambda: self.now)
        self.course = load_course()

    def tearDown(self):
        self.store.close()

    def answer(self, course, question, correct, mode='learn', at=None):
        self.store.db.execute('INSERT INTO attempts(qid,at,answer,correct,mode) VALUES(?,?,?,?,?)',
                              (course+':'+question, self.now if at is None else at, '', correct, mode))

    def test_empty_and_read_only(self):
        before = self.store.db.total_changes
        data = snapshot(self.store, self.course)
        self.assertIn('Courses attempted: 0/21', report(data))
        self.assertIn('Answer accuracy: N/A', report(data))
        self.assertIn('No activity yet', report(data))
        self.assertEqual(self.store.db.total_changes, before)

    def test_weighted_accuracy_retries_and_exact_course_filter(self):
        self.answer('c', 'q', 1)
        for i in range(9):
            self.answer('cpp', 'q', 0, 'review')
        data = snapshot(self.store)
        self.assertIn('Answer accuracy: 10.0%', report(data))
        self.assertIn('Unique questions seen: 2', report(data))
        self.assertIn('Answers: 1 · Correct: 1', report(data, 'c'))
        self.assertIn('Answer accuracy: 100.0%', report(data, 'c'))
        self.assertEqual(data['courses']['cpp']['modes']['review'], (0, 9))
        with self.assertRaises(ValueError):
            report(data, 'not-a-course')

    def test_seven_local_days_include_boundary_exclude_old_and_future(self):
        boundary = datetime(2026, 9, 5).timestamp()
        for at in (boundary-1, boundary, self.now, self.now+86400):
            self.answer('python', str(at), 1, at=at)
        data = snapshot(self.store)
        self.assertEqual(data['days'], [f'2026-09-{i:02}' for i in range(5,12)])
        self.assertEqual(data['courses']['python']['activity'], {'2026-09-05':1,'2026-09-11':1})
        self.assertEqual(data['courses']['python']['attempts'], 4)

    def test_exam_completion_due_legacy_and_unavailable_courses(self):
        self.store.db.execute('INSERT INTO completed(lid,at,origin) VALUES(?,?,?)',
            (self.course.lesson_key(self.course.lessons[0]['id']),self.now,'exam'))
        for state in ('passed','failed','active','abandoned'):
            self.store.db.execute('INSERT INTO exams(course,section,questions,state,at) VALUES(?,?,?,?,?)',
                                  ('python','Basics','[]',state,self.now))
        self.store.db.execute('INSERT INTO reviews(qid,due) VALUES(?,?)',('python:q',self.now))
        self.store.db.execute('INSERT INTO reviews(qid,due) VALUES(?,?)',('python:r',self.now+1))
        self.store.db.execute('INSERT INTO progress(qid,attempts) VALUES(?,?)',('old-custom:q',2))
        data = snapshot(self.store)
        python = data['courses']['python']
        self.assertEqual((python['done'], python['due'], python['exams'], python['passed_exams']), (1,1,2,1))
        self.assertTrue(python['attempted'])
        self.assertTrue(data['courses']['old-custom']['attempted'])
        self.assertIn('course size unavailable', report(data, 'old-custom'))
        self.assertIn('Answer accuracy: N/A', report(data, 'old-custom'))

    def test_tui_filter_only_attempted_and_does_not_switch_course(self):
        self.answer('rust','q',1)
        calls = []
        class Picker:
            selections = iter([0,1,0,None,1])
            def choose(self,title,body,options,**kwargs):
                calls.append((title,body,options,kwargs))
                return next(self.selections)
        app = TuiApp(self.course,self.store,Picker(),1)
        before = self.store.db.total_changes
        app.pick_analytics()
        self.assertEqual(len(calls[1][2]),2)
        self.assertEqual(calls[1][2][0],'All courses')
        self.assertIn('Rust', calls[1][2][1])
        self.assertIn('Courses attempted: 1/1', calls[2][1])
        self.assertEqual(calls[3][3]['initial'],1)
        self.assertEqual(app.course.id,'python')
        self.assertEqual(self.store.db.total_changes,before)

    def test_graphs_can_scroll_at_minimum_terminal_size(self):
        win = FakeWindow([FakeCurses.KEY_NPAGE,'q'], (18,60))
        Screen(win,self.store,FakeCurses()).choose('Analytics',report(snapshot(self.store)),['Filter','Back'])
        self.assertTrue(any('More text' in line for line in win.frames[0].values()))
        self.assertNotEqual(win.frames[0],win.frames[1])

    def test_plain_filter_and_back(self):
        self.answer('rust','q',1)
        app = App(self.course,self.store,Terminal(True))
        with patch('builtins.input',side_effect=['bad','1','b']), contextlib.redirect_stdout(io.StringIO()) as out:
            app.pick_analytics()
        self.assertIn('Choose a listed number or b.',out.getvalue())
        self.assertIn('Courses attempted: 1/1',out.getvalue())
        self.assertEqual(app.course.id,'python')
