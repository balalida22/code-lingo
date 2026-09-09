"""Progress counts distinct problems, so retrying never inflates the total."""


class SessionProgress:
    def __init__(self, mode, questions, initial=None):
        self.mode = mode
        self.replay_lid = None
        self.states = {q['id']: None for q in questions}
        for key, value in (initial or {}).items():
            if key in self.states:
                self.states[key] = value

    def mark(self, qid, correct):
        if qid in self.states:
            self.states[qid] = bool(correct)

    @property
    def counts(self):
        values = list(self.states.values())
        return (sum(v is True for v in values), sum(v is False for v in values),
                sum(v is None for v in values))

    @property
    def total(self):
        return len(self.states)

    @property
    def percent(self):
        correct, wrong, _ = self.counts
        return (correct + wrong) * 100 // self.total if self.total else 0
