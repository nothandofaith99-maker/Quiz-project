import unittest

from quiz_chatbot import DIFFICULTY_LEVELS, SUBJECT_QUESTIONS, Question, QuizChatbot


class QuizChatbotTests(unittest.TestCase):
    def setUp(self):
        self.bot = QuizChatbot(
            (
                Question("Pick blue.", ("Red", "Blue"), 1),
                Question("Pick two.", ("One", "Two"), 1),
            )
        )

    def run_bot(self, responses):
        remaining = iter(responses)
        output = []
        result = self.bot.run(
            input_fn=lambda _prompt: next(remaining),
            output_fn=output.append,
        )
        return result, output

    def test_accepts_letter_and_answer_text(self):
        result, output = self.run_bot(("b", "Two"))
        self.assertEqual(result, (2, 2))
        self.assertEqual(sum("Correct!" in line for line in output), 2)

    def test_invalid_input_reprompts_without_counting_attempt(self):
        result, output = self.run_bot(("maybe", "A", "B"))
        self.assertEqual(result, (1, 2))
        self.assertTrue(any("Please enter a listed" in line for line in output))

    def test_skip_and_quit(self):
        result, output = self.run_bot(("skip", "quit"))
        self.assertEqual(result, (0, 0))
        self.assertTrue(any("Thanks for playing!" in line for line in output))

    def test_rejects_empty_quiz(self):
        with self.assertRaises(ValueError):
            QuizChatbot(())

    def test_rejects_invalid_answer_index(self):
        with self.assertRaises(ValueError):
            Question("Invalid", ("One", "Two"), 2)

    def test_subjects_have_questions_in_easy_to_hard_order(self):
        self.assertGreaterEqual(len(SUBJECT_QUESTIONS), 3)
        for questions in SUBJECT_QUESTIONS.values():
            self.assertEqual(len(questions), len(DIFFICULTY_LEVELS))
            self.assertEqual(
                tuple(question.difficulty for question in questions),
                DIFFICULTY_LEVELS,
            )

    def test_rejects_unknown_difficulty(self):
        with self.assertRaises(ValueError):
            Question("Invalid", ("One", "Two"), 0, "Expert")


if __name__ == "__main__":
    unittest.main()
