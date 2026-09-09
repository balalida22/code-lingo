import contextlib
import io
import random
import unittest
from codelingo.cli import App,Terminal
from codelingo.course import load_course,course_catalog
from codelingo.exams import Exam
from codelingo.store import Store
from codelingo.templates import render
from codelingo.tui import Screen,TuiApp
from test_v2 import FakeCurses,FakeWindow

class FeedbackTests(unittest.TestCase):
    def test_feedback_colors_are_pinned_and_do_not_leak_to_next_page(self):
        class Window(FakeWindow):
            def __init__(self):super().__init__(['\n','\n','\n']);self.styles=[]
            def addnstr(self,y,x,text,n,style):
                if y==2:self.styles.append((text,style))
                super().addnstr(y,x,text,n,style)
        store=Store(':memory:')
        try:
            window=Window();screen=Screen(window,store,FakeCurses());screen.color=lambda n:n*16
            screen.page('Correct','Nice work',title_color=2)
            screen.page('Incorrect','Review the explanation',title_color=4)
            screen.page('Next question','Neutral title')
            self.assertEqual(window.styles,[('Correct',32|2),('Incorrect',64|2),('Next question',16|2)])
        finally:store.close()

    def test_lesson_answers_choose_correct_feedback_title_color(self):
        class Picker:
            progress=None
            def __init__(self):self.pages=[]
            def page(self,title,body,title_color=1):self.pages.append((title,title_color));return True
        store=Store(':memory:')
        try:
            picker=Picker();app=TuiApp(load_course(),store,picker,4)
            app.read_answer=lambda q,title:App.solution(q)
            app.ask(app.course.lessons[0]['questions'][0],'learn')
            app.read_answer=lambda q,title:'wrong'
            app.ask(app.course.lessons[0]['questions'][1],'learn')
            self.assertEqual(picker.pages,[('Correct',2),('Incorrect · Learn from this one',4)])
        finally:store.close()

    def test_plain_feedback_uses_green_and_red_when_color_enabled(self):
        store=Store(':memory:')
        try:
            terminal=Terminal(True);terminal.color=True;app=App(load_course(),store,terminal,3)
            q=app.course.lessons[0]['questions'][0]
            with contextlib.redirect_stdout(io.StringIO()) as output:
                app.ask(q,'learn',App.solution(q));app.ask(q,'learn','[wrong-demo]')
            self.assertIn('\x1b[32m\nCorrect!',output.getvalue())
            self.assertIn('\x1b[31m\nIncorrect.',output.getvalue())
        finally:store.close()

class RustBookTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.course=load_course('rust')

    def test_book_specific_progression_and_chapter_provenance(self):
        c=self.course;ids=list(c.by_id)
        self.assertEqual(ids[0],'cargo')
        self.assertLess(ids.index('ownership'),ids.index('collections'))
        self.assertLess(ids.index('borrowing'),ids.index('lifetimes'))
        self.assertLess(ids.index('threads'),ids.index('async'))
        for lid in ('bindings','models','patterns','generics','lifetimes','testing','workspaces','smart-pointers','threads','async','trait-objects','advanced-rust'):
            self.assertIn(lid,ids)
        self.assertFalse(any(l['section']=='Specialized' for l in c.lessons))
        refs={s['id']:s['url'] for s in c.data['sources']}
        for lesson in c.lessons:
            self.assertTrue(all(refs[s].startswith('https://doc.rust-lang.org/book/') for s in lesson['sources']))
            self.assertIn('chapter',lesson['intro'])

    def test_new_error_families_and_utf8_values(self):
        c=self.course
        for seed in range(30):
            q=render(c.questions['text-read-utf8'],random.Random(seed))
            word=q['variant']['word'];self.assertEqual(q['answer'],f'{len(("λ"+word).encode())} {len("λ"+word)}')
        for qid in ('bindings-read-3','ownership-read-1','collections-read-map-ownership','lifetimes-read-4','threads-read-4','trait-objects-read-4'):
            self.assertIn('Compile error',c.questions[qid]['answer'])
        self.assertIn('Panics',c.questions['smart-pointers-read-3']['answer'])
        self.assertEqual(c.questions['async-read-1']['answer'],'done')
        self.assertNotIn('collections-read-3',c.questions)
        self.assertIn('collections-read-entry',c.questions)

    def test_error_predictions_lead_to_repair_exercises(self):
        c=self.course
        broken=[q for q in c.questions.values() if '-read-' in q['id'] and q['answer'].startswith(('Compile error','Panics:'))]
        self.assertEqual(len(broken),10)
        for q in broken:
            repair=c.questions[q['id'].replace('-read-','-write-repair-')]
            self.assertIn('Repair the code',repair['prompt'])
            self.assertNotIn('Target result: Compile error',repair['prompt'])
            self.assertNotIn('Target result: Panics',repair['prompt'])

    def test_old_progress_survives_without_counting_retired_lessons(self):
        old_ids=['values','arithmetic','text','branches','loops','functions','collections','io','modules','results','ownership','borrowing','traits','iterators']
        store=Store(':memory:')
        class Picker:
            progress=None
            def choose(self,title,body,labels,**kwargs):self.labels=labels;return None
        try:
            for lid in old_ids:store.db.execute('INSERT INTO completed(lid,at) VALUES(?,?)',('rust:'+lid,store.clock()))
            store.db.commit();store.record('rust:ownership-read-1','old mistake',False,'exam')
            before=store.stats()['xp'];picker=Picker();app=TuiApp(self.course,store,picker,1)
            app.pick_course()
            label=next(s for s in picker.labels if s.startswith('Rust:'))
            self.assertIn('12/26',label)
            self.assertTrue(store.is_complete('rust:values'))
            self.assertEqual(len(store.mistakes(app.keys)),1)
            self.assertEqual(store.stats()['xp'],before)
            self.assertFalse(app.unlocked(self.course.by_id['bindings']))
            exam=Exam(self.course,store,'Basics',random.Random(1))
            for q in exam.questions:exam.submit(App.solution(q))
            self.assertTrue(exam.finish()['passed'])
            self.assertTrue(store.is_complete('rust:bindings'))
        finally:store.close()
