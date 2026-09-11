"""Read-only analytics from recorded answers, completions, and exams."""
from datetime import datetime, timedelta

from .course import course_catalog


COURSE_OF_Q = "substr(qid,1,instr(qid,':')-1)"
COURSE_OF_L = "substr(lid,1,instr(lid,':')-1)"


def snapshot(store, current_course=None):
    """Aggregate in SQLite; never load answer text or change learning state."""
    entries = {c['id']: c for c in course_catalog()}
    if current_course is not None:
        entries[current_course.id] = {
            'id': current_course.id, 'title': current_course.title,
            'lesson_ids': [l['id'] for l in current_course.lessons],
            'lessons': len(current_course.lessons), 'questions': len(current_course.questions)}
    rows = {}

    def row(cid):
        if cid not in rows:
            metadata = entries.get(cid, {'id': cid, 'title': cid + ' (saved history)',
                                         'lesson_ids': None, 'lessons': None, 'questions': None})
            rows[cid] = dict(metadata, attempts=0, correct=0, seen=0, done=0, due=0,
                             exams=0, passed_exams=0, modes={}, activity={}, attempted=False)
        return rows[cid]

    for cid in entries:
        row(cid)
    for r in store.db.execute(f'''SELECT {COURSE_OF_Q} AS course, mode,
                COUNT(*) AS n, SUM(correct) AS correct FROM attempts GROUP BY course,mode'''):
        item = row(r['course'])
        item['attempted'] = True
        item['attempts'] += r['n']
        item['correct'] += r['correct']
        item['modes'][r['mode']] = (r['correct'], r['n'])
    # Include older progress even when no individual answer log survives.
    for r in store.db.execute(f'''SELECT {COURSE_OF_Q} AS course, COUNT(*) AS n FROM
                (SELECT qid FROM attempts UNION SELECT qid FROM progress WHERE attempts>0)
                GROUP BY course'''):
        row(r['course'])['seen'] = r['n']
        row(r['course'])['attempted'] = True
    for r in store.db.execute(f'SELECT {COURSE_OF_L} AS course, lid FROM completed'):
        item = row(r['course'])
        item['attempted'] = True
        if item['lesson_ids'] is None or r['lid'].split(':', 1)[1] in item['lesson_ids']:
            item['done'] += 1
    for r in store.db.execute(f'''SELECT {COURSE_OF_Q} AS course, COUNT(*) AS n
                FROM reviews WHERE due<=? GROUP BY course''', (store.clock(),)):
        row(r['course'])['due'] = r['n']
        row(r['course'])['attempted'] = True
    for r in store.db.execute('SELECT course,state,COUNT(*) AS n FROM exams GROUP BY course,state'):
        item = row(r['course'])
        item['attempted'] = True
        if r['state'] in ('passed', 'failed'):
            item['exams'] += r['n']
        if r['state'] == 'passed':
            item['passed_exams'] += r['n']
    today = datetime.fromtimestamp(store.clock()).date()
    days = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    start = datetime.combine(today - timedelta(days=6), datetime.min.time()).timestamp()
    for r in store.db.execute(f'''SELECT {COURSE_OF_Q} AS course,
                date(at,'unixepoch','localtime') AS day, COUNT(*) AS n
                FROM attempts WHERE at>=? AND at<=? GROUP BY course,day''', (start, store.clock())):
        row(r['course'])['activity'][r['day']] = r['n']
    return {'courses': rows, 'days': days}


def bar(value, maximum, width=20):
    filled = min(width, round(width * value / maximum)) if maximum else 0
    if value > 0 and maximum > 0:
        filled = max(1, filled)
    return '█' * filled + '░' * (width - filled)


def report(data, course_id=None):
    if course_id is not None and course_id not in data['courses']:
        raise ValueError('No analytics for that course.')
    items = [data['courses'][course_id]] if course_id else list(data['courses'].values())
    total = lambda key: sum(c[key] for c in items)
    attempts, correct = total('attempts'), total('correct')
    accuracy = f'{100 * correct / attempts:.1f}%' if attempts else 'N/A'
    lines = ['ALL COURSES' if course_id is None else items[0]['title'],
             f"Courses attempted: {sum(c['attempted'] for c in items)}/{len(items)}",
             f'Answers: {attempts} · Correct: {correct} · Wrong/skipped: {attempts-correct}',
             f'Answer accuracy: {accuracy} · Unique questions seen: {total("seen")}',
             f'Lessons completed: {total("done")} · Reviews due: {total("due")}',
             f'Exams passed/finished: {total("passed_exams")}/{total("exams")}', '']
    if not any(c['attempted'] for c in items):
        lines += ['No activity yet. Start a lesson or exam to build your graphs.', '']
    lines.append('LESSON COMPLETION · each bar = 100%')
    for c in items:
        if not c['attempted']:
            continue
        lines.append(c['title'])
        if c['lessons'] is None:
            lines.append(f'  {c["done"]} done · course size unavailable')
        else:
            lines.append(f'  {bar(c["done"], c["lessons"])} {c["done"]}/{c["lessons"]}')
    lines += ['', 'ACCURACY BY MODE · each bar = 100%']
    modes = sorted({mode for c in items for mode in c['modes']})
    for mode in modes:
        right = sum(c['modes'].get(mode, (0, 0))[0] for c in items)
        count = sum(c['modes'].get(mode, (0, 0))[1] for c in items)
        lines += [mode, f'  {bar(right,count)} {100*right/count:.1f}% ({right}/{count})']
    if not modes:
        lines.append('No recorded answers.')
    activity = [sum(c['activity'].get(day, 0) for c in items) for day in data['days']]
    maximum = max(activity, default=0)
    lines += ['', f'LAST 7 DAYS · answers · full bar = {maximum or 1}']
    for day, count in zip(data['days'], activity):
        lines.append(f'{day[5:]} {bar(count, maximum)} {count}')
    lines += ['', 'Accuracy includes retries and skips in recorded answers.',
              'Completed lessons include section exam passes.',
              'Activity uses local calendar dates; filters do not change your course.']
    return '\n'.join(lines)
