import contextlib
import io
import random
import unittest
from codelingo.cli import App,Terminal
from codelingo.course import load_course,check_answer
from codelingo.exams import Exam
from codelingo.store import Store
from codelingo.templates import render

LIBRARIES=('numpy','matplotlib','pytorch','transformers')


class PythonLibraryTests(unittest.TestCase):
    def test_course_depth_variants_and_fragment_answers(self):
        for cid in LIBRARIES:
            c=load_course(cid)
            self.assertEqual(len(c.lessons),12)
            self.assertEqual(len(c.questions),144)
            self.assertEqual([l['section'] for l in c.lessons],['Basics']*4+['Intermediate']*4+['Advanced']*4)
            for template in c.questions.values():
                for seed in range(20):
                    q=render(template,random.Random(seed))
                    self.assertTrue(check_answer(q,App.solution(q)),(cid,q['id']))
                    self.assertFalse(check_answer(q,'[incorrect]'),(cid,q['id']))
                    self.assertNotIn('${',str(q))

    def test_fragment_checker_handles_slices_keywords_and_quotes(self):
        c=load_course('numpy')
        q=render(c.questions['indexing-write-3'],random.Random(4))
        self.assertTrue(check_answer(q,'0 : 1'))
        self.assertFalse(check_answer(q,'0'))
        q=render(c.questions['broadcasting-write-repair-4'],random.Random(4))
        self.assertTrue(check_answer(q,'b[ : , None ]'))
        self.assertFalse(check_answer(q,'b[None, :]'))
        q=render(load_course('transformers').questions['chat-write-3'],random.Random(4))
        self.assertTrue(check_answer(q,'add_special_tokens = False'))
        self.assertFalse(check_answer(q,'add_special_tokens = True'))
        q=render(load_course('matplotlib').questions['objects-write-4'],random.Random(4))
        self.assertFalse(check_answer(q,'set_title; print("injected")'))
        self.assertFalse(check_answer(q,'x'*2001))

    def test_all_library_lessons_complete_and_schedule_review(self):
        for cid in LIBRARIES:
            store=Store(':memory:')
            try:
                c=load_course(cid);app=App(c,store,Terminal(True),4)
                ask=app.ask
                app.ask=lambda q,mode:ask(q,mode,demo_answer='correct')
                with contextlib.redirect_stdout(io.StringIO()):
                    for lesson in c.lessons:app.learn(lesson['id'],warmup=False)
                self.assertTrue(all(store.is_complete(c.lesson_key(l['id'])) for l in c.lessons))
                self.assertEqual(len(store.due(app.keys,limit=1000,early=True)),144)
                self.assertEqual(store.stats()['daily'],12)
            finally:store.close()

    def test_exams_cover_each_lesson_without_costing_hearts(self):
        for cid in LIBRARIES:
            store=Store(':memory:');c=load_course(cid)
            try:
                for section in ('Basics','Intermediate','Advanced'):
                    exam=Exam(c,store,section,random.Random(4))
                    self.assertEqual(len(exam.questions),25)
                    for lesson in exam.lessons:
                        kinds={q['kind'] for q in exam.questions if c.lesson_for[q['id']]['id']==lesson['id']}
                        self.assertEqual(kinds,{'mcq','write'})
                    for i,q in enumerate(exam.questions):exam.submit('[wrong]' if i<4 else App.solution(q))
                    self.assertTrue(exam.finish()['passed'])
                    self.assertEqual(store.player()['hearts'],5)
                    self.assertTrue(all(store.is_complete(c.lesson_key(l['id'])) for l in exam.lessons))
            finally:store.close()

    def test_sampler_completion_does_not_fabricate_library_progress(self):
        store=Store(':memory:')
        self.addCleanup(store.close)
        python=load_course('python')
        for cid in LIBRARIES:
            lesson=python.by_id[cid]
            for q in lesson['questions']:store.record(python.key(q['id']),'correct',True,'learn')
            store.complete(python.lesson_key(cid),[python.key(q['id']) for q in lesson['questions']])
            expanded=load_course(cid)
            self.assertFalse(any(store.is_complete(expanded.lesson_key(l['id'])) for l in expanded.lessons))
            self.assertEqual(store.due({expanded.key(qid) for qid in expanded.questions},early=True),[])
            self.assertTrue(store.is_complete(python.lesson_key(cid)))
