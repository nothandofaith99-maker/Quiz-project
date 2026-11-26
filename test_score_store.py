import json
import tempfile
import unittest
from pathlib import Path

from score_store import ScoreStore, ScoreStoreError


class ScoreStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary_directory.name) / "scores.json"
        self.store = ScoreStore(self.path)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_saves_and_loads_scores(self):
        self.store.add_score("Alex", "Science", 2, 3)

        records = ScoreStore(self.path).load_scores()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "Alex")
        self.assertEqual(records[0].subject, "Science")
        self.assertEqual((records[0].score, records[0].total), (2, 3))

    def test_leaderboard_orders_highest_score_first(self):
        self.store.add_score("Sam", "History", 1, 3)
        self.store.add_score("Lee", "Mathematics", 3, 3)

        leaderboard = self.store.leaderboard()

        self.assertEqual([record.name for record in leaderboard], ["Lee", "Sam"])

    def test_rejects_corrupted_score_file(self):
        self.path.write_text(json.dumps([{"name": "Alex"}]), encoding="utf-8")

        with self.assertRaises(ScoreStoreError):
            self.store.load_scores()

    def test_deletes_only_the_selected_score(self):
        self.store.add_score("Alex", "Science", 2, 3)
        self.store.add_score("Sam", "History", 3, 3)

        deleted = self.store.delete_score(0)

        self.assertEqual(deleted.name, "Alex")
        self.assertEqual([record.name for record in self.store.load_scores()], ["Sam"])

    def test_deletes_all_scores_for_a_player_case_insensitively(self):
        self.store.add_score("Alex", "Science", 2, 3)
        self.store.add_score("alex", "History", 1, 3)
        self.store.add_score("Sam", "History", 3, 3)

        deleted_count = self.store.delete_player("ALEX")

        self.assertEqual(deleted_count, 2)
        self.assertEqual([record.name for record in self.store.load_scores()], ["Sam"])

    def test_clears_all_scores(self):
        self.store.add_score("Alex", "Science", 2, 3)
        self.store.add_score("Sam", "History", 3, 3)

        deleted_count = self.store.clear_scores()

        self.assertEqual(deleted_count, 2)
        self.assertEqual(self.store.load_scores(), ())


if __name__ == "__main__":
    unittest.main()
