import contextlib
import io
import unittest
from unittest.mock import patch
from codelingo.cli import App, Terminal
from codelingo.course import load_course
from codelingo.store import Store
from codelingo.tui import TuiApp, Screen
from test_v2 import FakeWindow, FakeCurses


class SectionNavigationTests(unittest.TestCase):
    def setUp(self):
        self.course = load_course()
        self.store = Store(':memory:')

    def tearDown(self):
        self.store.close()

    def test_section_filter_back_and_open_focus(self):
        first = self.course.lessons[0]
        self.store.db.execute('INSERT INTO completed(lid,at) VALUES(?,?)',
                              (self.course.lesson_key(first['id']), 1))
        calls = []
        class Picker:
            selections = iter([0, None, 1, None, None])
            def choose(self, title, body, options, **kwargs):
                calls.append((title, options, kwargs))
                return next(self.selections)
        app = TuiApp(self.course, self.store, Picker(), 1)
        app.pick_lesson()
        self.assertEqual(len(calls[0][1]), 4)
        self.assertIn('1/5 lessons done', calls[0][1][0])
        self.assertEqual(len(calls[1][1]), 5)
        self.assertEqual(calls[1][2]['initial'], 1)
        self.assertIn('Basics', calls[1][0])
        self.assertIn('Intermediate', calls[3][0])
        self.assertEqual(calls[4][2]['initial'], 1)

    def test_active_preferred_and_completed_fallback(self):
        self.assertEqual(App.preferred_lesson_index(['DONE','OPEN','ACTIVE','LOCK']), 2)
        self.assertEqual(App.preferred_lesson_index(['DONE','DONE']), 0)
        self.assertEqual(App.preferred_lesson_index(['LOCK','LOCK']), 0)

    def test_cursor_stays_centered_while_scrolling(self):
        win = FakeWindow([FakeCurses.KEY_DOWN, '\n'])
        screen = Screen(win, self.store, FakeCurses())
        self.assertEqual(screen.choose('Lessons', '', [f'Lesson {n}' for n in range(30)], initial=12), 13)
        for frame in win.frames:
            rows = [y for y, text in frame.items() if 'Lesson ' in text]
            selected = next(y for y in rows if '›' in frame[y])
            self.assertLessEqual(abs(selected - (min(rows)+max(rows))/2), 1)

    def test_plain_menu_section_back(self):
        app = App(self.course, self.store, Terminal(True), 1)
        with patch('builtins.input', side_effect=['1','b','b']), contextlib.redirect_stdout(io.StringIO()) as out:
            app.pick_lesson()
        self.assertIn('Basics · Choose a lesson', out.getvalue())
        self.assertNotIn('Intermediate · Choose a lesson', out.getvalue())
