import tempfile
import unittest
from pathlib import Path
from codelingo.store import Store


class PracticeHeartTests(unittest.TestCase):
    def setUp(self):
        self.store = Store(':memory:', lambda: 1000000)
        self.store.db.execute('UPDATE player SET hearts=0')
        self.store.db.commit()

    def tearDown(self):
        self.store.close()

    def answer(self, correct=True, mode='practice'):
        return self.store.record('python:q','answer',correct,mode)

    def test_five_correct_per_heart_and_repeat(self):
        for i in range(10):
            result = self.answer()
            self.assertEqual(result['hearts'], (i+1)//5)
            self.assertEqual(result['heart_earned'], (i+1)%5 == 0)
            self.assertEqual(self.store.practice_heart_progress(), (i+1)%5)
        self.assertIn('One heart earned', self.store.practice_heart_message(result))

    def test_mistakes_do_not_count_or_reset_progress(self):
        self.answer(); self.answer(False)
        self.assertEqual(self.store.practice_heart_progress(), 1)
        self.assertIn('1/5', self.store.practice_heart_message(self.answer(False)))
        for _ in range(4): result = self.answer()
        self.assertEqual(result['hearts'], 1)

    def test_full_hearts_do_not_bank_correct_answers(self):
        self.store.db.execute('UPDATE player SET hearts=5')
        for _ in range(6): self.answer()
        self.assertEqual(self.store.practice_heart_progress(), 0)
        self.answer(False)
        for _ in range(4): result = self.answer()
        self.assertEqual(result['hearts'], 4)
        self.assertEqual(self.answer()['hearts'], 5)

    def test_progress_survives_restart_and_courses(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'progress.db'
            with_store = Store(path, lambda: 1000000)
            with_store.db.execute('UPDATE player SET hearts=0')
            for _ in range(3): with_store.record('python:q','a',True,'practice')
            with_store.close()
            with_store = Store(path, lambda: 1000000)
            for _ in range(2): result = with_store.record('rust:q','a',True,'practice')
            self.assertEqual(result['hearts'], 1)
            with_store.close()

    def test_other_modes_do_not_count_toward_practice(self):
        self.answer(mode='review')
        self.answer(mode='learn')
        self.answer(mode='exam')
        self.assertEqual(self.store.practice_heart_progress(), 0)
        self.assertEqual(self.store.player()['hearts'], 1)
