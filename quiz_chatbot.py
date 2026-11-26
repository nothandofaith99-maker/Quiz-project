"""A small command-line quiz chatbot with no third-party dependencies."""

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional, Tuple


DIFFICULTY_LEVELS = ("Easy", "Medium", "Hard")


@dataclass(frozen=True)
class Question:
    prompt: str
    choices: Tuple[str, ...]
    answer: int
    difficulty: str = "Easy"
    explanation: str = ""

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("Question prompt cannot be empty.")
        if len(self.choices) < 2:
            raise ValueError("Each question must have at least two choices.")
        if not 0 <= self.answer < len(self.choices):
            raise ValueError("Answer must be the index of one of the choices.")
        if self.difficulty not in DIFFICULTY_LEVELS:
            raise ValueError("Difficulty must be Easy, Medium, or Hard.")


DEFAULT_QUESTIONS = (
    Question(
        "Which planet is known as the Red Planet?",
        ("Earth", "Mars", "Venus", "Jupiter"),
        1,
    ),
    Question(
        "What is 5 multiplied by 6?",
        ("11", "25", "30", "56"),
        2,
    ),
    Question(
        "Which language is this quiz chatbot written in?",
        ("Java", "Python", "C++", "Ruby"),
        1,
    ),
)

SUBJECT_QUESTIONS: Dict[str, Tuple[Question, ...]] = {
    "Mathematics": (
        Question("What is 7 + 5?", ("10", "11", "12", "13"), 2, "Easy",
                 "7 + 5 = 12."),
        Question("Solve for x: 4x - 7 = 13.", ("4", "5", "6", "7"), 1, "Medium",
                 "Add 7 to both sides to get 4x = 20, then divide by 4."),
        Question(
            "A right triangle has legs of 9 cm and 12 cm. What is its area?",
            ("42 cm²", "48 cm²", "54 cm²", "108 cm²"),
            2,
            "Hard",
            "The area of a right triangle is 1/2 times the product of its legs: 1/2 x 9 x 12 = 54 cm².",
        ),
    ),
    "Science": (
        Question(
            "What is the chemical formula for water?",
            ("CO₂", "H₂O", "O₂", "NaCl"),
            1,
            "Easy",
        ),
        Question(
            "What force accelerates a 2 kg object at 3 m/s²?",
            ("1.5 N", "5 N", "6 N", "9 N"),
            2,
            "Medium",
        ),
        Question(
            "If two heterozygous parents have a recessive trait, what is the chance "
            "their child shows that trait?",
            ("0%", "25%", "50%", "75%"),
            1,
            "Hard",
        ),
    ),
    "Geography": (
        Question(
            "Which is the largest ocean on Earth?",
            ("Atlantic", "Indian", "Arctic", "Pacific"),
            3,
            "Easy",
        ),
        Question(
            "Which river flows through Paris?",
            ("Seine", "Danube", "Tiber", "Thames"),
            0,
            "Medium",
        ),
        Question(
            "Which strait connects the Black Sea to the Sea of Marmara?",
            ("Gibraltar", "Bosporus", "Bering", "Malacca"),
            1,
            "Hard",
        ),
    ),
    "History": (
        Question(
            "The ancient pyramids of Giza are in which country?",
            ("Egypt", "Greece", "Mexico", "India"),
            0,
            "Easy",
        ),
        Question(
            "In what year was the Magna Carta agreed?",
            ("1066", "1215", "1492", "1776"),
            1,
            "Medium",
        ),
        Question(
            "Which 1648 settlement ended the Thirty Years' War?",
            (
                "Treaty of Versailles",
                "Peace of Westphalia",
                "Congress of Vienna",
                "Treaty of Utrecht",
            ),
            1,
            "Hard",
        ),
    ),
    "English": (
        Question(
            "What is the past tense of 'go'?",
            ("Goed", "Gone", "Went", "Going"),
            2,
            "Easy",
        ),
        Question(
            "Choose the correct word: 'Neither of the students ___ submitted the form.'",
            ("have", "has", "are", "were"),
            1,
            "Medium",
        ),
        Question(
            "What figure of speech is used in 'The wind whispered through the trees'?",
            ("Simile", "Hyperbole", "Personification", "Alliteration"),
            2,
            "Hard",
        ),
    ),
    "Computer Science": (
        Question(
            "What is 5 written in binary?",
            ("101", "110", "111", "1001"),
            0,
            "Easy",
        ),
        Question(
            "What does HTML stand for?",
            (
                "HyperText Markup Language",
                "High Transfer Machine Language",
                "Hyperlink Text Management Language",
                "Home Tool Markup Language",
            ),
            0,
            "Medium",
        ),
        Question(
            "What is the time complexity of binary search on a sorted array?",
            ("O(1)", "O(log n)", "O(n)", "O(n²)"),
            1,
            "Hard",
        ),
    ),
}


class QuizChatbot:
    def __init__(self, questions: Iterable[Question] = DEFAULT_QUESTIONS) -> None:
        self.questions = tuple(questions)
        if not self.questions:
            raise ValueError("The quiz must contain at least one question.")

    @staticmethod
    def _parse_answer(response: str, choices: Tuple[str, ...]) -> Optional[int]:
        value = response.strip().casefold()
        if len(value) == 1 and "a" <= value <= "z":
            index = ord(value) - ord("a")
            if index < len(choices):
                return index
        for index, choice in enumerate(choices):
            if value == choice.strip().casefold():
                return index
        return None

    def run(
        self,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> Tuple[int, int]:
        """Run the quiz and return (correct answers, questions attempted)."""
        output_fn("QuizBot: Hi! Let's take a quick quiz.")
        output_fn("Type a letter or an answer. You can also type 'skip' or 'quit'.")
        score = 0
        attempted = 0

        for number, question in enumerate(self.questions, start=1):
            output_fn("")
            output_fn("QuizBot: Question {}: {}".format(number, question.prompt))
            for index, choice in enumerate(question.choices):
                output_fn("  {}) {}".format(chr(ord("A") + index), choice))

            while True:
                response = input_fn("You: ").strip()
                command = response.casefold()
                if command in ("quit", "exit"):
                    output_fn("QuizBot: Thanks for playing!")
                    self._show_result(score, attempted, len(self.questions), output_fn)
                    return score, attempted
                if command == "skip":
                    output_fn("QuizBot: Skipped.")
                    break

                selected = self._parse_answer(response, question.choices)
                if selected is None:
                    output_fn("QuizBot: Please enter a listed letter or answer, 'skip', or 'quit'.")
                    continue

                attempted += 1
                if selected == question.answer:
                    score += 1
                    output_fn("QuizBot: Correct!")
                else:
                    correct = question.choices[question.answer]
                    output_fn("QuizBot: Not quite. The answer is {}.".format(correct))
                if question.explanation:
                    output_fn("QuizBot: {}".format(question.explanation))
                break

        output_fn("")
        output_fn("QuizBot: That's the end of the quiz.")
        self._show_result(score, attempted, len(self.questions), output_fn)
        return score, attempted

    @staticmethod
    def _show_result(
        score: int,
        attempted: int,
        total: int,
        output_fn: Callable[[str], None],
    ) -> None:
        output_fn(
            "QuizBot: Your score is {}/{} ({} attempted, {} total).".format(
                score, attempted, attempted, total
            )
        )


def main() -> None:
    QuizChatbot().run()


if __name__ == "__main__":
    main()
