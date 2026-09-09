import random
import unittest

from codelingo.c_tokens import equivalent
from codelingo.course import check_answer,load_course
from codelingo.cli import App,Terminal
from codelingo.store import Store
from codelingo.templates import render

class CSpacingTests(unittest.TestCase):
    def test_spacing_between_tokens_is_ignored(self):
        for expected,answer in [('x + 6','x+6'),('x+6',' x \t+\n 6 '),
                ('std::move(a)','std :: move ( a )'),('const int *p','const int* p'),
                ('f(a, b);','f ( a ,b ) ;'),('a->value','a -> value')]:
            self.assertTrue(equivalent(answer,expected),(expected,answer))

    def test_literals_and_token_boundaries_remain_significant(self):
        for expected,answer in [('"a b"','"ab"'),("' '","''"),
                ('x + +6','x++6'),('int x','intx'),('x + 6','x + 7'),
                ('a >> b','a > > b'),('a && b','a & & b'),('1e+6','1e + 6'),
                ('1.0','1 . 0'),('L"x"','L "x"'),('"x"_tag','"x" _tag')]:
            self.assertFalse(equivalent(answer,expected),(expected,answer))

    def test_raw_strings_escapes_and_comments_are_preserved(self):
        self.assertTrue(equivalent('f ( R"tag(a b)tag" )','f(R"tag(a b)tag")'))
        self.assertFalse(equivalent('f(R"tag(ab)tag")','f(R"tag(a b)tag")'))
        self.assertFalse(equivalent(r'"a\nb"',r'"a nb"'))
        self.assertFalse(equivalent('x/* comment */+6','x+6'))
        self.assertFalse(equivalent('#define F(x) x','#define F (x) x'))
        self.assertFalse(equivalent('x+6; unwanted();','x+6'))
        self.assertFalse(equivalent('x'*2001,'x'*2001))

    def test_real_c_and_cpp_questions_accept_spacing_in_both_directions(self):
        for cid in ('c','cpp'):
            course=load_course(cid)
            q=render(course.questions['values-write-3'],random.Random(3))
            self.assertEqual(q['checker'],'c_tokens')
            self.assertTrue(check_answer(q,q['accepted'][0].replace(' ','')))
            q=render(course.questions['functions-write-1'],random.Random(3))
            self.assertTrue(check_answer(q,'x + 1'))
            self.assertFalse(check_answer(q,'x + 2'))
            self.assertEqual(course.questions['build-write-1']['checker'],'exact')

    def test_grading_does_not_deduct_a_heart_for_whitespace(self):
        for cid in ('c','cpp'):
            course=load_course(cid);store=Store(':memory:')
            try:
                app=App(course,store,Terminal(True),seed=2)
                q=app.prepare_question(course.questions['values-write-3'])
                before=store.player()['hearts']
                result=app.grade(q,q['accepted'][0].replace(' ',''),'learn')
                self.assertTrue(result['correct'])
                self.assertEqual(store.player()['hearts'],before)
                self.assertTrue(store.passed(course.key(q['id'])))
            finally:store.close()

    def test_other_checkers_keep_their_contract(self):
        self.assertFalse(check_answer({'kind':'write','checker':'exact','accepted':['x + 6']},'x+6'))
        self.assertFalse(check_answer({'kind':'mcq','answer':'a b'},'ab'))
        self.assertTrue(check_answer({'kind':'write','checker':'python_ast','accepted':['x + 6']},'x+6'))
