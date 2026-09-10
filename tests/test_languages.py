import contextlib
import io
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from codelingo.course import load_course,course_catalog,check_answer,Course
from codelingo.templates import render
from codelingo.store import Store
from codelingo.exams import Exam
from codelingo.cli import App,Terminal,main
from codelingo.tui import TuiApp

NEW={'c','cpp','rust','typescript','web','ruby','lua','sql','php','perl'}

class LanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.courses={name:load_course(name) for name in NEW}

    def test_complete_curricula_and_randomized_variants(self):
        self.assertEqual({c['id'] for c in course_catalog()},NEW|{'python'})
        for name,c in self.courses.items():
            self.assertEqual(len(c.lessons),26 if name=='rust' else 20)
            self.assertEqual(len(c.questions),336 if name=='rust' else 240)
            sections=[l['section'] for l in c.lessons]
            rank={'Basics':0,'Intermediate':1,'Advanced':2}
            self.assertEqual(sections,sorted(sections,key=rank.get))
            self.assertEqual(set(sections),set(rank))
            self.assertTrue(all(5<=sections.count(s)<=12 for s in rank))
            self.assertTrue(all(12 <= len(l['questions']) <= 18 for l in c.lessons))
            self.assertTrue(all([q['kind'] for q in l['questions']]==['mcq']*(2*len(l['questions'])//3)+['write']*(len(l['questions'])//3) for l in c.lessons))
            for q in c.questions.values():
                variants=set()
                for seed in range(30):
                    sample=render(q,random.Random(seed)); variants.add(json.dumps(sample,sort_keys=True))
                    payload=json.dumps(sample)
                    self.assertNotIn('${',payload,(name,q['id']))
                    self.assertNotIn('__TILDE__',payload,(name,q['id']))
                    self.assertNotIn('\x00',sample.get('code',''))
                    answer=App.solution(sample)
                    self.assertTrue(check_answer(sample,answer),(name,q['id']))
                    self.assertFalse(check_answer(sample,'[incorrect]'))
                    if sample['kind']=='mcq':
                        self.assertEqual(len(set(sample['options'])),len(sample['options']))
                        self.assertTrue(all(sample['options']))
                if q.get('parameters'):self.assertGreater(len(variants),1,(name,q['id']))

    def test_every_course_completes_through_learning(self):
        for c in self.courses.values():
            store=Store(':memory:')
            try:
                app=App(c,store,Terminal(True),seed=9)
                for l in c.lessons:
                    self.assertTrue(app.unlocked(l))
                    app.begin_session('learn',l['questions'])
                    for q in l['questions']:
                        q=app.prepare_question(q);app.grade(q,App.solution(q),'learn')
                    self.assertTrue(store.is_complete(c.lesson_key(l['id'])))
                    self.assertEqual(app.progress.counts,(len(l['questions']),0,0))
                self.assertEqual(store.stats()['daily'],len(c.lessons))
            finally:store.close()

    def test_exams_unlock_only_selected_course_and_keep_hearts(self):
        for c in self.courses.values():
            store=Store(':memory:')
            try:
                store.db.execute('UPDATE player SET hearts=0');store.db.commit()
                with self.assertRaisesRegex(ValueError,'locked'):Exam(c,store,'Advanced',random.Random(1))
                for section in ('Basics','Intermediate','Advanced'):
                    exam=Exam(c,store,section,random.Random(1))
                    self.assertEqual(len(exam.questions),25)
                    self.assertEqual(len({q['id'] for q in exam.questions}),25)
                    for q in exam.questions:exam.submit(App.solution(q))
                    result=exam.finish();self.assertTrue(result['passed']);self.assertEqual(result['correct'],25)
                    self.assertEqual(store.player()['hearts'],0)
                    self.assertTrue(all(store.is_complete(c.lesson_key(l['id'])) for l in c.lessons if l['section']==section))
                self.assertEqual(store.stats()['daily'],3)
                self.assertFalse(store.is_complete('python:variables'))
            finally:store.close()

    def test_course_switch_preserves_isolated_mistakes_and_resumption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'progress.sqlite3';store=Store(path)
            app=App(self.courses['c'],store,Terminal(True),seed=1)
            q=app.prepare_question(app.course.lessons[0]['questions'][0]);app.grade(q,'wrong','learn')
            store.active_lesson('c','values');before=store.player()
            app.switch_course('cpp')
            self.assertEqual(store.mistakes(app.keys),[])
            self.assertFalse(store.passed('cpp:'+q['id']))
            self.assertIsNone(app.progress)
            self.assertEqual(store.player()['xp'],before['xp'])
            app.switch_course('c');self.assertEqual(len(store.mistakes(app.keys)),1)
            self.assertEqual(store.active_lesson('c'),'values')
            store.close();store=Store(path)
            self.assertEqual(store.selected_course(),'c');store.close()

    def test_tui_course_picker_switch_and_cancel(self):
        catalog=course_catalog();index=next(i for i,c in enumerate(catalog) if c['id']=='rust')
        class Picker:
            progress=None
            def choose(self,*args,**kwargs):return index
        store=Store(':memory:')
        try:
            picker=Picker();app=TuiApp(load_course(),store,picker,1)
            app.pick_course();self.assertEqual(app.course.id,'rust')
            self.assertEqual(store.selected_course(),'rust')
            picker.choose=lambda *args,**kwargs:None
            app.pick_course();self.assertEqual(app.course.id,'rust')
        finally:store.close()

    def test_cli_catalog_explicit_selection_and_saved_default(self):
        with tempfile.TemporaryDirectory() as tmp,contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['languages']),0)
            self.assertIn('typescript',output.getvalue())
            self.assertEqual(main(['--data-dir',tmp,'--course','lua','--plain','course']),0)
            output.seek(0);output.truncate(0)
            self.assertEqual(main(['--data-dir',tmp,'--plain','course']),0)
            self.assertIn('Lua',output.getvalue())
            with patch('builtins.input',return_value='1'):
                s=Store(':memory:');a=App(self.courses['c'],s,Terminal(True));a.pick_course();self.assertEqual(a.course.id,'python');s.close()

    def test_parameterized_non_python_writing_is_not_parsed_as_python(self):
        course=self.courses['c']
        q=next(q for q in course.questions.values() if q['kind']=='write' and q.get('parameters'))
        q=render(q,random.Random(3));self.assertTrue(check_answer(q,' '+q['accepted'][0]+' '))
        q={'kind':'write','checker':'exact','accepted':['"a b"']}
        self.assertFalse(check_answer(q,'"ab"'))
        self.assertFalse(check_answer(q,'"A b"'))

    def test_sql_answers_against_sqlite(self):
        course=self.courses['sql']
        for seed in (4,17,29):
            for q in course.questions.values():
                if '-read-' not in q['id']:continue
                q=render(q,random.Random(seed));expected=q['answer']
                db=sqlite3.connect(':memory:',isolation_level=None)
                try:
                    statements=[];buffer=''
                    for ch in q['code']:
                        buffer+=ch
                        if ch==';' and sqlite3.complete_statement(buffer):statements.append(buffer);buffer=''
                    if 'constraint error' in expected.lower():
                        with self.assertRaises(sqlite3.IntegrityError,msg=q['id']):
                            for statement in statements:db.execute(statement)
                        continue
                    for statement in statements:cursor=db.execute(statement,{'size':q.get('variant',{}).get('n',3)})
                    rows=cursor.fetchall()
                    result='; '.join(', '.join('NULL' if v is None else str(v) for v in row) for row in rows)
                    if q['id']=='select-read-3':result=cursor.description[0][0]
                    elif expected.startswith('One row containing '):expected=expected.removeprefix('One row containing ')
                    elif expected.startswith('Two rows containing '):value=expected.removeprefix('Two rows containing ');expected=value+'; '+value
                    elif expected=='Two rows, each containing 2':expected='2; 2'
                    self.assertEqual(result,expected,q['id'])
                finally:db.close()
