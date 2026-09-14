import contextlib
import io
import unittest
from unittest.mock import patch
from codelingo.cli import App, Terminal
from codelingo.course import load_course
from codelingo.store import Store
from codelingo.tui import TuiApp


class QuestionMarkTests(unittest.TestCase):
    def setUp(self):
        self.course = load_course('rust')
        self.question = next(q for q in self.course.questions.values()
                             if q['kind'] != 'mcq' and '?' in q.get('accepted', []))
        self.store = Store(':memory:')

    def tearDown(self):
        self.store.close()

    def test_plain_writing_hint_then_literal_operator_is_correct(self):
        app = App(self.course,self.store,Terminal(True),1)
        with patch('builtins.input',side_effect=[':hint','?']), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertTrue(app.ask(self.question,'practice'))
        self.assertIn('Hint:',out.getvalue())
        self.assertEqual(self.store.db.execute('SELECT answer,correct FROM attempts').fetchone()[:],('?',1))

    def test_plain_exam_submits_literal_operator(self):
        app = App(self.course,self.store,Terminal(True),1)
        with patch('builtins.input',return_value='?'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(app.exam_answer(self.question,1,25),'?')

    def test_tui_writing_and_exam_submit_operator_without_interception(self):
        class Editor:
            def edit(self,*args):return '?'
        app = TuiApp(self.course,self.store,Editor(),1)
        for exam in (False,True):
            self.assertEqual(app.read_answer(self.question,'Rust',exam=exam),'?')

    def test_tui_explicit_hint_and_exam_hint_rejection(self):
        for exam in (False,True):
            class Editor:
                answers = iter([':hint','?'])
                bodies = []
                def edit(self,title,body):
                    self.bodies.append(body)
                    return next(self.answers)
            editor = Editor()
            app = TuiApp(self.course,self.store,editor,1)
            self.assertEqual(app.read_answer(self.question,'Rust',exam=exam),'?')
            self.assertIn('Hints are unavailable' if exam else 'Hint:',editor.bodies[1])

    def test_plain_mcq_keeps_question_mark_hint_shortcut(self):
        question = {'id':'test-hint','kind':'mcq','concept':'test','prompt':'Choose yes',
                    'options':['yes'],'answer':'yes','hint':'Choose yes','explanation':'Yes.'}
        app = App(self.course,self.store,Terminal(True),1)
        with patch('builtins.input',side_effect=['?','A']), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertTrue(app.ask(question,'practice'))
        self.assertIn('Hint:',out.getvalue())
