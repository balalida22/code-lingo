"""SQLite-backed progress, hearts, activity, and spaced learning review."""

from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import time
import json

INTERVALS = (1, 3, 7, 14, 30)
HEART_SECONDS = 1800
DAILY_GOAL = 1


class Store:
    def __init__(self, path, clock=time.time):
        self.clock = clock
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY CHECK(id=1), hearts INTEGER NOT NULL,
                heart_at REAL NOT NULL, xp INTEGER NOT NULL DEFAULT 0,
                best_combo INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS progress (
                qid TEXT PRIMARY KEY, passed INTEGER NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0, errors INTEGER NOT NULL DEFAULT 0,
                last_wrong TEXT, last_seen REAL);
            CREATE TABLE IF NOT EXISTS reviews (
                qid TEXT PRIMARY KEY, due REAL NOT NULL, stage INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS completed (lid TEXT PRIMARY KEY, at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS active_lessons (course TEXT PRIMARY KEY, lid TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS credit (
                day TEXT NOT NULL, qid TEXT NOT NULL, xp INTEGER NOT NULL,
                PRIMARY KEY(day, qid));
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY, qid TEXT NOT NULL, at REAL NOT NULL,
                answer TEXT NOT NULL, correct INTEGER NOT NULL, mode TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS variants (qid TEXT PRIMARY KEY, snapshot TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY, course TEXT NOT NULL, section TEXT NOT NULL,
                questions TEXT NOT NULL, answers TEXT NOT NULL DEFAULT '[]',
                state TEXT NOT NULL DEFAULT 'active', at REAL NOT NULL,
                correct INTEGER, total INTEGER);
            CREATE TABLE IF NOT EXISTS section_passes (
                course TEXT NOT NULL, section TEXT NOT NULL, exam_id INTEGER NOT NULL,
                PRIMARY KEY(course, section));
            CREATE TABLE IF NOT EXISTS daily_completions (
                day TEXT NOT NULL, kind TEXT NOT NULL, activity TEXT NOT NULL,
                at REAL NOT NULL, PRIMARY KEY(day,kind,activity));
            CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS migrations (name TEXT PRIMARY KEY);
        """)
        with self.db:
            # Additive migration from the original 0.1 database. No progress reset.
            for table, column, declaration in (
                ('player', 'gems', 'INTEGER NOT NULL DEFAULT 0'),
                ('progress', 'last_wrong_snapshot', 'TEXT'),
                ('attempts', 'snapshot', 'TEXT'),
                ('attempts', 'exam_id', 'INTEGER'),
                ('completed', 'origin', "TEXT NOT NULL DEFAULT 'learn'")
            ):
                if column not in {r[1] for r in self.db.execute(f'PRAGMA table_info({table})')}:
                    self.db.execute(f'ALTER TABLE {table} ADD COLUMN {column} {declaration}')
            self.db.execute('CREATE UNIQUE INDEX IF NOT EXISTS exam_answer_once ON attempts(exam_id,qid) WHERE exam_id IS NOT NULL')
            self.db.execute("INSERT OR IGNORE INTO player(id,hearts,heart_at) VALUES(1,5,?)", (clock(),))
            if not self.db.execute("SELECT 1 FROM migrations WHERE name='completion_daily_goal'").fetchone():
                # Preserve historical earned streak days, but today's goal uses
                # actual lesson/exam completions instead of old card credit.
                for row in self.db.execute("SELECT day FROM credit WHERE day < ? GROUP BY day HAVING COUNT(*)>=5", (self.today(),)).fetchall():
                    self.db.execute("INSERT OR IGNORE INTO daily_completions VALUES(?,'legacy','card-goal',?)", (row[0],clock()))
                for row in self.db.execute("SELECT lid,at FROM completed WHERE origin='learn'").fetchall():
                    self._completion_event('lesson', row['lid'], row['at'])
                for row in self.db.execute("""SELECT e.id,COALESCE(MAX(a.at),e.at) AS finished_at
                    FROM exams e LEFT JOIN attempts a ON a.exam_id=e.id
                    WHERE e.state IN ('passed','failed') GROUP BY e.id""").fetchall():
                    self._completion_event('exam', str(row['id']), row['finished_at'])
                self.db.execute("INSERT INTO migrations VALUES('completion_daily_goal')")

            if not self.db.execute("SELECT 1 FROM migrations WHERE name='learned_card_reviews'").fetchone():
                # Seed successfully learned cards, preserving every existing due date.
                self.db.execute("""INSERT OR IGNORE INTO reviews(qid,due,stage)
                    SELECT qid,COALESCE(last_seen,?)+86400,1 FROM progress
                    WHERE passed=1""", (clock(),))
                self.db.execute("""INSERT OR IGNORE INTO reviews(qid,due,stage)
                    SELECT qid,MAX(at)+86400,1 FROM attempts
                    WHERE correct=1 AND mode IN ('exam','practice') GROUP BY qid""")
                self.db.execute("INSERT INTO migrations VALUES('learned_card_reviews')")

    def selected_course(self, course_id=None):
        if course_id is not None:
            with self.db:
                self.db.execute("INSERT INTO settings VALUES('course',?) ON CONFLICT(name) DO UPDATE SET value=excluded.value", (course_id,))
        row = self.db.execute("SELECT value FROM settings WHERE name='course'").fetchone()
        return row[0] if row else 'python'

    def close(self):
        self.db.close()

    def pinned_courses(self):
        prefix='pinned_course:'
        return {row[0][len(prefix):] for row in self.db.execute(
            "SELECT name FROM settings WHERE name GLOB 'pinned_course:*' AND value='1'")}

    def toggle_course_pin(self, course_id):
        key='pinned_course:'+course_id
        with self.db:
            pinned=self.db.execute('SELECT 1 FROM settings WHERE name=?',(key,)).fetchone()
            if pinned:
                self.db.execute('DELETE FROM settings WHERE name=?',(key,))
            else:
                self.db.execute('INSERT INTO settings(name,value) VALUES(?,?)',(key,'1'))
        return not bool(pinned)

    def today(self):
        return datetime.fromtimestamp(self.clock()).date().isoformat()

    def _refill(self, now):
        p = self.db.execute("SELECT * FROM player WHERE id=1").fetchone()
        elapsed = max(0, int((now - p["heart_at"]) // HEART_SECONDS))
        hearts = min(5, p["hearts"] + elapsed)
        anchor = now if hearts == 5 else p["heart_at"] + elapsed * HEART_SECONDS
        self.db.execute("UPDATE player SET hearts=?,heart_at=? WHERE id=1", (hearts, anchor))
        return hearts

    def player(self):
        with self.db:
            self._refill(self.clock())
        return dict(self.db.execute("SELECT * FROM player WHERE id=1").fetchone())

    def passed(self, qid):
        row = self.db.execute("SELECT passed FROM progress WHERE qid=?", (qid,)).fetchone()
        return bool(row and row[0])

    def complete(self, lid, qids):
        if qids and all(self.passed(qid) for qid in qids):
            with self.db:
                self.db.execute("INSERT OR IGNORE INTO completed(lid,at) VALUES(?,?)", (lid, self.clock()))
                self._completion_event('lesson', lid)
            return True
        return False

    def _completion_event(self, kind, activity, at=None):
        """Insert inside the caller's transaction; do not commit other writes."""
        at = self.clock() if at is None else at
        day = datetime.fromtimestamp(at).date().isoformat()
        self.db.execute('INSERT OR IGNORE INTO daily_completions VALUES(?,?,?,?)', (day,kind,activity,at))

    def finish_lesson_replay(self, lid):
        with self.db:
            if not self.is_complete(lid):
                raise ValueError('Only completed lessons can be replayed')
            self._completion_event('lesson', lid)

    def is_complete(self, lid):
        return self.db.execute("SELECT 1 FROM completed WHERE lid=?", (lid,)).fetchone() is not None

    def active_lesson(self, course, lid=None):
        if lid is not None:
            with self.db:
                self.db.execute("INSERT INTO active_lessons VALUES(?,?) ON CONFLICT(course) DO UPDATE SET lid=excluded.lid", (course, lid))
        row = self.db.execute("SELECT lid FROM active_lessons WHERE course=?", (course,)).fetchone()
        return row[0] if row else None

    def due(self, valid_keys, limit=5, early=False):
        rows = self.db.execute("SELECT qid,due FROM reviews ORDER BY due,qid").fetchall()
        now = self.clock()
        return [r["qid"] for r in rows if r["qid"] in valid_keys and (early or r["due"] <= now)][:limit]

    def record(self, qid, answer, correct, mode, combo=0, snapshot=None, exam_id=None):
        """Persist each answer in one transaction. Practice cannot clear lesson cards.

        A wrong answer restarts review at ten minutes. Only a due review
        advances its interval. Newly learned cards start at one day.
        Early practice never delays a scheduled review.
        """
        if mode not in {"learn", "review", "practice", "exam"}:
            raise ValueError("Unknown mode")
        now = self.clock()
        with self.db:
            # Acquire the write lock before reading balances (also for two CLIs).
            self.db.execute("UPDATE player SET id=id WHERE id=1")
            hearts = self._refill(now)
            if exam_id is not None and self.db.execute('SELECT 1 FROM attempts WHERE exam_id=? AND qid=?', (exam_id,qid)).fetchone():
                return {'xp':0,'gems':0,'combo':0,'hearts':hearts,'correct':correct}
            if mode == "learn" and hearts == 0:
                raise ValueError("No hearts. Review or practice to recover one.")
            self.db.execute("INSERT OR IGNORE INTO progress(qid) VALUES(?)", (qid,))
            self.db.execute("""UPDATE progress SET attempts=attempts+1, errors=errors+?,
                passed=MAX(passed,?), last_wrong=CASE WHEN ? THEN last_wrong ELSE ? END,
                last_seen=? WHERE qid=?""",
                (int(not correct), int(correct and mode == "learn"), int(correct), answer[:2000], now, qid))
            encoded = json.dumps(snapshot) if snapshot else None
            self.db.execute("INSERT INTO attempts(qid,at,answer,correct,mode,snapshot,exam_id) VALUES(?,?,?,?,?,?,?)",
                            (qid, now, answer[:2000], int(correct), mode, encoded, exam_id))
            if not correct:
                self.db.execute("UPDATE progress SET last_wrong_snapshot=? WHERE qid=?", (encoded, qid))
            review = self.db.execute("SELECT * FROM reviews WHERE qid=?", (qid,)).fetchone()
            if not correct:
                if mode != 'exam':
                    hearts = max(0, hearts - 1)
                self.db.execute("""INSERT INTO reviews VALUES(?,?,0)
                    ON CONFLICT(qid) DO UPDATE SET due=excluded.due,stage=0""", (qid, now + 600))
            elif review and mode in {"review", "practice"} and review["due"] <= now:
                stage = review["stage"]
                self.db.execute("UPDATE reviews SET due=?,stage=? WHERE qid=?",
                                (now + INTERVALS[min(stage, 4)] * 86400, min(stage + 1, 4), qid))
            elif correct and not review and mode in {"learn", "exam", "practice"}:
                self.db.execute("INSERT INTO reviews(qid,due,stage) VALUES(?,?,1)",
                                (qid, now + 86400))
            if correct and mode in {"review", "practice"}:
                hearts = min(5, hearts + 1)
            combo = combo + 1 if correct and mode != 'exam' else 0
            xp = 0
            if correct and mode != 'exam':
                xp = 10 + min(combo // 3, 3) * 5
                cursor = self.db.execute("INSERT OR IGNORE INTO credit VALUES(?,?,?)", (self.today(), qid, xp))
                if not cursor.rowcount:
                    xp = 0
            gems = 2 if xp else 0
            self.db.execute("UPDATE player SET hearts=?,xp=xp+?,gems=gems+?,best_combo=MAX(best_combo,?) WHERE id=1",
                            (hearts, xp, gems, combo))
        return {"xp": xp, "gems": gems, "combo": combo, "hearts": hearts, "correct": correct}

    def last_variant(self, key, snapshot=None):
        row = self.db.execute('SELECT snapshot FROM variants WHERE qid=?', (key,)).fetchone()
        previous = json.loads(row[0]) if row else None
        if snapshot is not None:
            with self.db:
                self.db.execute('INSERT INTO variants VALUES(?,?) ON CONFLICT(qid) DO UPDATE SET snapshot=excluded.snapshot', (key, json.dumps(snapshot)))
        return previous

    def buy_heart(self):
        with self.db:
            self.db.execute('UPDATE player SET id=id WHERE id=1')
            hearts = self._refill(self.clock())
            gems = self.db.execute('SELECT gems FROM player WHERE id=1').fetchone()[0]
            if hearts >= 5:
                return 'Your hearts are already full.'
            if gems < 10:
                return 'You need 10 gems to restore one heart.'
            self.db.execute('UPDATE player SET hearts=hearts+1,gems=gems-10 WHERE id=1')
        return 'One heart restored for 10 gems.'

    def completion_origin(self, lid):
        row = self.db.execute('SELECT origin FROM completed WHERE lid=?', (lid,)).fetchone()
        return row[0] if row else None

    def stats(self):
        p = self.player()
        days = {r[0] for r in self.db.execute('SELECT DISTINCT day FROM daily_completions')}
        today = datetime.fromtimestamp(self.clock()).date()
        cursor = today if today.isoformat() in days else today - timedelta(days=1)
        streak = 0
        while cursor.isoformat() in days:
            streak += 1
            cursor -= timedelta(days=1)
        p.update(today=self.today(), daily=self.db.execute("SELECT COUNT(*) FROM daily_completions WHERE day=?", (self.today(),)).fetchone()[0], streak=streak)
        return p

    def mistakes(self, valid_keys):
        return [dict(r) for r in self.db.execute("""SELECT p.*,r.due,r.stage FROM progress p
            LEFT JOIN reviews r USING(qid) WHERE errors>0 ORDER BY errors DESC,qid""") if r["qid"] in valid_keys]
