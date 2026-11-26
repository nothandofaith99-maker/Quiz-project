import tempfile
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from quiz_app import QUESTION_TIME_SECONDS, QuizApp
from score_store import ScoreStore


class QuizAppTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.temporary_directory = tempfile.TemporaryDirectory()
        score_store = ScoreStore(Path(self.temporary_directory.name) / "scores.json")
        self.app = QuizApp(self.root, score_store)
        self.app.name_entry.insert(0, "Test Player")
        self.app.start_quiz()

    def tearDown(self):
        self.app.cancel_pending_callbacks()
        self.root.destroy()
        self.temporary_directory.cleanup()

    def fire_advance(self):
        self.root.after_cancel(self.app.advance_after_id)
        self.app.advance_after_id = None
        self.app.advance_automatically()

    def test_answer_advances_and_resets_the_timer(self):
        question = self.app.questions[0]
        self.app.answer(question.answer)
        self.assertIsNotNone(self.app.advance_after_id)
        self.assertIsNone(self.app.timer_after_id)

        self.fire_advance()

        self.assertEqual(self.app.question_index, 1)
        self.assertEqual(self.app.score, 1)
        self.assertEqual(self.app.remaining_seconds, QUESTION_TIME_SECONDS)
        self.assertIsNotNone(self.app.timer_after_id)

    def test_timeout_marks_question_unanswered_and_advances(self):
        self.app.cancel_timer()
        self.app.remaining_seconds = 1

        self.app.update_timer()

        self.assertTrue(self.app.answered)
        self.assertEqual(self.app.attempted, 0)
        self.assertIn("unanswered", self.app.feedback.cget("text"))
        self.assertIsNotNone(self.app.advance_after_id)

        self.fire_advance()

        self.assertEqual(self.app.question_index, 1)
        self.assertEqual(self.app.attempted, 0)
        self.assertEqual(self.app.remaining_seconds, QUESTION_TIME_SECONDS)

    def test_fifty_fifty_lifeline_keeps_the_correct_answer(self):
        question = self.app.questions[0]

        self.app.use_lifeline()

        visible_choices = [
            index
            for index, button in enumerate(self.app.choice_buttons)
            if button.winfo_manager()
        ]
        visible_original_choices = [
            self.app.choice_mapping[index] for index in visible_choices
        ]
        self.assertTrue(self.app.lifeline_used)
        self.assertEqual(len(visible_choices), 2)
        self.assertIn(question.answer, visible_original_choices)
        self.assertEqual(str(self.app.lifeline_button["state"]), "disabled")

    def test_streak_increments_for_correct_answers_and_resets_on_wrong_answer(self):
        question = self.app.questions[0]
        self.app.answer(question.answer)
        self.assertEqual(self.app.streak, 1)

        self.fire_advance()
        next_question = self.app.questions[1]
        wrong_answer = (next_question.answer + 1) % len(next_question.choices)
        self.app.answer(wrong_answer)

        self.assertEqual(self.app.streak, 0)
        self.assertEqual(self.app.best_streak, 1)

    def test_result_is_saved_once_with_the_player_name(self):
        self.app.skip()
        self.app.skip()
        self.app.skip()

        records = self.app.score_store.load_scores()

        self.assertIn("Test Player", self.app.prompt.cget("text"))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "Test Player")
        self.assertEqual((records[0].score, records[0].total), (0, 3))

        self.app.show_results()
        self.assertEqual(len(self.app.score_store.load_scores()), 1)

    def test_score_history_shows_all_records_in_ranked_order(self):
        self.app.score_store.add_score("Sam", "History", 1, 3)
        self.app.score_store.add_score("Alex", "Science", 3, 3)

        self.app.refresh_leaderboard()

        rows = self.app.leaderboard_table.get_children()
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            self.app.leaderboard_table.item(rows[0], "values")[1],
            "Alex",
        )

    def test_answer_history_records_explanation_and_review(self):
        question = self.app.questions[0]

        self.app.answer(question.answer)
        self.fire_advance()
        self.app.skip()
        self.app.show_results()
        self.app.toggle_answer_review()

        self.assertEqual(len(self.app.answer_history), 2)
        self.assertEqual(self.app.answer_history[0]["status"], "Correct")
        self.assertTrue(self.app.answer_history[0]["explanation"])
        self.assertTrue(self.app.review_frame.winfo_manager())

    def test_quiz_modes_filter_or_adapt_difficulty(self):
        self.app.mode_picker.set("Hard")
        self.app.start_quiz()

        self.assertEqual(len(self.app.questions), 1)
        self.assertEqual(self.app.questions[0].difficulty, "Hard")

    def test_selected_score_can_be_deleted(self):
        self.app.score_store.add_score("Sam", "History", 1, 3)
        self.app.score_store.add_score("Alex", "Science", 3, 3)
        self.app.refresh_leaderboard()
        alex_row = self.app.leaderboard_table.get_children()[0]
        self.app.leaderboard_table.selection_set(alex_row)

        with patch("quiz_app.messagebox.askyesno", return_value=True):
            self.app.delete_selected_score()

        records = self.app.score_store.load_scores()
        self.assertEqual([record.name for record in records], ["Sam"])

    def test_selected_player_scores_can_be_deleted(self):
        self.app.score_store.add_score("Alex", "Science", 2, 3)
        self.app.score_store.add_score("Alex", "History", 3, 3)
        self.app.score_store.add_score("Sam", "History", 1, 3)
        self.app.refresh_leaderboard()
        alex_row = next(
            row
            for row in self.app.leaderboard_table.get_children()
            if self.app.leaderboard_table.item(row, "values")[1] == "Alex"
        )
        self.app.leaderboard_table.selection_set(alex_row)

        with patch("quiz_app.messagebox.askyesno", return_value=True):
            self.app.delete_selected_player()

        records = self.app.score_store.load_scores()
        self.assertEqual([record.name for record in records], ["Sam"])

    def test_clear_all_scores_can_delete_the_leaderboard(self):
        self.app.score_store.add_score("Sam", "History", 1, 3)
        self.app.score_store.add_score("Alex", "Science", 3, 3)
        self.app.refresh_leaderboard()

        with patch("quiz_app.messagebox.askyesno", return_value=True):
            self.app.clear_all_scores()

        self.assertEqual(self.app.score_store.load_scores(), ())


if __name__ == "__main__":
    unittest.main()
