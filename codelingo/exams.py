"""Balanced section placement exams; no unlocks until a complete passing run."""
import json
from .course import check_answer
from .templates import render

EXAM_SIZE = 25


def section_requirements(course, store, section):
    lessons = [l for l in course.lessons if l['section'].lower() == section.lower()]
    if not lessons:
        raise ValueError('Unknown section: ' + section)
    within = {l['id'] for l in lessons}
    missing = sorted({lid for l in lessons for lid in l['requires']
                      if lid not in within and not store.is_complete(course.lesson_key(lid))})
    return lessons, missing


def passes(correct, total):
    return total >= 20 and correct * 100 > total * 80


class Exam:
    def __init__(self, course, store, section, rng):
        self.course, self.store, self.section = course, store, section
        self.lessons, missing = section_requirements(course, store, section)
        self.section = self.lessons[0]['section']
        if missing:
            raise ValueError('Exam locked. Complete or test out of the prerequisites first: ' + ', '.join(course.by_id[lid]['title'] for lid in missing))
        selected = []
        pools = []
        for lesson in self.lessons:
            # Every lesson contributes reading AND writing. Prefer parameterized
            # cards; fixed conceptual questions can still test language rules.
            pool = list(lesson['questions'])
            rng.shuffle(pool)
            for kind in ('mcq', 'write'):
                candidates = [q for q in pool if q['kind'] == kind]
                candidates.sort(key=lambda q: not bool(q.get('parameters')))
                if not candidates:
                    raise ValueError('Exam needs reading and writing in each lesson')
                q = candidates[0]
                selected.append(q)
                pool.remove(q)
            pools.append(pool)
        # Round-robin sampling keeps lesson counts within one of each other.
        while len(selected) < EXAM_SIZE:
            any_added = False
            for pool in pools:
                if pool and len(selected) < EXAM_SIZE:
                    selected.append(pool.pop())
                    any_added = True
            if not any_added:
                raise ValueError('Section needs at least 25 distinct exercise templates')
        rng.shuffle(selected)
        self.questions = []
        for q in selected:
            previous = store.last_variant(course.key(q['id']))
            for _ in range(30):
                instance = render(q, rng)
                if not q.get('parameters') or instance != previous:
                    break
            store.last_variant(course.key(q['id']), instance)
            self.questions.append(instance)
        with store.db:
            cursor = store.db.execute('INSERT INTO exams(course,section,questions,at) VALUES(?,?,?,?)', (course.id, self.section, json.dumps(self.questions), store.clock()))
            self.id = cursor.lastrowid

    def submit(self, answer):
        with self.store.db:
            # Serialize answer appends; committed answers survive leaving a run.
            self.store.db.execute('UPDATE exams SET id=id WHERE id=?', (self.id,))
            row = self.store.db.execute('SELECT * FROM exams WHERE id=?', (self.id,)).fetchone()
            answers = json.loads(row['answers'])
            if row['state'] != 'active' or len(answers) >= len(self.questions):
                raise ValueError('This exam does not accept more answers')
            answers.append(answer[:2000])
            self.store.db.execute('UPDATE exams SET answers=? WHERE id=?', (json.dumps(answers), self.id))
        q = self.questions[len(answers)-1]
        self.store.record(self.course.key(q['id']), answer, check_answer(q, answer), 'exam', snapshot=q, exam_id=self.id)
        # No correctness feedback is returned before the entire exam is over.

    def finish(self):
        with self.store.db:
            self.store.db.execute('UPDATE exams SET id=id WHERE id=?', (self.id,))
            row = self.store.db.execute('SELECT * FROM exams WHERE id=?', (self.id,)).fetchone()
            answers = json.loads(row['answers'])
            if row['state'] != 'active' or len(answers) != len(self.questions):
                raise ValueError('Finish all exam questions before grading')
            results = [check_answer(q, a) for q, a in zip(self.questions, answers)]
            correct, total = sum(results), len(results)
            passed = passes(correct, total)
            self.store.db.execute('UPDATE exams SET state=?,correct=?,total=? WHERE id=?', ('passed' if passed else 'failed', correct, total, self.id))
            self.store._completion_event('exam', str(self.id))
            rewarded = False
            if passed:
                cursor = self.store.db.execute('INSERT OR IGNORE INTO section_passes VALUES(?,?,?)', (self.course.id, self.section, self.id))
                rewarded = bool(cursor.rowcount)
                for lesson in self.lessons:
                    self.store.db.execute("INSERT OR IGNORE INTO completed(lid,at,origin) VALUES(?,?,'exam')", (self.course.lesson_key(lesson['id']), self.store.clock()))
                if rewarded:
                    self.store.db.execute('UPDATE player SET xp=xp+50,gems=gems+20 WHERE id=1')
        return dict(correct=correct, total=total, passed=passed, rewarded=rewarded, results=results)

    def abort(self):
        with self.store.db:
            self.store.db.execute("UPDATE exams SET state='abandoned' WHERE id=? AND state='active'", (self.id,))

    def save_attempts(self):
        """Called once on normal completion or abandonment, never shows answers."""
        row = self.store.db.execute('SELECT answers FROM exams WHERE id=?', (self.id,)).fetchone()
        for q, answer in zip(self.questions, json.loads(row[0])):
            self.store.record(self.course.key(q['id']), answer, check_answer(q, answer), 'exam', snapshot=q, exam_id=self.id)
