import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from codelingo.cli import App,Terminal
from codelingo.course import load_course,course_catalog
from codelingo.store import Store
from codelingo.tui import Screen,StyledBody,TuiApp
from test_v2 import FakeCurses,FakeWindow

class ReadabilityTests(unittest.TestCase):
    def test_pin_persistence_and_no_progress_changes(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'progress.db'
            store=Store(path,lambda:1788955200)
            before=store.stats()
            self.assertTrue(store.toggle_course_pin('rust'))
            self.assertTrue(store.toggle_course_pin('sql'))
            self.assertEqual(store.stats(),before)
            store.close()
            store=Store(path,lambda:1788955200)
            try:
                self.assertEqual(store.pinned_courses(),{'rust','sql'})
                self.assertFalse(store.toggle_course_pin('rust'))
                self.assertEqual(store.pinned_courses(),{'sql'})
                self.assertEqual(store.selected_course(),'python')
            finally:store.close()

    def test_picker_reorders_pins_keeps_focus_and_only_switches_on_enter(self):
        store=Store(':memory:')
        app=None
        class Picker:
            progress=None
            calls=0
            def choose(self,title,body,labels,**kwargs):
                self.calls+=1
                if self.calls==1:
                    self.rust=next(i for i,s in enumerate(labels) if s.startswith('Rust:'))
                    return ('pin',self.rust)
                assert labels[0].startswith('★ Rust:')
                assert kwargs['initial']==0
                assert app.course.id=='python'
                return 0
        try:
            app=TuiApp(load_course(),store,Picker(),1)
            app.pick_course()
            self.assertEqual(app.course.id,'rust')
            self.assertEqual(store.pinned_courses(),{'rust'})
        finally:store.close()

    def test_pin_shortcut_and_scroll_hint_only_on_overflow(self):
        store=Store(':memory:')
        try:
            window=FakeWindow(['p'])
            screen=Screen(window,store,FakeCurses())
            self.assertEqual(screen.choose('Languages','Short text',['Python','Rust'],pin=True),('pin',0))
            text='\n'.join(window.frames[-1].values())
            self.assertNotIn('text line',text)
            self.assertNotIn('More text',text)
            self.assertIn('p pin/unpin',text)
            window=FakeWindow([FakeCurses.KEY_NPAGE,'\n'],(18,60))
            screen=Screen(window,store,FakeCurses())
            screen.page('Explanation','\n'.join(f'Explanation {i}' for i in range(40)))
            self.assertIn('More text','\n'.join(window.frames[-1].values()))
            self.assertNotEqual(window.frames[0][4],window.frames[1][4])
        finally:store.close()

    def test_wrapped_scrolled_explanation_keeps_distinct_style(self):
        class Curses(FakeCurses):A_DIM=4
        class Window(FakeWindow):
            def __init__(self):super().__init__([]);self.styles=[]
            def addnstr(self,y,x,text,n,style):self.styles.append((text,style))
        store=Store(':memory:')
        try:
            window=Window();screen=Screen(window,store,Curses())
            screen.color=lambda index:16*index
            body=StyledBody('general prompt','muted')+StyledBody('\n\nExplanation across wrapped lines','explanation')
            lines=screen.wrapped(body,12)
            screen.body(lines,4,20,0)
            self.assertTrue(all(style==4 for text,style in window.styles if text.startswith(('general','prompt'))))
            self.assertTrue(any(style==18 for text,style in window.styles if 'Explanation' in text))
            self.assertEqual({role for text,role in lines if text.strip() and 'general' not in text and text.strip()!='prompt'},{'explanation'})
        finally:store.close()

    def test_plain_picker_shares_pins(self):
        store=Store(':memory:')
        try:
            index=next(i for i,c in enumerate(course_catalog(),1) if c['id']=='sql')
            app=App(load_course(),store,Terminal(True),1)
            with patch('builtins.input',side_effect=[f'p {index}','1']),contextlib.redirect_stdout(io.StringIO()):
                app.pick_course()
            self.assertEqual(app.course.id,'sql')
            self.assertEqual(store.pinned_courses(),{'sql'})
        finally:store.close()
