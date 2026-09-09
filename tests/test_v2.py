import contextlib
from collections import Counter
import copy
import io
import json
from pathlib import Path
import random
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from codelingo.course import load_course, check_answer
from codelingo.templates import render, expression
from codelingo.store import Store
from codelingo.exams import Exam, passes
from codelingo.cli import App, Terminal
from codelingo.tui import Screen, header_parts, TuiApp


class UpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.course = load_course()

    def setUp(self):
        self.store = Store(':memory:', lambda: 1788955200)

    def tearDown(self):
        self.store.close()

    def test_lesson_sizes_and_variant_schema(self):
        self.assertEqual(len(self.course.questions),216)
        self.assertTrue(all(len(l['questions']) == 12 for l in self.course.lessons))
        templates = [q for q in self.course.questions.values() if q.get('parameters')]
        self.assertEqual(len(templates),126)
        for q in templates:
            seen = set()
            for seed in range(100):
                instance = render(q,random.Random(seed))
                seen.add(json.dumps(instance,sort_keys=True))
                for field in ('code','prompt','explanation','hint'):
                    self.assertNotIn('${',instance[field],q['id'])
                if instance['kind'] == 'mcq':
                    self.assertEqual(len(set(instance['options'])),len(instance['options']))
                    self.assertTrue(check_answer(instance,instance['answer']))
                else:
                    for answer in instance['accepted']:
                        self.assertTrue(check_answer(instance,answer),q['id'])
            self.assertGreater(len(seen),1,q['id'])

    def test_template_expression_is_not_an_execution_engine(self):
        for source in ('__import__("os")','x.__class__','[i for i in x]','open("file")','2 ** 100000','"x" * 1000000'):
            with self.subTest(source=source), self.assertRaises((ValueError,SyntaxError)):
                expression(source,{'x':'hello'})
        self.assertEqual(expression('a+b*2',{'a':3,'b':4}),11)
        self.assertEqual(expression('repr(word)',{'word':"can't"}), '"can\'t"')

    def test_collision_retry_and_reproducible_seed(self):
        q=self.course.questions['arithmetic-v1']
        self.assertEqual(render(q,random.Random(5)),render(q,random.Random(5)))
        broken=copy.deepcopy(q)
        broken['options']=['same','same']
        broken['answer']='same'
        with self.assertRaisesRegex(ValueError,'distinct'):
            render(broken,random.Random(0))

    def test_review_keeps_actual_snapshot_but_draws_new_variant(self):
        app=App(self.course,self.store,Terminal(True),seed=9)
        q=self.course.questions['variables-v1']
        first=app.prepare_question(q)
        app.grade(first,'wrong','learn')
        second=app.prepare_question(q)
        self.assertNotEqual(first['variant'],second['variant'])
        row=self.store.mistakes(app.keys)[0]
        self.assertEqual(json.loads(row['last_wrong_snapshot']),first)
        app.grade(second,second['answer'],'review')
        self.assertEqual(self.store.player()['gems'],2)
        third=app.prepare_question(q)
        result=app.grade(third,third['answer'],'review')
        self.assertEqual(result['xp'],0)
        self.assertEqual(result['gems'],0)

    def test_legacy_database_migrates_without_losing_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'old.sqlite3'
            db=sqlite3.connect(path)
            db.executescript('''
            CREATE TABLE player(id INTEGER PRIMARY KEY,hearts INTEGER,heart_at REAL,xp INTEGER,best_combo INTEGER);
            INSERT INTO player VALUES(1,3,1788955200,280,7);
            CREATE TABLE completed(lid TEXT PRIMARY KEY,at REAL);
            INSERT INTO completed VALUES('python:variables',1788955200);
            CREATE TABLE progress(qid TEXT PRIMARY KEY,passed INTEGER DEFAULT 0,attempts INTEGER DEFAULT 0,errors INTEGER DEFAULT 0,last_wrong TEXT,last_seen REAL);
            INSERT INTO progress VALUES('python:variables-1',1,2,1,'4',1788955200);
            CREATE TABLE attempts(id INTEGER PRIMARY KEY,qid TEXT,at REAL,answer TEXT,correct INTEGER,mode TEXT);
            INSERT INTO attempts VALUES(1,'python:variables-1',1788955200,'9',1,'learn');
            ''')
            db.close()
            migrated=Store(path,lambda:1788955200)
            self.assertEqual(migrated.player()['xp'],280)
            self.assertEqual(migrated.player()['gems'],0)
            self.assertEqual(migrated.player()['hearts'],3)
            self.assertTrue(migrated.passed('python:variables-1'))
            self.assertEqual(migrated.completion_origin('python:variables'),'learn')
            migrated.close()
            migrated=Store(path,lambda:1788955200)
            self.assertEqual(migrated.player()['xp'],280)
            migrated.close()

    def answer_exam(self,section='Basics',correct=25,seed=1):
        exam=Exam(self.course,self.store,section,random.Random(seed))
        for i,q in enumerate(exam.questions):
            answer=q['answer'] if q['kind']=='mcq' else q['accepted'][0]
            self.assertIsNone(exam.submit(answer if i<correct else '[wrong]'))
        result=exam.finish()
        exam.save_attempts()
        return exam,result

    def test_exact_80_fails_and_84_passes(self):
        self.assertFalse(passes(20,25))
        self.assertTrue(passes(21,25))
        exam,result=self.answer_exam(correct=20)
        self.assertFalse(result['passed'])
        self.assertFalse(self.store.is_complete('python:variables'))
        self.assertEqual(self.store.player()['xp'],0)
        self.assertEqual(self.store.player()['hearts'],5)
        exam,result=self.answer_exam(correct=21,seed=2)
        self.assertTrue(result['passed'])
        self.assertTrue(self.store.is_complete('python:conditions'))
        self.assertEqual(self.store.completion_origin('python:variables'),'exam')
        self.assertFalse(self.store.passed('python:variables-1'))
        self.assertEqual(self.store.player()['xp'],50)
        self.assertEqual(self.store.player()['gems'],20)
        _,again=self.answer_exam(seed=3)
        self.assertFalse(again['rewarded'])
        self.assertEqual(self.store.player()['gems'],20)

    def test_balanced_exams_all_sections_have_25_and_writing(self):
        for section in ('Basics','Intermediate','Advanced','Specialized'):
            exam,result=self.answer_exam(section)
            self.assertEqual(len(exam.questions),25)
            self.assertEqual(len({q['id'] for q in exam.questions}),25)
            counts=Counter(self.course.lesson_for[q['id']]['id'] for q in exam.questions)
            self.assertLessEqual(max(counts.values())-min(counts.values()),1)
            for lid in counts:
                kinds={q['kind'] for q in exam.questions if self.course.lesson_for[q['id']]['id']==lid}
                self.assertEqual(kinds,{'mcq','write'})
            self.assertTrue(result['passed'])

    def test_incomplete_exam_never_unlocks_and_answer_logging_is_idempotent(self):
        with self.assertRaisesRegex(ValueError,'prerequisites'):
            Exam(self.course,self.store,'Advanced',random.Random(0))
        exam=Exam(self.course,self.store,'Basics',random.Random(0))
        exam.submit('[wrong]')
        with self.assertRaisesRegex(ValueError,'Finish all'):
            exam.finish()
        exam.abort()
        exam.save_attempts()
        exam.save_attempts()
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],1)
        self.assertEqual(self.store.db.execute('SELECT state FROM exams').fetchone()[0],'abandoned')
        self.assertFalse(self.store.is_complete('python:variables'))
        with self.assertRaises(ValueError):
            exam.submit('answer')

    def test_gem_shop_transactions(self):
        self.store.record('a','wrong',False,'learn')
        self.assertIn('need 10',self.store.buy_heart())
        for i in range(5):
            self.store.record(str(i),'right',True,'learn')
        self.assertEqual(self.store.player()['gems'],10)
        self.assertIn('restored',self.store.buy_heart())
        self.assertEqual(self.store.player()['hearts'],5)
        self.assertEqual(self.store.player()['gems'],0)
        self.assertIn('already full',self.store.buy_heart())

    def test_generated_core_examples_match_real_python(self):
        # Run a bounded sample of authored variants, not learner answers.
        ids=['variables-v1','variables-v2','variables-v3','variables-v6',
             'arithmetic-v1','arithmetic-v2','arithmetic-v3','arithmetic-v6',
             'input-v1','input-v2','input-v3','input-v6',
             'strings-v1','strings-v2','strings-v3','strings-v6',
             'conditions-v1','conditions-v2','conditions-v3',
             'containers-v1','containers-v2','containers-v3','containers-v6',
             'functions-v1','functions-v3','functions-v6',
             'modules-v1','modules-v6','errors-v1','errors-v2',
             'mutation-v1','mutation-v2','mutation-v3','mutation-v6',
             'classes-v1','classes-v2','classes-v6',
             'iteration-v1','iteration-v2','iteration-v3','iteration-v6',
             'decorators-v1','decorators-v3']
        for qid in ids:
            for seed in (3,19,71):
                q=render(self.course.questions[qid],random.Random(seed))
                run=subprocess.run([sys.executable,'-I','-c',q['code']],capture_output=True,text=True,timeout=5)
                self.assertEqual(run.returncode,0, qid+run.stderr)
                self.assertEqual(run.stdout.strip(),q['answer'],qid)


class FakeCurses:
    class error(Exception):pass
    A_REVERSE=1;A_BOLD=2
    KEY_DOWN=1001;KEY_UP=1002;KEY_ENTER=1003;KEY_NPAGE=1004;KEY_PPAGE=1005
    KEY_BACKSPACE=1006;KEY_DC=1007;KEY_LEFT=1008;KEY_RIGHT=1009;KEY_HOME=1010;KEY_END=1011
    def has_colors(self):return False
    def curs_set(self,flag):pass


class FakeWindow:
    def __init__(self,keys,size=(24,80)):
        self.keys=iter(keys);self.size=size;self.rows={};self.frames=[]
    def keypad(self,value):pass
    def timeout(self,value):pass
    def getmaxyx(self):return self.size
    def erase(self):self.rows={}
    def addnstr(self,y,x,text,n,style):
        row=self.rows.get(y,' '*self.size[1]);text=text[:n]
        self.rows[y]=row[:x]+text+row[x+len(text):]
    def refresh(self):self.frames.append(dict(self.rows))
    def move(self,y,x):pass
    def get_wch(self):return next(self.keys)


class TuiTests(unittest.TestCase):
    def setUp(self):self.store=Store(':memory:');self.c=FakeCurses()
    def tearDown(self):self.store.close()

    def test_arrow_menu_and_pinned_balances(self):
        window=FakeWindow([self.c.KEY_DOWN,self.c.KEY_DOWN,self.c.KEY_UP,'\n'])
        screen=Screen(window,self.store,self.c)
        self.assertEqual(screen.choose('Menu','Welcome',['One','Two','Three']),1)
        for frame in window.frames:
            self.assertIn('EXP',frame[0]);self.assertIn('gems',frame[0])
            self.assertIn('♥♥♥♥♥',frame[0]);self.assertTrue(frame[0].index('EXP')<frame[0].index('♥'))

    def test_scroll_does_not_change_selection(self):
        window=FakeWindow([self.c.KEY_NPAGE,self.c.KEY_DOWN,'\n'],(18,60))
        screen=Screen(window,self.store,self.c)
        self.assertEqual(screen.choose('Question','\n'.join('line '+str(i) for i in range(50)),['A','B','C','D']),1)
        self.assertTrue(any('line 6' in ''.join(f.values()) for f in window.frames))

    def test_input_editing_and_escape(self):
        window=FakeWindow(['a','c',self.c.KEY_LEFT,'b',self.c.KEY_END,'x',self.c.KEY_BACKSPACE,'\n'])
        self.assertEqual(Screen(window,self.store,self.c).edit('Write','Write abc'),'abc')
        self.assertIsNone(Screen(FakeWindow(['\x1b']),self.store,self.c).edit('Write','Body'))

    def test_small_terminal_still_allows_exit(self):
        screen=Screen(FakeWindow(['q'],(8,25)),self.store,self.c)
        self.assertIsNone(screen.choose('Menu','Body',['One']))

    def test_exam_ui_does_not_offer_hint(self):
        class StubScreen:
            def page(self,*args):return True
            def choose(self,title,body,options,**kwargs):
                self.kwargs=kwargs
                return 0
        stub=StubScreen();app=TuiApp(load_course(),self.store,stub,1)
        q=render(app.course.questions['variables-v1'],random.Random(0))
        self.assertIn(app.exam_answer(q,1,25),q['options'])
        self.assertFalse(stub.kwargs['hint'])


if __name__=='__main__':unittest.main()
