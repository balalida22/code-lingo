"""Regressions for the six new tracks' native content and integration."""
import random
import unittest
from codelingo.course import load_course, check_answer
from codelingo.templates import render
from codelingo.store import Store
from codelingo.cli import App, Terminal


class AddedCourseTests(unittest.TestCase):
    def test_shell_parameter_syntax_survives_randomization(self):
        c=load_course('bash')
        cases={
            'expansion-read-1':'${name:-',
            'expansion-read-3':'${name%.txt}',
            'arrays-read-1':'${items[@]}',
            'patterns-read-3':'${BASH_REMATCH[1]}',
        }
        for qid,literal in cases.items():
            for seed in range(10):
                q=render(c.questions[qid],random.Random(seed))
                self.assertIn(literal,q['code'])
                self.assertNotIn('${word}',q['code'])
                self.assertNotIn('${n}',q['code'])

    def test_error_identification_has_a_valid_repair(self):
        c=load_course('java')
        broken=c.questions['values-read-4']
        fixed=c.questions[broken['repair_question_id']]
        self.assertEqual(fixed['kind'],'write')
        q=render(fixed,random.Random(4))
        self.assertTrue(check_answer(q,q['accepted'][0]))
        self.assertNotIn('final int',q['code'])
        self.assertIn('Target result:',q['prompt'])

    def test_tracks_have_distinct_native_advanced_topics(self):
        landmarks={
            'java':{'records','streams','optional','futures'},
            'go':{'slices','defer','goroutines','channels','context'},
            'csharp':{'properties','records','linq','delegates','cancellation'},
            'bash':{'quoting','redirection','subshells','traps','processes'},
            'kotlin':{'nulls','smartcasts','extensions','scope','suspension'},
            'swift':{'value-types','guard','protocols','arc','actors'},
        }
        for cid,ids in landmarks.items():
            course=load_course(cid)
            self.assertTrue(ids<=set(course.by_id))
            self.assertFalse(any(l['section']=='Specialized' for l in course.lessons))
            self.assertTrue(all(l['sources'] for l in course.lessons))

    def test_new_tracks_share_pins_but_keep_review_and_learning_separate(self):
        store=Store(':memory:')
        self.addCleanup(store.close)
        app=App(load_course('java'),store,Terminal(True),4)
        q=app.prepare_question(app.course.questions['values-read-1'])
        app.grade(q,App.solution(q),'learn')
        store.toggle_course_pin('java')
        for cid in ('go','csharp','bash','kotlin','swift'):
            app.switch_course(cid)
            self.assertEqual(store.due(app.keys,early=True),[])
            self.assertIn('java',store.pinned_courses())
            self.assertEqual(store.selected_course(),cid)
        app.switch_course('java')
        self.assertIn('java:values-read-1',store.due(app.keys,early=True))
