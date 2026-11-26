# QuizBot

A lightweight quiz desktop app written in Python. Its graphical interface uses
Tkinter, which is included with most Python installations; no third-party
packages are required.

## Run

### Windows

Double-click `quiz_chatbot.bat` to open the quiz app. Python 3 with Tkinter
must be installed.

You can also start the app from a terminal:

```text
python quiz_app.py
```

### Other platforms

Run `python quiz_app.py` in a terminal.

Click an answer, use **Skip** to move on, and **Play again** to restart after
the results. Choose from Mathematics, Science, Geography, History, English,
and Computer Science. Questions progress from Easy to Medium to Hard. At the
end of a quiz, you can replay the subject or choose another one. Mixed quizzes
shuffle questions and answer choices; Adaptive mode adjusts the next difficulty
from your streak. Each question
now includes an explanation shown after an answer, and the final review screen
shows each response, the correct answer, difficulty, and average answer time.
has a 15-second timer. The quiz advances after a short answer-feedback message,
or automatically when time runs out; timed-out questions count as unanswered.
Use one **50:50 lifeline** per quiz to remove two wrong choices. Correct
answers build a streak, and the results show your best streak with a playful
finish message. Enter a player name before starting; results are saved locally
and the score history appears on the subject screen. Select a row to delete one
score, delete every score for that player, or clear the full leaderboard. Each
delete action asks for confirmation. On Windows, scores are stored in
`%LOCALAPPDATA%\QuizBot\scores.json`.
The command-line chatbot is still available with `python quiz_chatbot.py`.

Edit `SUBJECT_QUESTIONS` in `quiz_chatbot.py` to change or add subjects.
Each `Question` takes a prompt, a tuple of choices, the zero-based index of
the correct choice, and its difficulty (`Easy`, `Medium`, or `Hard`).

## Test

```text
python -m unittest
```
