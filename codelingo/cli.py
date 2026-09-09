"""Terminal interface. The course and learning state are UI-independent."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import random
import shutil
import sqlite3
import sys
import textwrap

from . import __version__
from .course import check_answer, load_course, course_catalog
from .store import DAILY_GOAL, Store
from .templates import render
from .exams import Exam
from .progress import SessionProgress


class LeaveSession(Exception):
    pass


class Terminal:
    def __init__(self, plain=False):
        self.color = sys.stdout.isatty() and not plain and "NO_COLOR" not in os.environ
        self.width = min(88, max(40, shutil.get_terminal_size((80, 24)).columns - 2))

    def style(self, text, color="36"):
        return f"\033[{color}m{text}\033[0m" if self.color else text

    def heading(self, text):
        print("\n" + self.style(text, "1;36"))
        print(self.style("─" * self.width, "2"))

    def prose(self, text):
        for paragraph in text.split("\n"):
            print(textwrap.fill(paragraph, self.width))

    def code(self, text):
        if text:
            print()
            for i, line in enumerate(text.splitlines(), 1):
                print(self.style(f"  {i:2} │ ", "2") + line)
            print()


class App:
    def __init__(self, course, store, terminal, seed=None):
        self.course, self.store, self.ui = course, store, terminal
        self.rng = random.Random(seed)
        self.keys = {course.key(qid): q for qid, q in course.questions.items()}
        self.combo = 0
        self.progress = None

    def switch_course(self, course_id):
        course = load_course(course_id)
        self.course = course
        self.keys = {course.key(qid): q for qid, q in course.questions.items()}
        self.combo = 0
        self.progress = None
        self.store.selected_course(course_id)

    def pick_course(self):
        entries = course_catalog()
        for i, entry in enumerate(entries, 1):
            print(f"{i:2}. {entry['title']} ({entry['lessons']} lessons)")
        try:
            choice = input('Language number (blank to cancel) > ').strip()
        except (EOFError, KeyboardInterrupt):
            raise LeaveSession from None
        if not choice:
            return
        if not choice.isdigit() or not 1 <= int(choice) <= len(entries):
            raise ValueError('Choose a listed language number.')
        self.switch_course(entries[int(choice)-1]['id'])

    def begin_session(self, mode, questions):
        initial = {}
        if mode == 'learn':
            for q in questions:
                key = self.course.key(q['id'])
                if self.store.passed(key):
                    initial[q['id']] = True
                else:
                    row = self.store.db.execute("SELECT correct FROM attempts WHERE qid=? AND mode='learn' ORDER BY id DESC LIMIT 1", (key,)).fetchone()
                    if row:
                        initial[q['id']] = bool(row[0])
        self.progress = SessionProgress(mode, questions, initial)

    def lesson_status(self, lesson):
        if self.store.is_complete(self.course.lesson_key(lesson['id'])):
            return 'DONE'
        if not self.unlocked(lesson):
            return 'LOCK'
        if self.store.active_lesson(self.course.id) == lesson['id']:
            return 'ACTIVE'
        return 'OPEN'

    def unlocked(self, lesson):
        return all(self.store.is_complete(self.course.lesson_key(lid)) for lid in lesson["requires"])

    def status(self):
        s = self.store.stats()
        self.ui.prose(f"EXP {s['xp']}  |  Gems {s['gems']}  |  Streak {s['streak']} days  |  Today {min(s['daily'], DAILY_GOAL)}/{DAILY_GOAL}  |  Hearts {s['hearts']}/5")
        return s

    def course_map(self):
        self.ui.heading(self.course.title)
        section = None
        for l in self.course.lessons:
            if section != l["section"]:
                section = l["section"]
                print("\n" + self.ui.style(section, "1"))
            done = self.store.is_complete(self.course.lesson_key(l["id"]))
            passed = sum(self.store.passed(self.course.key(q["id"])) for q in l["questions"])
            state = self.lesson_status(l)
            color = {'DONE':'32', 'OPEN':'36', 'ACTIVE':'33', 'LOCK':'31'}[state]
            note = ' · passed by exam' if self.store.completion_origin(self.course.lesson_key(l['id'])) == 'exam' else ''
            print(self.ui.style(f"  {state:6}  {l['id']:14} {l['title']} ({passed}/{len(l['questions'])} practiced){note}", color))
        self.ui.prose("\nStart: learn <lesson-id>. Each lesson teaches first, then checks reading before writing. Pass a section exam to mark its lessons done and unlock the next section.")

    def sources(self):
        self.ui.heading("Course sources")
        for s in self.course.data["sources"]:
            print(f"\n{s['title']}\n{s['url']}")
            self.ui.prose(s["usage"])
            if s.get("license_url"):
                print(s["license_url"])

    def stats(self):
        self.ui.heading("Your progress")
        s = self.status()
        done = sum(self.store.is_complete(self.course.lesson_key(l["id"])) for l in self.course.lessons)
        due = len(self.store.due(self.keys, limit=len(self.keys)))
        print(f"Lessons completed: {done}/{len(self.course.lessons)}")
        print(f"Best combo: {s['best_combo']}  |  Mistakes due: {due}")
        for row in self.store.db.execute('SELECT section,state,correct,total FROM exams WHERE course=? ORDER BY id DESC LIMIT 5', (self.course.id,)):
            score = f"{row['correct']}/{row['total']}" if row['total'] else 'unfinished'
            print(f"Exam: {row['section']} · {row['state']} · {score}")
        print(f"Daily goal: finish one lesson or exam. Completed today: {s['daily']}; local date {s['today']}.")
        if s["daily"] >= DAILY_GOAL:
            print(self.ui.style("Daily goal complete. Your streak is secured!", "32"))
        if done == len(self.course.lessons):
            print(self.ui.style("Course explorer badge earned: every starter lesson complete.", "33"))

    def mistakes(self):
        self.ui.heading("Mistake notebook")
        rows = self.store.mistakes(self.keys)
        if not rows:
            print("No mistakes yet. Start a lesson to build your notebook.")
        for r in rows:
            q = json.loads(r['last_wrong_snapshot']) if r.get('last_wrong_snapshot') else self.keys[r["qid"]]
            due = datetime.fromtimestamp(r["due"]).strftime("%Y-%m-%d %H:%M") if r["due"] else "—"
            print(f"\n{q['id']}  |  {r['errors']} misses  |  Next review: {due}")
            self.ui.prose(q["prompt"])
            self.ui.code(q.get("code", ""))
            print("Your last answer: " + str(r["last_wrong"]))
            print("Answer: " + self.solution(q))
            self.ui.prose(q["explanation"])

    @staticmethod
    def solution(q):
        return q["answer"] if q["kind"] == "mcq" else q["accepted"][0]

    def prepare_question(self, q):
        previous = self.store.last_variant(self.course.key(q['id']))
        for _ in range(30):
            instance = render(q, self.rng)
            if not q.get('parameters') or instance != previous:
                break
        self.store.last_variant(self.course.key(q['id']), instance)
        return instance

    def grade(self, q, answer, mode):
        correct = check_answer(q, answer)
        result = self.store.record(self.course.key(q['id']), answer, correct, mode, self.combo, snapshot=q)
        self.combo = result['combo']
        if self.progress:
            self.progress.mark(q['id'], result['correct'])
            # Secure the goal on the final submission, even if the learner
            # closes the feedback page before returning to the summary.
            if mode == 'learn' and self.progress.counts[0] == self.progress.total:
                lesson = self.course.lesson_for[q['id']]
                self.store.complete(self.course.lesson_key(lesson['id']), [self.course.key(card['id']) for card in lesson['questions']])
            elif mode == 'practice' and self.progress.replay_lid and self.progress.counts[2] == 0:
                self.store.finish_lesson_replay(self.progress.replay_lid)
        return result

    def ask(self, q, mode, demo_answer=None):
        q = self.prepare_question(q)
        if demo_answer is not None:
            demo_answer = self.solution(q) if demo_answer != '[wrong-demo]' else next(a for a in q['options'] if a != q['answer'])
        self.ui.heading(("READ" if q["kind"] == "mcq" else "WRITE") + "  ·  " + q["concept"])
        self.ui.code(q.get("code", ""))
        self.ui.prose(q["prompt"])
        options = list(q.get("options", []))
        self.rng.shuffle(options)
        if options:
            for i, option in enumerate(options):
                print(f"  {chr(65 + i)}. {option}")
        else:
            self.ui.prose("Enter only the requested fragment. Preserve spelling, internal spaces, and punctuation." if q.get("checker") == "exact" else "Enter only the requested fragment. Spaces and quote style may vary; use the named construction.")
        print(self.ui.style("? hint   :skip reveal & lose a heart   :q save & leave", "2"))
        revealed = False
        while True:
            try:
                if demo_answer is None:
                    raw = input("\n> ").strip()
                else:
                    raw = chr(65 + options.index(demo_answer)) if options else demo_answer
                    print("\n> " + raw + "  [demo]")
            except (EOFError, KeyboardInterrupt):
                raise LeaveSession from None
            if raw.lower() == ":q":
                raise LeaveSession
            if raw == "?":
                self.ui.prose("Hint: " + q["hint"])
                continue
            if raw.lower() == ":skip":
                answer, revealed = "[skipped]", True
                break
            if not raw or len(raw) > 2000:
                print("Enter an answer of 1–2000 characters, or :q to leave.")
                continue
            if options:
                index = ord(raw.upper()) - 65 if len(raw) == 1 and raw.isascii() and raw.isalpha() else int(raw) - 1 if raw.isascii() and raw.isdigit() and len(raw) <= 2 else -1
                if not 0 <= index < len(options):
                    print(f"Choose A–{chr(64 + len(options))} or 1–{len(options)}. No heart lost.")
                    continue
                answer = options[index]
            else:
                answer = raw
            break
        correct = not revealed and check_answer(q, answer)
        result = self.grade(q, answer, mode)
        if correct:
            reward = f"+{result['xp']} EXP / +{result['gems']} gems" if result["xp"] else "already credited today"
            print(self.ui.style(f"\nCorrect!  {reward}  |  Combo {self.combo}  |  Hearts {result['hearts']}/5", "32"))
            if self.combo % 3 == 0:
                print(self.ui.style("Combo reward tier reached!", "33"))
        else:
            print(self.ui.style(f"\nIncorrect.  Hearts {result['hearts']}/5  |  Combo reset", "31"))
            print("Answer: " + self.solution(q))
            print("Added to review; it will return in 10 minutes.")
        self.ui.prose(q["explanation"])
        return correct

    def review(self, limit=5, early=False):
        self.combo = 0
        keys = self.store.due(self.keys, limit=limit, early=early)
        self.ui.heading("Mistake review" + (" · including upcoming cards" if early else ""))
        if not keys:
            print("No reviews due." if not early else "No mistakes to review yet.")
            print("Use practice for a refresher and to restore hearts.")
            return
        self.begin_session('review', [self.keys[key] for key in keys])
        self.ui.prose("Correct answers restore one heart. Review remains available at zero hearts. Early review keeps the existing due date.")
        for key in keys:
            self.ask(self.keys[key], "review")
        self.stats()

    def practice(self, limit=5, lesson=None):
        self.combo = 0
        if lesson:
            # Called only for completed lessons, so all stages are already taught.
            pool = lesson["questions"]
            limit = len(pool)
        else:
            pool = [q for key, q in self.keys.items() if self.store.passed(key) or self.store.is_complete(self.course.lesson_key(self.course.lesson_for[q['id']]['id']))]
            if not pool:
                first = self.course.lessons[0]
                self.ui.heading(first["title"] + " · refresher")
                self.ui.prose(first["intro"])
                pool = [q for q in first["questions"] if q["kind"] == "mcq"]
        self.ui.heading("Practice · earn back hearts")
        self.ui.prose("Correct answers restore a heart. Practice does not unlock lessons; return to learn to finish your course.")
        selected = self.rng.sample(pool, min(limit, len(pool)))
        self.begin_session('practice', selected)
        if lesson:
            self.progress.replay_lid = self.course.lesson_key(lesson['id'])
        for q in selected:
            self.ask(q, "practice")
        if lesson:
            self.store.finish_lesson_replay(self.course.lesson_key(lesson['id']))
            print('Full lesson replay complete. Daily goal secured.')
        self.stats()

    def learn(self, lesson_id=None, warmup=True):
        if lesson_id:
            lesson = self.course.by_id.get(lesson_id)
            if not lesson:
                raise ValueError(f"Unknown lesson: {lesson_id}. Use course to list lesson IDs.")
        else:
            lesson = self.course.by_id.get(self.store.active_lesson(self.course.id))
            if not lesson or not self.unlocked(lesson) or self.store.is_complete(self.course.lesson_key(lesson["id"])):
                lesson = next((l for l in self.course.lessons if self.unlocked(l) and not self.store.is_complete(self.course.lesson_key(l["id"]))), None)
        if lesson is None:
            print("All starter lessons complete! Use review or practice to keep reading.")
            return
        if not self.unlocked(lesson):
            missing = [lid for lid in lesson["requires"] if not self.store.is_complete(self.course.lesson_key(lid))]
            print("This lesson opens after: " + ", ".join(missing))
            return
        if self.store.is_complete(self.course.lesson_key(lesson["id"])):
            self.practice(lesson=lesson)
            return
        self.store.active_lesson(self.course.id, lesson["id"])
        if warmup and self.store.due(self.keys, limit=1):
            print("First, revisit up to two due mistakes.")
            self.review(limit=2)
        self.combo = 0
        self.begin_session('learn', lesson['questions'])
        self.ui.heading(lesson["section"] + " · " + lesson["title"])
        self.ui.prose(lesson["intro"])
        self.ui.prose(f"\n{len(lesson['questions'])} problems · Read → explain → write. Each answer saves immediately; :q leaves safely.")
        # Two stages ensure missed reading questions are corrected before writing.
        for kind in ("mcq", "write"):
            pending = [q for q in lesson["questions"] if q["kind"] == kind and not self.store.passed(self.course.key(q["id"]))]
            while pending:
                if self.store.player()["hearts"] == 0:
                    print("\nOut of hearts. Progress saved. Use review --all or practice to recover, then learn to resume.")
                    return
                q = pending.pop(0)
                if not self.ask(q, "learn"):
                    pending.append(q)
        self.store.complete(self.course.lesson_key(lesson["id"]), [self.course.key(q["id"]) for q in lesson["questions"]])
        self.ui.heading("Lesson complete · " + lesson["title"])
        print("All cards answered correctly. Any mistakes remain in spaced review.")
        self.stats()

    def demo(self):
        lesson = self.course.lessons[0]
        self.ui.heading("CODE LINGO · guided demo")
        self.ui.prose("This demo uses temporary progress. Watch a mistake, a correction, a combo, and heart recovery.")
        self.ui.prose(lesson["intro"])
        q = lesson["questions"][0]
        self.ask(q, "learn", '[wrong-demo]')
        for q in lesson["questions"]:
            self.ask(q, "learn", self.solution(q))
        self.store.complete(self.course.lesson_key(lesson["id"]), [self.course.key(q["id"]) for q in lesson["questions"]])
        self.ui.heading("Early review restores a heart; the scheduled review stays")
        self.ask(lesson["questions"][0], "review", self.solution(lesson["questions"][0]))
        self.stats()
        print("\nTry it yourself: python3 -m codelingo learn")

    def exam_answer(self, q, index, total):
        self.ui.heading(f'Section exam · {index}/{total}')
        self.ui.code(q.get('code', ''))
        self.ui.prose(q['prompt'])
        options = list(q.get('options', []))
        self.rng.shuffle(options)
        for i, option in enumerate(options):
            print(f'  {chr(65+i)}. {option}')
        print('No hints or answers until the end. :skip submits a miss; :q abandons the exam.')
        while True:
            try:
                raw = input('> ').strip()
            except (EOFError, KeyboardInterrupt):
                raise LeaveSession from None
            if raw == ':q':
                raise LeaveSession
            if raw == ':skip':
                return '[skipped]'
            if not raw or len(raw) > 2000:
                continue
            if not options:
                return raw
            index = ord(raw.upper()) - 65 if len(raw) == 1 and raw.isascii() and raw.isalpha() else int(raw)-1 if raw.isascii() and raw.isdigit() and len(raw) <= 2 else -1
            if 0 <= index < len(options):
                return options[index]
            print('Choose an option letter or number.')

    def exam(self, section=None):
        if section is None:
            try:
                section = input('Section (' + ' / '.join(dict.fromkeys(l['section'] for l in self.course.lessons)) + '): ').strip()
            except (EOFError, KeyboardInterrupt):
                raise LeaveSession from None
        exam = Exam(self.course, self.store, section, self.rng)
        self.begin_session('exam', exam.questions)
        self.ui.heading(f'{exam.section} placement · 25 questions')
        self.ui.prose('21/25 or better passes and marks every lesson in this section done. The status bar shows correct/wrong/remaining counts. Detailed answers appear at the end. No hints or retries; no hearts are deducted. Leaving abandons this attempt; nothing is unlocked.')
        try:
            for index, q in enumerate(exam.questions, 1):
                answer = self.exam_answer(q, index, len(exam.questions))
                exam.submit(answer)
                self.progress.mark(q['id'], check_answer(q, answer))
            result = exam.finish()
        except BaseException:
            exam.abort()
            raise
        finally:
            exam.save_attempts()
        self.ui.heading(f"{'PASSED' if result['passed'] else 'NOT PASSED'} · {result['correct']}/{result['total']} ({100*result['correct']/result['total']:.0f}%)")
        print('All lessons in this section are now done.' if result['passed'] else '21 correct answers are required. Study the missed concepts, then try a fresh exam.')
        if result['rewarded']:
            print('+50 EXP and +20 gems for your first pass.')
        for q, correct in zip(exam.questions, result['results']):
            if not correct:
                print('\n' + q['id'])
                self.ui.code(q.get('code',''))
                self.ui.prose(q['prompt'])
                print('Answer: ' + self.solution(q))
                self.ui.prose(q['explanation'])

    def menu(self):
        while True:
            self.ui.heading("CODE LINGO  /  Read code. Build fluency.  /  " + self.course.title)
            self.status()
            print("\n  1  Continue learning\n  2  Review due mistakes\n  3  Practice / restore hearts\n  4  Course map\n  5  Mistake notebook\n  6  Progress\n  7  Sources\n  8  Section exam / skip section\n  9  Shop / restore heart (10 gems)\n  10 Change language\n  q  Quit")
            try:
                choice = input("\nChoose > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nSee you next time.")
                return
            if choice in {"q", ":q"}:
                return
            actions = {"1": self.learn, "2": self.review, "3": self.practice, "4": self.course_map, "5": self.mistakes, "6": self.stats, "7": self.sources, "8": self.exam, "9": lambda: print(self.store.buy_heart()), "10": self.pick_course}
            action = actions.get(choice)
            if not action:
                print("Choose 1–10 or q.")
                continue
            try:
                action()
            except LeaveSession:
                print("\nProgress saved.")
            except (ValueError, OSError, sqlite3.Error) as exc:
                print(str(exc))


def positive_int(value):
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer") from None
    if not 1 <= number <= 50:
        raise argparse.ArgumentTypeError("must be between 1 and 50")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description="Code Lingo — a reading-first daily code tutor")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--data-dir", type=Path, help="progress directory (default: XDG_DATA_HOME/code-lingo)")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--course", choices=[c["id"] for c in course_catalog()], help="select a built-in language")
    selection.add_argument("--course-file", type=Path, help="load an additional JSON course")
    parser.add_argument("--plain", action="store_true", help="disable ANSI styling")
    parser.add_argument("--seed", type=int, help="repeatable option shuffling")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("languages", help="list built-in languages")
    sub.add_parser('tui', help='launch the arrow-key terminal interface')
    sub.add_parser('menu', help='launch the plain line-input menu')
    exam = sub.add_parser('exam', help='pass a 25-question exam to skip a section')
    exam.add_argument('section', choices=['Basics','Intermediate','Advanced','Specialized','basics','intermediate','advanced','specialized'])
    learn = sub.add_parser("learn", help="start or resume the next lesson")
    learn.add_argument("lesson", nargs="?")
    review = sub.add_parser("review", help="revisit mistakes due now")
    review.add_argument("--all", action="store_true", help="also include upcoming mistakes")
    review.add_argument("--limit", type=positive_int, default=5)
    practice = sub.add_parser("practice", help="practice known cards and restore hearts")
    practice.add_argument("--limit", type=positive_int, default=5)
    for command, help_text in [("course", "show the curriculum and unlocks"), ("stats", "show daily progress"), ("mistakes", "show your mistake notebook"), ("sources", "show curriculum references"), ("demo", "watch a demo with temporary progress"), ("validate", "validate the course file")]:
        sub.add_parser(command, help=help_text)
    args = parser.parse_args(argv)
    store = None
    try:
        if args.command == "languages":
            for c in course_catalog():
                print(f"{c['id']:12} {c['title']} — {c['lessons']} lessons / {c['questions']} questions")
            return 0
        if args.command == "validate":
            course = load_course(args.course or "python", path=args.course_file)
            print(f"Valid: {course.title} — {len(course.lessons)} lessons, {len(course.questions)} questions")
            return 0
        directory = args.data_dir or Path(os.environ.get("CODELINGO_HOME") or str(Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))) / "code-lingo"))
        store = Store(":memory:" if args.command == "demo" else directory / "progress.sqlite3")
        name = args.course or store.selected_course()
        if name not in {c["id"] for c in course_catalog()}:
            name = "python"
        course = load_course(name, path=args.course_file)
        if args.course:
            store.selected_course(args.course)
        app = App(course, store, Terminal(args.plain), seed=args.seed)
        if args.command == 'tui' or (args.command is None and sys.stdin.isatty() and sys.stdout.isatty() and not args.plain):
            from .tui import run_tui
            return run_tui(course, store, args.seed)
        if args.command == 'menu':
            app.menu()
        elif args.command == 'exam':
            app.exam(args.section)
        elif args.command == "learn":
            app.learn(args.lesson)
        elif args.command == "review":
            app.review(args.limit, args.all)
        elif args.command == "practice":
            app.practice(args.limit)
        elif args.command == "course":
            app.course_map()
        elif args.command:
            getattr(app, args.command)()
        else:
            app.menu()
        return 0
    except LeaveSession:
        print("\nProgress saved. Run learn to resume.")
        return 0
    except (ValueError, KeyError, TypeError, OSError, sqlite3.Error) as exc:
        print(f"Code Lingo: {exc}", file=sys.stderr)
        return 1
    finally:
        if store:
            store.close()
