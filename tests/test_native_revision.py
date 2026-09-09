"""Regression gates for authored course evolution and existing profiles."""
import hashlib
import json
from pathlib import Path
import random
import unittest

from codelingo.cli import App,Terminal
from codelingo.course import load_course
from codelingo.exams import Exam
from codelingo.store import Store

BASE=json.loads((Path(__file__).parent/'fixtures/v1_course_ids.json').read_text())
FIELDS=('kind','code','prompt','answer','options','accepted','checker','parameters','derived')

class NativeRevisionTests(unittest.TestCase):
    def test_retained_ids_keep_their_exercise_meaning(self):
        for cid,old in BASE.items():
            c=load_course(cid)
            self.assertTrue(set(old['lessons'])<=set(c.by_id),cid)
            for qid,digest in old['questions'].items():
                if qid not in c.questions:
                    self.assertTrue('-choose-' in qid or '-write-' in qid,(cid,qid))
                    new_id=qid.replace('-choose-','-choose-repair-').replace('-write-','-write-repair-')
                    self.assertIn(new_id,c.questions,(cid,qid))
                    continue
                q=c.questions[qid]
                actual=hashlib.sha256(json.dumps({k:q[k] for k in FIELDS if k in q},sort_keys=True).encode()).hexdigest()
                self.assertEqual(actual,digest,(cid,qid))

    def test_error_reading_leads_to_a_successful_repair(self):
        error_prefixes=('Compile error','Link error','Type error','TypeError:','Error:','ReferenceError:',
                        'Undefined behavior','Throws','Raises','FrozenError','Constraint error',
                        'Unique constraint error','Foreign-key constraint error')
        for cid in BASE:
            c=load_course(cid)
            errors=[q for q in c.questions.values() if '-read-' in q['id'] and q['answer'].startswith(error_prefixes)]
            self.assertTrue(errors,cid)
            for q in errors:
                repair=c.questions[q['repair_question_id']]
                self.assertIn('Repair the code',repair['prompt'])
                self.assertFalse(repair['target_answer'].startswith(error_prefixes),(cid,q['id']))
                self.assertNotIn('____',repair['code'].replace('____',repair['accepted'][0]))

    def test_old_history_survives_and_new_topics_start_unfinished(self):
        for cid,old in BASE.items():
            c=load_course(cid);store=Store(':memory:')
            try:
                for lid in old['lessons']:
                    store.db.execute('INSERT INTO completed(lid,at) VALUES(?,?)',(c.lesson_key(lid),store.clock()))
                store.db.commit()
                repaired=[q for q in c.questions.values() if q.get('repair_question_id') and q['id'] in old['questions']]
                read=repaired[0] if repaired else next(q for q in c.questions.values() if '-read-' in q['id'] and q['id'] in old['questions'])
                if repaired:
                    retired=read['id'].replace('-read-','-write-')
                    self.assertNotIn(retired,c.questions)
                else:
                    retired=next(qid for qid in old['questions'] if '-write-' in qid and c.lesson_for[qid]['id']!=c.lesson_for[read['id']]['id'])
                store.record(c.key(read['id']),'old wrong answer',False,'learn',snapshot=read)
                store.record(c.key(retired),'old stored answer',True,'learn')
                before=dict(store.stats())
                app=App(c,store,Terminal(True),seed=2)
                new_ids=set(c.by_id)-set(old['lessons'])
                self.assertEqual(len(new_ids),6)
                self.assertTrue(all(store.is_complete(c.lesson_key(lid)) for lid in old['lessons']))
                self.assertFalse(any(store.is_complete(c.lesson_key(lid)) for lid in new_ids))
                self.assertEqual(dict(store.stats()),before)
                self.assertEqual(store.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],2)
                app.begin_session('learn',c.lesson_for[read['id']]['questions'])
                self.assertEqual(app.progress.counts,(0,1,11))
                self.assertEqual(len(store.mistakes(app.keys)),1)
                exam=Exam(c,store,'Basics',random.Random(1))
                hearts=store.player()['hearts']
                for q in exam.questions:exam.submit(App.solution(q))
                self.assertTrue(exam.finish()['passed'])
                self.assertEqual(store.player()['hearts'],hearts)
                self.assertTrue(all(store.is_complete(c.lesson_key(l['id'])) for l in c.lessons if l['section']=='Basics'))
            finally:store.close()

    def test_native_dependencies_and_sources(self):
        pairs={'c':('pointers','memory'),'cpp':('ownership','value-semantics'),
               'lua':('functions','results'),'ruby':('methods','keywords'),
               'perl':('context','text-pipeline'),'php':('validation','database'),
               'typescript':('validation','async-boundaries'),'web':('semantics','events'),
               'sql':('null-logic','join-boundaries')}
        for cid,(before,after) in pairs.items():
            c=load_course(cid);ids=list(c.by_id)
            self.assertLess(ids.index(before),ids.index(after))
            refs={s['id']:s['url'] for s in c.data['sources']}
            for lid in set(ids)-set(BASE[cid]['lessons']):
                self.assertTrue(c.by_id[lid]['sources'])
                self.assertTrue(all(refs[s].startswith('https://') for s in c.by_id[lid]['sources']))
                self.assertNotEqual(c.by_id[lid]['section'],'Specialized')
