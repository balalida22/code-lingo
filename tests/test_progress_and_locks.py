import contextlib
import io
import random
import unittest
from unittest.mock import patch

from codelingo.cli import App, Terminal, LeaveSession
from codelingo.course import load_course
from codelingo.progress import SessionProgress
from codelingo.store import Store
from codelingo.tui import TuiApp, Screen, STATUS_COLORS
from test_v2 import FakeWindow, FakeCurses


class ProgressAndLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.course = load_course()

    def setUp(self):
        self.store = Store(':memory:', lambda: 1788955200)
        self.app = App(self.course, self.store, Terminal(True), 7)

    def tearDown(self):
        self.store.close()

    def test_distinct_progress_and_correction(self):
        p = SessionProgress('learn', [{'id':str(n)} for n in range(25)])
        for n in range(10):
            p.mark(str(n), True)
        p.mark('10',False); p.mark('11',False)
        self.assertEqual(p.counts,(10,2,13))
        self.assertEqual(p.percent,48)
        p.mark('10',False)
        self.assertEqual(p.counts,(10,2,13))
        p.mark('10',True)
        self.assertEqual(p.counts,(11,1,13))
        p.mark('unrelated',True)
        self.assertEqual(sum(p.counts),25)

    def test_resume_and_review_do_not_mix_counts(self):
        lesson = self.course.lessons[0]
        q1,q2 = lesson['questions'][:2]
        self.store.record(self.course.key(q1['id']),'right',True,'learn')
        self.store.record(self.course.key(q2['id']),'wrong',False,'learn')
        self.app.begin_session('learn',lesson['questions'])
        self.assertEqual(self.app.progress.counts,(1,1,10))
        self.app.begin_session('review',[q2])
        self.assertEqual(self.app.progress.counts,(0,0,1))
        self.app.begin_session('learn',lesson['questions'])
        self.assertEqual(self.app.progress.counts,(1,1,10))

    def test_draw_counts_colors_and_progress_after_daily_goal(self):
        p = SessionProgress('exam',[{'id':str(n)} for n in range(25)])
        for n in range(10):p.mark(str(n),True)
        p.mark('10',False);p.mark('11',False)
        class StyledWindow(FakeWindow):
            def __init__(self):super().__init__([]);self.calls=[]
            def addnstr(self,y,x,text,n,style):
                self.calls.append((y,text,style))
                super().addnstr(y,x,text,n,style)
        win=StyledWindow();screen=Screen(win,self.store,FakeCurses())
        screen.progress=p;screen.color=lambda n:n*16
        screen.frame('Exam')
        self.assertIn('10/2/13',win.rows[0])
        self.assertIn('48%',win.rows[0])
        self.assertIn((0,'10',32|FakeCurses.A_BOLD),win.calls)
        self.assertIn((0,'2',64|FakeCurses.A_BOLD),win.calls)
        self.assertIn((0,'13',0),win.calls)
        p.mark('12',True);screen.frame('Exam')
        self.assertIn('11/2/12',win.rows[0])
        self.assertIn('52%',win.rows[0])

    def test_daily_header_only_on_main_menu_and_progress_replaces_it(self):
        for width in (60, 80, 120):
            win = FakeWindow([], (24, width))
            screen = Screen(win, self.store, FakeCurses())
            screen.frame('Main menu', main_menu=True)
            self.assertIn('streak', win.rows[0])
            self.assertIn('today', win.rows[0])
            screen.frame('Choose a lesson')
            self.assertNotIn('streak', win.rows[0])
            self.assertNotIn('today', win.rows[0])
            for mode in ('learn', 'exam'):
                screen.progress = SessionProgress(mode, [{'id':str(n)} for n in range(25)])
                screen.progress.mark('0', True)
                screen.progress.mark('1', False)
                screen.frame(mode)
                self.assertIn('1/1/23', win.rows[0])
                self.assertIn('░', win.rows[0])
                self.assertIn('EXP', win.rows[0])
                self.assertIn('gems', win.rows[0])
                self.assertIn('♥♥♥♥♥', win.rows[0])
                self.assertNotIn('streak', win.rows[0])
                self.assertNotIn('today', win.rows[0])
                self.assertNotIn('1/1/23', win.rows[1])
            screen.progress = None
            screen.frame('Main menu', main_menu=True)
            self.assertIn('today', win.rows[0])

    def test_locked_lesson_returns_to_picker_without_mutation(self):
        class Picker:
            def __init__(self):self.selections=iter([1,None]);self.pages=[];self.statuses=[]
            def choose(self,*args,**kwargs):
                self.statuses.append(kwargs['statuses'])
                return next(self.selections)
            def page(self,title,body):self.pages.append((title,body));return True
        picker=Picker();tui=TuiApp(self.course,self.store,picker,1)
        tui.pick_lesson()
        self.assertEqual(picker.pages[0][0],'Lesson locked')
        self.assertIn(self.course.lessons[0]['title'],picker.pages[0][1])
        self.assertEqual(picker.statuses[0][1],'LOCK')
        self.assertIsNone(self.store.active_lesson(self.course.id))
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM attempts').fetchone()[0],0)

    def test_locked_exam_returns_to_picker_without_creating_exam(self):
        class Picker:
            def __init__(self):self.selections=iter([1,None]);self.pages=[]
            def choose(self,*args,**kwargs):return next(self.selections)
            def page(self,title,body):self.pages.append((title,body));return True
        picker=Picker();tui=TuiApp(self.course,self.store,picker,1)
        tui.pick_exam()
        self.assertEqual(picker.pages[0][0],'Exam locked')
        self.assertIn('Branches and truthiness',picker.pages[0][1])
        self.assertEqual(self.store.db.execute('SELECT COUNT(*) FROM exams').fetchone()[0],0)

    def test_locked_exam_plain_menu_stays_open(self):
        with patch('builtins.input',side_effect=['8','Advanced','q']),contextlib.redirect_stdout(io.StringIO()) as out:
            self.app.menu()
        self.assertIn('Exam locked',out.getvalue())
        self.assertEqual(out.getvalue().count('Read code. Build fluency.'),2)

    def test_all_exam_misses_and_skips_leave_hearts_unchanged(self):
        self.store.db.execute('UPDATE player SET hearts=3 WHERE id=1');self.store.db.commit()
        self.app.exam_answer=lambda q,index,total:'[skipped]' if index%2 else '[wrong]'
        with contextlib.redirect_stdout(io.StringIO()):self.app.exam('Basics')
        self.assertEqual(self.store.player()['hearts'],3)
        self.assertEqual(self.app.progress.counts,(0,25,0))
        self.assertTrue(all(not self.store.is_complete(self.course.lesson_key(l['id'])) for l in self.course.lessons[:5]))

    def test_passing_exam_marks_entire_section_done_even_at_zero_hearts(self):
        self.store.db.execute('UPDATE player SET hearts=0 WHERE id=1');self.store.db.commit()
        self.app.exam_answer=lambda q,index,total:self.app.solution(q)
        with contextlib.redirect_stdout(io.StringIO()):self.app.exam('Basics')
        self.assertEqual(self.store.player()['hearts'],0)
        self.assertEqual(self.app.progress.counts,(25,0,0))
        for lesson in self.course.lessons[:5]:
            self.assertTrue(self.store.is_complete(self.course.lesson_key(lesson['id'])))
            self.assertEqual(self.app.lesson_status(lesson),'DONE')
        self.assertTrue(self.app.unlocked(self.course.lessons[5]))
        self.assertEqual(STATUS_COLORS['DONE'],2)
        self.assertEqual(STATUS_COLORS['LOCK'],4)

    def test_tui_status_colors_survive_selection_highlight(self):
        class StyledWindow(FakeWindow):
            def __init__(self):super().__init__(['\n']);self.calls=[]
            def addnstr(self,y,x,text,n,style):
                self.calls.append((text,style));super().addnstr(y,x,text,n,style)
        win=StyledWindow();screen=Screen(win,self.store,FakeCurses());screen.color=lambda n:n*16
        screen.choose('Lessons','Legend',['[DONE] a','[LOCK] b'],statuses=['DONE','LOCK'])
        self.assertTrue(any('[DONE]' in t and s==(32|3) for t,s in win.calls))
        self.assertTrue(any('[LOCK]' in t and s==64 for t,s in win.calls))

    def test_tui_clears_session_progress_on_quit(self):
        class Picker:
            progress=None
            def page(self,*args):return True
        picker=Picker();tui=TuiApp(self.course,self.store,picker,1)
        def action():
            tui.begin_session('learn',self.course.lessons[0]['questions'])
            raise LeaveSession
        tui.action(action)
        self.assertIsNone(picker.progress)
        self.assertIsNone(tui.progress)


if __name__=='__main__':unittest.main()
