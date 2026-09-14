"""Curses TUI with pinned stats, scrolling content, and keyboard selection."""
import contextlib
import io
import os
import sys
import textwrap
import sqlite3

from .cli import App, Terminal, LeaveSession
from .store import DAILY_GOAL
from .exams import section_requirements

STATUS_COLORS = {'DONE': 2, 'OPEN': 1, 'ACTIVE': 3, 'LOCK': 4}

class StyledBody(str):
    """Text with semantic spans; stays usable by plain-text screen doubles."""
    def __new__(cls, text, role='normal', spans=None):
        value=super().__new__(cls,text)
        value.spans=spans if spans is not None else [(0,len(text),role)]
        return value

    def __add__(self, other):
        spans=getattr(other,'spans',[(0,len(other),'normal')])
        return StyledBody(str(self)+str(other),spans=self.spans+[(a+len(self),b+len(self),r) for a,b,r in spans])


def header_parts(stats, width, main_menu=False):
    left = f" EXP {stats['xp']}   ◆ {stats['gems']} gems"
    right = '♥' * stats['hearts'] + '♡' * (5 - stats['hearts']) + f" {stats['hearts']}/5 "
    center = f"{stats['streak']} day streak · {min(stats['daily'], DAILY_GOAL)}/{DAILY_GOAL} today" if main_menu else ''
    if len(left) + len(right) + len(center) + 4 > width:
        center = ''
    return left, center, right


class Screen:
    def __init__(self, window, store, curses):
        self.win, self.store, self.c = window, store, curses
        self.progress = None
        window.keypad(True)
        window.timeout(1000)
        self.colors = False
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            curses.init_pair(1, curses.COLOR_CYAN, -1)
            curses.init_pair(2, curses.COLOR_GREEN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
            curses.init_pair(4, curses.COLOR_RED, -1)
            self.colors = True
        self.cursor(False)

    def cursor(self, enabled):
        try:
            self.c.curs_set(int(enabled))
        except self.c.error:
            pass

    def color(self, index):
        return self.c.color_pair(index) if self.colors else 0

    def put(self, y, x, text, style=0):
        h, w = self.win.getmaxyx()
        if not (0 <= y < h and 0 <= x < w):
            return
        # Bound terminal rendering and remove control characters from content.
        text = ''.join(ch if ch.isprintable() else ' ' for ch in str(text))
        try:
            self.win.addnstr(y, x, text, max(0, w-x-1), style)
        except self.c.error:
            pass

    def frame(self, title, main_menu=False, title_color=1):
        self.win.erase()
        h, w = self.win.getmaxyx()
        if h < 18 or w < 60:
            self.put(0, 0, 'Resize terminal to at least 60 columns x 18 rows.')
            self.put(2, 0, 'Esc or q goes back. Progress is saved.')
            self.win.refresh()
            return None
        s = self.store.stats()
        left, center, right = header_parts(s, w, main_menu)
        self.put(0, 0, ' ' * (w-1), self.c.A_REVERSE)
        self.put(0, 0, left, self.c.A_BOLD | self.color(3))
        if self.progress:
            start = len(left) + 2
            self.draw_progress(start, w-len(right)-2-start)
        elif center:
            # Center in the space between the left and right balances.
            start = len(left) + (w-len(left)-len(right)-len(center))//2
            self.put(0, start, center, self.color(1))
        self.put(0, w-len(right)-1, right, self.color(4) | self.c.A_BOLD)
        self.put(1, 0, '─' * (w-1), self.color(1))
        self.put(2, 2, title, self.c.A_BOLD | self.color(title_color))
        return h, w

    def draw_progress(self, start, width):
        correct, wrong, remaining = self.progress.counts
        label = 'Correct/Wrong/Left ' if width >= 45 else 'C/W/L '
        self.put(0, start, label)
        x = start + len(label)
        for text, style in ((str(correct), self.color(2) | self.c.A_BOLD), ('/', 0),
                            (str(wrong), self.color(4) | self.c.A_BOLD), ('/', 0),
                            (str(remaining), 0)):
            self.put(0, x, text, style)
            x += len(text)
        self.put(0, x, ' [')
        x += 2
        cells = max(1, start+width-x-6)
        total = self.progress.total or 1
        green = cells*correct//total
        filled = cells*(correct+wrong)//total
        self.put(0, x, '█'*green, self.color(2))
        self.put(0, x+green, '█'*(filled-green), self.color(4))
        self.put(0, x+filled, '░'*(cells-filled))
        self.put(0, x+cells, f'] {self.progress.percent:3}%')

    def key(self):
        try:
            return self.win.get_wch()
        except self.c.error:
            return None

    def wrapped(self, body, width):
        lines = []
        position=0
        for raw in body.splitlines(keepends=True):
            line=raw.rstrip('\r\n')
            at=position+len(line)-len(line.lstrip())
            role=next((r for a,b,r in getattr(body,'spans',[]) if a<=at<b),'normal')
            parts=textwrap.wrap(line, width, replace_whitespace=False,
                                drop_whitespace=False, subsequent_indent='    ') or ['']
            lines.extend((part,role) for part in parts)
            position+=len(raw)
        return lines

    def body(self, lines, start, height, offset):
        offset = max(0, min(offset, max(0, len(lines)-height)))
        for i, (line,role) in enumerate(lines[offset:offset+height]):
            style=self.muted() if role=='muted' else self.color(1)|self.c.A_BOLD if role=='explanation' else 0
            self.put(start+i, 2, line,style)
        return offset

    def muted(self):
        # Use the terminal's own low-intensity foreground on light/dark themes.
        return getattr(self.c,'A_DIM',0)

    def choose(self, title, body, options, question=False, hint=False, statuses=None, initial=0, main_menu=False, title_color=1, pin=False):
        selected, offset = max(0, min(initial, len(options)-1)), 0
        while True:
            size = self.frame(title, main_menu=main_menu, title_color=title_color)
            if size:
                h, w = size
                option_lines = [textwrap.wrap(str(o), w-8) or [''] for o in options]
                # A viewport for menus; selected items remain visible at any size.
                budget = max(4, min(h//2, h-11))
                start = selected
                used = len(option_lines[selected]) + 1
                while start > 0 and used + len(option_lines[start-1]) + 1 <= (budget + len(option_lines[selected]) + 1) // 2:
                    start -= 1
                    used += len(option_lines[start]) + 1
                end = selected + 1
                while end < len(options) and used + len(option_lines[end]) + 1 <= budget:
                    used += len(option_lines[end]) + 1
                    end += 1
                # Near the end, fill spare space above the selection.
                while start > 0 and used + len(option_lines[start-1]) + 1 <= budget:
                    start -= 1
                    used += len(option_lines[start]) + 1
                top = h - 3 - min(used, budget)
                rendered=StyledBody(body,'muted') if not isinstance(body,StyledBody) and not question and len(options)>1 else body
                lines = self.wrapped(rendered, w-5)
                offset = self.body(lines, 4, max(1, top-5), offset)
                row = top
                for idx in range(start, end):
                    style = self.c.A_REVERSE | self.c.A_BOLD if idx == selected else 0
                    if statuses:
                        style |= self.color(STATUS_COLORS.get(statuses[idx], 1))
                    for part, line in enumerate(option_lines[idx]):
                        if row >= h-3:
                            break
                        self.put(row, 2, ('› ' if idx == selected else '  ') + (line if part == 0 else '  '+line), style)
                        row += 1
                    row += 1
                overflow=len(lines)>max(1,top-5)
                position=f'{selected+1}/{len(options)} choices' if len(options)>1 else ''
                if overflow:
                    directions=('↑' if offset else '')+('↓' if offset+max(1,top-5)<len(lines) else '')
                    position+=(' · ' if position else '')+'More text '+directions+' · PgUp/PgDn'
                self.put(h-3, 2, position, self.muted())
                help_text = '↑↓ / j k select · Enter confirm · Esc/q back'
                if pin:
                    help_text = '↑↓ select · Enter open · p pin/unpin · Esc/q back'
                if question:
                    help_text = '↑↓ select · Enter answer · s skip · Esc/q leave'
                    if hint:
                        help_text += ' · ? hint'
                self.put(h-1, 1, help_text,self.muted())
                self.win.refresh()
            key = self.key()
            if key in ('q', '\x1b'):
                return None
            if not size:
                continue
            if key in (self.c.KEY_DOWN, 'j'):
                selected = (selected+1) % len(options)
            elif key in (self.c.KEY_UP, 'k'):
                selected = (selected-1) % len(options)
            elif key in ('\n', '\r', self.c.KEY_ENTER):
                return selected
            elif key == self.c.KEY_NPAGE:
                offset += max(1, top-5)
            elif key == self.c.KEY_PPAGE:
                offset = max(0, offset-max(1, top-5))
            elif question and key == 's':
                return 'skip'
            elif hint and key == '?':
                return 'hint'
            elif pin and key in ('p','P'):
                return ('pin',selected)

    def page(self, title, body, title_color=1):
        return self.choose(title, body, ['Continue'], title_color=title_color) is not None

    def edit(self, title, body):
        chars, cursor, offset = [], 0, 0
        self.cursor(True)
        try:
            while True:
                size = self.frame(title)
                if size:
                    h, w = size
                    lines = self.wrapped(body, w-5)
                    offset = self.body(lines, 4, h-9, offset)
                    self.put(h-4, 2, 'Your code fragment (one line):', self.muted())
                    start = max(0, cursor-(w-8))
                    self.put(h-3, 2, '> ' + ''.join(chars[start:start+w-6]))
                    if len(lines)>h-9:
                        self.put(h-2,2,'More text · PgUp/PgDn',self.muted())
                    self.put(h-1, 1, 'Enter submit · ←→ edit · Esc leave · :skip / :hint',self.muted())
                    try:
                        self.win.move(h-3, min(w-2, 4+cursor-start))
                    except self.c.error:
                        pass
                    self.win.refresh()
                key = self.key()
                if key == '\x1b':
                    return None
                if not size:
                    if key == 'q':
                        return None
                    continue
                if key in ('\n','\r',self.c.KEY_ENTER):
                    value = ''.join(chars).strip()
                    if value:
                        return value
                elif key in (self.c.KEY_BACKSPACE, '\b', '\x7f') and cursor:
                    del chars[cursor-1]
                    cursor -= 1
                elif key == self.c.KEY_DC and cursor < len(chars):
                    del chars[cursor]
                elif key == self.c.KEY_LEFT:
                    cursor = max(0, cursor-1)
                elif key == self.c.KEY_RIGHT:
                    cursor = min(len(chars), cursor+1)
                elif key == self.c.KEY_HOME:
                    cursor = 0
                elif key == self.c.KEY_END:
                    cursor = len(chars)
                elif key == self.c.KEY_NPAGE:
                    offset += h-9
                elif key == self.c.KEY_PPAGE:
                    offset = max(0, offset-h+9)
                elif isinstance(key, str) and key.isprintable() and len(chars) < 2000:
                    chars.insert(cursor,key)
                    cursor += 1
        finally:
            self.cursor(False)


class CaptureTerminal(Terminal):
    """Leave wrapping to the live viewport, including after a resize."""
    def heading(self, text):
        print('\n' + text + '\n')

    def prose(self, text):
        print(text)


class TuiApp(App):
    def __init__(self, course, store, screen, seed):
        super().__init__(course, store, CaptureTerminal(True), seed)
        self.screen = screen
        self.transcript = io.StringIO()

    def begin_session(self, mode, questions):
        super().begin_session(mode, questions)
        self.screen.progress = self.progress

    def take_output(self):
        text = self.transcript.getvalue()
        self.transcript.seek(0)
        self.transcript.truncate(0)
        return text.strip()

    def action(self, method):
        self.progress = self.screen.progress = None
        with contextlib.redirect_stdout(self.transcript):
            try:
                method()
            except LeaveSession:
                self.take_output()
                self.progress = self.screen.progress = None
                return
            except (ValueError, OSError, sqlite3.Error) as exc:
                print(str(exc))
        text = self.take_output()
        if text:
            self.screen.page('Code Lingo', text)
        self.progress = self.screen.progress = None

    def question_body(self, q):
        code = '\n'.join(f'{i:2} │ {line}' for i,line in enumerate(q.get('code','').splitlines(),1))
        return StyledBody(code) + StyledBody('\n\n'+q['prompt'],'muted')

    def read_answer(self, q, title, exam=False):
        intro = self.take_output()
        if intro and not self.screen.page(title + ' · Before you begin', intro):
            raise LeaveSession
        body = self.question_body(q)
        if q['kind'] == 'mcq':
            options = list(q['options'])
            self.rng.shuffle(options)
            while True:
                selected = self.screen.choose(title, body, options, question=True, hint=not exam)
                if selected is None:
                    raise LeaveSession
                if selected == 'skip':
                    return '[skipped]'
                if selected == 'hint':
                    body = self.question_body(q) + '\n\nHint: ' + q['hint']
                    continue
                return options[selected]
        body += StyledBody('\n\nEnter only the requested expression or statement. Use the specified construction.','muted')
        while True:
            answer = self.screen.edit(title, body)
            if answer is None or answer == ':q':
                raise LeaveSession
            if answer == ':hint':
                if not exam:
                    body = self.question_body(q) + '\n\nHint: ' + q['hint']
                else:
                    body = self.question_body(q) + '\n\nHints are unavailable during an exam.'
                continue
            return '[skipped]' if answer == ':skip' else answer

    def ask(self, q, mode, demo_answer=None):
        q = self.prepare_question(q)
        title = ('READ' if q['kind'] == 'mcq' else 'WRITE') + ' · ' + self.course.lesson_for[q['id']]['title']
        answer = self.read_answer(q, title)
        result = self.grade(q, answer, mode)
        if result['correct']:
            message = f"Correct! +{result['xp']} EXP · +{result['gems']} gems · Combo {result['combo']}"
        else:
            message = 'Not quite. One heart lost; combo reset. A fresh variant will return in review.'
        if mode == 'practice':
            message += '\n' + self.store.practice_heart_message(result)
        body = self.question_body(q) + StyledBody('\n\n'+message,'muted') + '\n\nAnswer: ' + self.solution(q) + StyledBody('\n\nExplanation\n'+q['explanation'],'explanation')
        if not self.screen.page('Correct' if result['correct'] else 'Incorrect · Learn from this one', body,
                                title_color=2 if result['correct'] else 4):
            raise LeaveSession
        return result['correct']

    def exam_answer(self, q, index, total):
        return self.read_answer(q, f'PLACEMENT EXAM · {index}/{total} · need 21 correct', exam=True)

    def pick_lesson(self):
        sections = self.lesson_sections()
        section_states = [self.section_details(section)[1] for section in sections]
        initial = self.preferred_lesson_index(section_states)
        lesson_focus = {}
        legend = 'Green DONE · Cyan OPEN · Yellow ACTIVE · Red LOCK'
        while True:
            details = [self.section_details(section) for section in sections]
            choices = [f"[{state}] {section} · {done}/{len(lessons)} lessons done"
                       for section, (lessons, state, done) in zip(sections, details)]
            index = self.screen.choose('Choose a section · ' + self.course.title,
                legend + '\nChoose a section to browse its lessons. Esc returns to the main menu.',
                choices, statuses=[state for _, state, _ in details], initial=initial)
            if index is None:
                return
            initial = index
            section = sections[index]
            while True:
                lessons, _, _ = self.section_details(section)
                statuses = [self.lesson_status(l) for l in lessons]
                choices = [f"[{tag}] {l['title']} · {len(l['questions'])} questions"
                           for l, tag in zip(lessons, statuses)]
                selected = self.screen.choose(section + ' · Choose a lesson',
                    legend + '\nEsc returns to sections. Section exams are on the main menu.',
                    choices, statuses=statuses, initial=lesson_focus.get(section, self.preferred_lesson_index(statuses)))
                if selected is None:
                    break
                lesson_focus[section] = selected
                lesson = lessons[selected]
                if not self.unlocked(lesson):
                    missing = [self.course.by_id[lid]['title'] for lid in lesson['requires']
                               if not self.store.is_complete(self.course.lesson_key(lid))]
                    self.screen.page('Lesson locked',
                        'First complete these lessons, or pass their section exam:\n\n' +
                        '\n'.join('• ' + title for title in missing))
                    continue
                self.action(lambda: self.learn(lesson['id']))
                lesson_focus.pop(section, None)

    def pick_exam(self):
        sections = list(dict.fromkeys(l['section'] for l in self.course.lessons))
        initial = 0
        while True:
            requirements = [section_requirements(self.course, self.store, section) for section in sections]
            statuses = ['LOCK' if missing else 'DONE' if all(self.store.is_complete(self.course.lesson_key(l['id'])) for l in lessons) else 'OPEN' for lessons, missing in requirements]
            labels = [f'[{state}] {section}' for section, state in zip(sections, statuses)]
            i = self.screen.choose('Skip a section · placement exam', '25 questions · Pass with 21/25 to mark every lesson done.\nLive correct/wrong/left counts; detailed answers at the end. No hearts deducted.\nGreen DONE · Cyan OPEN · Red LOCK', labels, statuses=statuses, initial=initial)
            if i is None:
                return
            initial = i
            missing = requirements[i][1]
            if missing:
                self.screen.page('Exam locked', 'First complete these prerequisites, or pass their section exam:\n\n' + '\n'.join('• '+self.course.by_id[lid]['title'] for lid in missing))
                continue
            self.action(lambda: self.exam(sections[i]))

    def pick_course(self):
        from .course import course_catalog
        focused=None
        while True:
            pins=self.store.pinned_courses()
            entries=sorted(course_catalog(),key=lambda c:c['id'] not in pins)
            if focused is None:
                focused=entries[0]['id'] if pins else self.course.id
            selected=next((i for i,c in enumerate(entries) if c['id']==focused),0)
            labels=[];statuses=[]
            for c in entries:
                done=sum(self.store.is_complete(c['id']+':'+lid) for lid in c['lesson_ids'])
                status='DONE' if done>=c['lessons'] else 'ACTIVE' if c['id']==self.course.id else 'OPEN'
                labels.append(('★ ' if c['id'] in pins else '')+f"{c['title']} · {done}/{c['lessons']} lessons")
                statuses.append(status)
            body=StyledBody('★ Pinned languages appear first. Press p to pin/unpin the highlighted language.\nEach language keeps its own lessons, exams, and mistakes.','muted')
            choice=self.screen.choose('Choose language or library',body,labels,statuses=statuses,initial=selected,pin=True)
            if choice is None:
                return
            if isinstance(choice,tuple) and choice[0]=='pin':
                focused=entries[choice[1]]['id']
                self.store.toggle_course_pin(focused)
                continue
            self.switch_course(entries[choice]['id'])
            self.screen.progress = None
            return

    def pick_analytics(self):
        from .analytics import snapshot, report
        data = snapshot(self.store, self.course)
        entries = [c for c in data['courses'].values() if c['attempted']]
        selected = None
        while True:
            title = data['courses'][selected]['title'] if selected else 'All courses'
            choice = self.screen.choose('Overall analytics', StyledBody(report(data, selected)),
                ['Filter: ' + title, 'Back'])
            if choice is None or choice == 1:
                return
            ids = [None] + [c['id'] for c in entries]
            index = self.screen.choose('Filter analytics',
                'Only courses with saved activity appear here. Esc keeps the current filter.',
                ['All courses'] + [c['title'] for c in entries], initial=ids.index(selected))
            if index is not None:
                selected = ids[index]

    def pick_streak_recovery(self):
        while True:
            choice = self.screen.choose('Streak recovery', self.streak_recovery_text(),
                ['Restore streak', 'Choose a lesson', 'Review questions (up to 20)', 'Back'])
            if choice is None or choice == 3:
                return
            if choice == 0:
                self.action(self.recover_streak)
            elif choice == 1:
                self.pick_lesson()
            else:
                self.action(lambda: self.review(limit=20, early=True))

    def menu(self):
        labels = ['Continue learning','Choose section / lesson','Review due questions','Review upcoming questions','Practice / recover hearts','Skip section · take exam','Mistake notebook','Progress & exam history','Shop · heart for 10 gems','Course sources','Change language / library','Overall analytics','Streak recovery','Quit']
        while True:
            labels[2] = f'Review due questions ({len(self.store.due(self.keys, limit=len(self.keys)))})'
            i = self.screen.choose('CODE LINGO · ' + self.course.title, 'Daily goal: finish one lesson or exam.\nNumbers, text, and contexts vary across attempts.\n\nUse the arrow keys and Enter. Your progress saves after each answer.', labels, main_menu=True)
            if i is None or i == 13:
                return
            if i == 12:
                self.pick_streak_recovery()
            elif i == 11:
                self.pick_analytics()
            elif i == 10:
                self.pick_course()
            elif i == 1:
                self.pick_lesson()
            elif i == 5:
                self.pick_exam()
            elif i == 8:
                choice = self.screen.choose('Gem shop', 'Earn 2 gems per newly credited correct problem each day, and 20 for a first exam pass. A heart costs 10 gems. Five correct practice answers restore one heart for free.', ['Buy one heart · 10 gems','Back'])
                if choice == 0:
                    self.screen.page('Gem shop', self.store.buy_heart())
            else:
                actions = {0:self.learn, 2:self.review, 3:lambda:self.review(early=True), 4:self.practice, 6:self.mistakes, 7:self.stats, 9:self.sources}
                self.action(actions[i])


def run_tui(course, store, seed=None):
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise ValueError('TUI needs an interactive terminal. Use menu or --plain for line input.')
    try:
        import curses
    except ImportError:
        raise ValueError('This Python has no curses support. Use the line-input menu on this platform.') from None
    try:
        if hasattr(curses, 'set_escdelay'):
            curses.set_escdelay(25)
        curses.wrapper(lambda win: TuiApp(course, store, Screen(win, store, curses), seed).menu())
    except KeyboardInterrupt:
        pass
    except curses.error as exc:
        raise ValueError(f'Terminal could not start: {exc}. Try TERM=xterm-256color or the line-input menu.') from None
    return 0
