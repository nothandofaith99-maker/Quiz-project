"""Tkinter desktop interface for QuizBot."""

import random
import tkinter as tk
import time
from tkinter import messagebox, ttk
from typing import Optional

from score_store import ScoreStore, ScoreStoreError
from quiz_chatbot import SUBJECT_QUESTIONS


QUESTION_TIME_SECONDS = 15
FEEDBACK_DELAY_MS = 1500
MAX_PLAYER_NAME_LENGTH = 30
CORRECT_MESSAGES = (
    "Brilliant! Moving to the next question...",
    "You're on fire! Moving to the next question...",
    "Correct! Keep that streak going...",
)


class QuizApp:
    def __init__(
        self, root: tk.Tk, score_store: Optional[ScoreStore] = None
    ) -> None:
        self.root = root
        self.score_store = score_store if score_store is not None else ScoreStore()
        self.questions = ()
        self.subject = ""
        self.player_name = ""
        self.question_index = 0
        self.score = 0
        self.attempted = 0
        self.score_saved = False
        self.streak = 0
        self.best_streak = 0
        self.lifeline_used = False
        self.answered = False
        self.remaining_seconds = QUESTION_TIME_SECONDS
        self.timer_after_id = None
        self.advance_after_id = None
        self.answer_history = []
        self.choice_mapping = []
        self.question_started_at = 0
        self.response_times = []

        root.title("QuizBot")
        root.geometry("700x680")
        root.minsize(540, 600)
        root.configure(bg="#f2f5fb")

        header = tk.Frame(root, bg="#243b6b", padx=28, pady=20)
        header.pack(fill="x")
        tk.Label(
            header,
            text="QuizBot",
            font=("Segoe UI", 22, "bold"),
            fg="white",
            bg="#243b6b",
        ).pack(anchor="w")
        tk.Label(
            header,
            text="A little quiz, one question at a time.",
            font=("Segoe UI", 10),
            fg="#dce6ff",
            bg="#243b6b",
        ).pack(anchor="w", pady=(3, 0))

        content = tk.Frame(root, bg="#f2f5fb", padx=32, pady=28)
        content.pack(fill="both", expand=True)

        self.selection_frame = tk.Frame(content, bg="#f2f5fb")
        self.selection_frame.pack(fill="both", expand=True)
        tk.Label(
            self.selection_frame,
            text="Player name",
            font=("Segoe UI", 10, "bold"),
            fg="#1c2940",
            bg="#f2f5fb",
        ).pack(anchor="w", pady=(8, 5))
        self.name_entry = tk.Entry(
            self.selection_frame,
            font=("Segoe UI", 11),
        )
        self.name_entry.pack(fill="x", pady=(0, 14), ipady=5)
        tk.Label(
            self.selection_frame,
            text="Choose a subject",
            font=("Segoe UI", 18, "bold"),
            fg="#1c2940",
            bg="#f2f5fb",
        ).pack(anchor="w", pady=(0, 8))
        tk.Label(
            self.selection_frame,
            text="Each quiz gets harder as you go. You have 15 seconds per question.",
            font=("Segoe UI", 10),
            fg="#53627a",
            bg="#f2f5fb",
        ).pack(anchor="w", pady=(0, 18))
        self.subject_picker = ttk.Combobox(
            self.selection_frame,
            values=tuple(SUBJECT_QUESTIONS),
            state="readonly",
            font=("Segoe UI", 11),
        )
        self.subject_picker.current(0)
        self.subject_picker.pack(fill="x", pady=(0, 14), ipady=5)
        tk.Label(
            self.selection_frame,
            text="Quiz mode",
            font=("Segoe UI", 10, "bold"),
            fg="#1c2940",
            bg="#f2f5fb",
        ).pack(anchor="w", pady=(0, 5))
        self.mode_picker = ttk.Combobox(
            self.selection_frame,
            values=("Mixed", "Adaptive", "Easy", "Medium", "Hard"),
            state="readonly",
            font=("Segoe UI", 11),
        )
        self.mode_picker.current(0)
        self.mode_picker.pack(fill="x", pady=(0, 14), ipady=5)
        tk.Button(
            self.selection_frame,
            text="Start quiz",
            font=("Segoe UI", 10, "bold"),
            command=self.start_quiz,
            bg="#3158a5",
            fg="white",
            activebackground="#274887",
            activeforeground="white",
            padx=18,
            pady=9,
            relief="flat",
            cursor="hand2",
        ).pack(anchor="e")
        tk.Label(
            self.selection_frame,
            text="Score history & leaderboard",
            font=("Segoe UI", 14, "bold"),
            fg="#1c2940",
            bg="#f2f5fb",
        ).pack(anchor="w", pady=(18, 8))
        tk.Label(
            self.selection_frame,
            text="Select a score to remove it, or remove all scores for a player.",
            font=("Segoe UI", 9),
            fg="#53627a",
            bg="#f2f5fb",
        ).pack(anchor="w", pady=(0, 5))
        score_table_frame = tk.Frame(self.selection_frame, bg="#f2f5fb")
        score_table_frame.pack(fill="both", expand=True)
        self.leaderboard_table = ttk.Treeview(
            score_table_frame,
            columns=("rank", "name", "subject", "score", "date"),
            show="headings",
            height=6,
        )
        for column, heading, width in (
            ("rank", "#", 42),
            ("name", "Player", 140),
            ("subject", "Subject", 160),
            ("score", "Score", 75),
            ("date", "Date", 105),
        ):
            self.leaderboard_table.heading(column, text=heading)
            self.leaderboard_table.column(
                column,
                width=width,
                anchor="center" if column in ("rank", "score") else "w",
            )
        leaderboard_scrollbar = ttk.Scrollbar(
            score_table_frame,
            orient="vertical",
            command=self.leaderboard_table.yview,
        )
        self.leaderboard_table.configure(yscrollcommand=leaderboard_scrollbar.set)
        self.leaderboard_table.pack(side="left", fill="both", expand=True)
        leaderboard_scrollbar.pack(side="right", fill="y")
        score_actions = tk.Frame(self.selection_frame, bg="#f2f5fb")
        score_actions.pack(fill="x", pady=(7, 0))
        self.delete_score_button = tk.Button(
            score_actions,
            text="Delete score",
            command=self.delete_selected_score,
            padx=8,
            pady=5,
        )
        self.delete_score_button.pack(side="left")
        self.delete_player_button = tk.Button(
            score_actions,
            text="Delete player",
            command=self.delete_selected_player,
            padx=8,
            pady=5,
        )
        self.delete_player_button.pack(side="left", padx=(6, 0))
        self.clear_scores_button = tk.Button(
            score_actions,
            text="Clear all scores",
            command=self.clear_all_scores,
            padx=8,
            pady=5,
        )
        self.clear_scores_button.pack(side="right")
        self.leaderboard_status = tk.Label(
            self.selection_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#53627a",
            bg="#f2f5fb",
            anchor="w",
        )
        self.leaderboard_status.pack(fill="x", pady=(5, 0))
        self.refresh_leaderboard()

        self.quiz_frame = tk.Frame(content, bg="#f2f5fb")

        status_frame = tk.Frame(self.quiz_frame, bg="#f2f5fb")
        status_frame.pack(fill="x", pady=(0, 12))
        self.progress = tk.Label(
            status_frame,
            font=("Segoe UI", 10, "bold"),
            fg="#53627a",
            bg="#f2f5fb",
        )
        self.progress.pack(side="left", anchor="w")
        self.timer_label = tk.Label(
            status_frame,
            font=("Segoe UI", 10, "bold"),
            fg="#b42318",
            bg="#f2f5fb",
        )
        self.timer_label.pack(side="right", anchor="e")

        self.prompt = tk.Label(
            self.quiz_frame,
            font=("Segoe UI", 16, "bold"),
            fg="#1c2940",
            bg="white",
            padx=20,
            pady=20,
            justify="left",
            wraplength=540,
            anchor="w",
        )
        self.prompt.pack(fill="x")

        self.choices_frame = tk.Frame(self.quiz_frame, bg="#f2f5fb")
        self.choices_frame.pack(fill="x", pady=(18, 8))
        self.choice_buttons = []
        choice_count = max(
            len(question.choices)
            for questions in SUBJECT_QUESTIONS.values()
            for question in questions
        )
        for index in range(choice_count):
            button = tk.Button(
                self.choices_frame,
                text="",
                font=("Segoe UI", 11),
                anchor="w",
                padx=14,
                pady=9,
                bg="white",
                fg="#243b6b",
                activebackground="#e7edfa",
                relief="solid",
                bd=1,
                cursor="hand2",
                command=lambda choice=index: self.answer(choice, choice_is_display=True),
            )
            button.pack(fill="x", pady=4)
            self.choice_buttons.append(button)

        self.feedback = tk.Label(
            self.quiz_frame,
            text="Choose an answer to start.",
            font=("Segoe UI", 10),
            fg="#53627a",
            bg="#f2f5fb",
            anchor="w",
        )
        self.feedback.pack(fill="x", pady=(2, 12))

        controls = tk.Frame(self.quiz_frame, bg="#f2f5fb")
        controls.pack(fill="x", side="bottom")
        self.skip_button = tk.Button(
            controls,
            text="Skip",
            font=("Segoe UI", 10),
            command=self.skip,
            padx=14,
            pady=7,
        )
        self.skip_button.pack(side="left")
        self.lifeline_button = tk.Button(
            controls,
            text="50:50 lifeline",
            font=("Segoe UI", 10),
            command=self.use_lifeline,
            padx=14,
            pady=7,
        )
        self.next_button = tk.Button(
            controls,
            text="Next",
            font=("Segoe UI", 10, "bold"),
            command=self.next_question,
            bg="#3158a5",
            fg="white",
            activebackground="#274887",
            activeforeground="white",
            padx=18,
            pady=7,
            relief="flat",
            cursor="hand2",
            state="disabled",
        )
        self.next_button.pack(side="right")
        self.restart_button = tk.Button(
            controls,
            text="Play again",
            font=("Segoe UI", 10, "bold"),
            command=self.restart,
            bg="#3158a5",
            fg="white",
            activebackground="#274887",
            activeforeground="white",
            padx=18,
            pady=7,
            relief="flat",
            cursor="hand2",
        )
        self.subject_button = tk.Button(
            controls,
            text="Choose another subject",
            font=("Segoe UI", 10),
            command=self.choose_subject,
            padx=14,
            pady=7,
        )
        self.review_button = tk.Button(
            controls,
            text="Review answers",
            font=("Segoe UI", 10),
            command=self.toggle_answer_review,
            padx=14,
            pady=7,
        )

        self.review_frame = tk.Frame(self.quiz_frame, bg="#f2f5fb")
        review_table_frame = tk.Frame(self.review_frame, bg="#f2f5fb")
        review_table_frame.pack(fill="both", expand=True)
        self.review_table = ttk.Treeview(
            review_table_frame,
            columns=("number", "status", "difficulty", "answer"),
            show="headings",
            height=5,
        )
        for column, heading, width in (
            ("number", "#", 35),
            ("status", "Result", 75),
            ("difficulty", "Level", 75),
            ("answer", "Question / Answer", 430),
        ):
            self.review_table.heading(column, text=heading)
            self.review_table.column(column, width=width, anchor="w")
        review_scrollbar = ttk.Scrollbar(
            review_table_frame,
            orient="vertical",
            command=self.review_table.yview,
        )
        self.review_table.configure(yscrollcommand=review_scrollbar.set)
        self.review_table.pack(side="left", fill="both", expand=True)
        review_scrollbar.pack(side="right", fill="y")

    def start_quiz(self) -> None:
        player_name = self.name_entry.get().strip()
        if not player_name:
            messagebox.showerror(
                "Name required",
                "Enter a player name before starting the quiz.",
                parent=self.root,
            )
            self.name_entry.focus_set()
            return
        if len(player_name) > MAX_PLAYER_NAME_LENGTH:
            messagebox.showerror(
                "Name too long",
                "Player names must be {} characters or fewer.".format(
                    MAX_PLAYER_NAME_LENGTH
                ),
                parent=self.root,
            )
            self.name_entry.focus_set()
            return
        self.cancel_pending_callbacks()
        self.player_name = player_name
        self.subject = self.subject_picker.get()
        subject_questions = SUBJECT_QUESTIONS[self.subject]
        mode = self.mode_picker.get()
        if mode in ("Easy", "Medium", "Hard"):
            filtered = tuple(
                question for question in subject_questions
                if question.difficulty == mode
            )
            self.questions = filtered or subject_questions
        elif mode == "Adaptive":
            easy = tuple(q for q in subject_questions if q.difficulty == "Easy")
            medium = tuple(q for q in subject_questions if q.difficulty == "Medium")
            hard = tuple(q for q in subject_questions if q.difficulty == "Hard")
            self.questions = tuple(easy + medium + hard)
        else:
            self.questions = tuple(subject_questions)
        if mode != "Adaptive":
            self.questions = tuple(random.sample(self.questions, len(self.questions)))
        self.question_index = 0
        self.score = 0
        self.attempted = 0
        self.score_saved = False
        self.streak = 0
        self.best_streak = 0
        self.lifeline_used = False
        self.answer_history = []
        self.response_times = []
        self.choices_frame.pack(fill="x", pady=(18, 8))
        self.skip_button.pack(side="left")
        self.lifeline_button.config(text="50:50 lifeline", state="normal")
        self.lifeline_button.pack(side="left", padx=(8, 0))
        self.next_button.pack(side="right")
        self.restart_button.pack_forget()
        self.subject_button.pack_forget()
        self.selection_frame.pack_forget()
        self.quiz_frame.pack(fill="both", expand=True)
        self.show_question()

    def show_question(self) -> None:
        self.cancel_pending_callbacks()
        question = self.questions[self.question_index]
        self.answered = False
        self.update_progress()
        self.prompt.config(text=question.prompt)
        self.feedback.config(text="Choose an answer to start.", fg="#53627a")
        self.choice_mapping = list(range(len(question.choices)))
        random.shuffle(self.choice_mapping)
        for index, button in enumerate(self.choice_buttons):
            if index < len(self.choice_mapping):
                original_index = self.choice_mapping[index]
                button.config(
                    text="{}   {}".format(
                        chr(ord("A") + index),
                        question.choices[original_index],
                    ),
                    state="normal",
                    bg="white",
                    fg="#243b6b",
                )
                button.pack(fill="x", pady=4)
            else:
                button.pack_forget()
        self.skip_button.config(state="normal")
        self.lifeline_button.config(
            state="disabled" if self.lifeline_used else "normal"
        )
        self.next_button.config(text="Next")
        self.next_button.config(state="disabled")
        self.review_frame.pack_forget()
        self.review_button.pack_forget()
        self.remaining_seconds = QUESTION_TIME_SECONDS
        self.update_timer_label()
        self.question_started_at = time.monotonic()
        self.timer_after_id = self.root.after(1000, self.update_timer)

    def update_progress(self) -> None:
        question = self.questions[self.question_index]
        self.progress.config(
            text="{}   |   {}   |   QUESTION {} OF {}   |   SCORE {}   |   STREAK {}".format(
                self.subject.upper(),
                question.difficulty.upper(),
                self.question_index + 1,
                len(self.questions),
                self.score,
                self.streak,
            )
        )

    def answer(self, selected: int, choice_is_display: bool = False) -> None:
        if self.answered:
            return
        self.answered = True
        self.cancel_timer()
        self.attempted += 1
        elapsed = max(0, round(time.monotonic() - self.question_started_at, 1))
        self.response_times.append(elapsed)
        question = self.questions[self.question_index]
        original_selected = (
            self.choice_mapping[selected]
            if choice_is_display and self.choice_mapping
            else selected
        )
        correct = original_selected == question.answer
        if correct:
            self.score += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            self.feedback.config(
                text=random.choice(CORRECT_MESSAGES),
                fg="#18794e",
            )
        else:
            self.streak = 0
            correct_choice = question.choices[question.answer]
            self.feedback.config(
                text="Not quite. The answer is {}. Moving on...".format(correct_choice),
                fg="#b42318",
            )
        self.answer_history.append(
            {
                "number": self.question_index + 1,
                "prompt": question.prompt,
                "selected": (
                    question.choices[original_selected]
                    if 0 <= original_selected < len(question.choices)
                    else "No answer"
                ),
                "correct": question.choices[question.answer],
                "status": "Correct" if correct else "Incorrect",
                "difficulty": question.difficulty,
                "explanation": question.explanation or "Review the correct answer above.",
            }
        )
        if question.explanation:
            self.feedback.config(
                text="{} {}".format(self.feedback.cget("text"), question.explanation),
                fg="#18794e" if correct else "#b42318",
            )
        self.update_progress()
        for button in self.choice_buttons:
            button.config(state="disabled")
        self.skip_button.config(state="disabled")
        self.lifeline_button.config(state="disabled")
        self.next_button.config(
            text="See results" if self.question_index + 1 == len(self.questions) else "Next",
            state="normal",
        )
        self.advance_after_id = self.root.after(
            FEEDBACK_DELAY_MS, self.advance_automatically
        )

    def skip(self) -> None:
        self.streak = 0
        elapsed = max(0, round(time.monotonic() - self.question_started_at, 1))
        self.response_times.append(elapsed)
        question = self.questions[self.question_index]
        self.answer_history.append(
            {
                "number": self.question_index + 1,
                "prompt": question.prompt,
                "selected": "Skipped",
                "correct": question.choices[question.answer],
                "status": "Skipped",
                "difficulty": question.difficulty,
                "explanation": question.explanation or "Review the correct answer above.",
            }
        )
        self.next_question()

    def use_lifeline(self) -> None:
        if self.answered or self.lifeline_used:
            return
        self.lifeline_used = True
        question = self.questions[self.question_index]
        wrong_choices = [
            index
            for index, original_index in enumerate(self.choice_mapping)
            if original_index != question.answer
            and self.choice_buttons[index].winfo_manager()
        ]
        choices_to_remove = random.sample(wrong_choices, max(0, len(wrong_choices) - 1))
        for index in choices_to_remove:
            self.choice_buttons[index].pack_forget()
        self.lifeline_button.config(text="50:50 used", state="disabled")
        self.feedback.config(
            text="Two incorrect answers are out. Pick one of the remaining choices!",
            fg="#3158a5",
        )

    def next_question(self) -> None:
        self.cancel_pending_callbacks()
        self.question_index += 1
        if self.question_index == len(self.questions):
            self.show_results()
        else:
            if self.mode_picker.get() == "Adaptive":
                target = (
                    "Hard" if self.streak >= 2
                    else "Medium" if self.streak >= 1
                    else "Easy"
                )
                remaining = list(range(self.question_index, len(self.questions)))
                for position in remaining:
                    if self.questions[position].difficulty == target:
                        self.questions[self.question_index], self.questions[position] = (
                            self.questions[position],
                            self.questions[self.question_index],
                        )
                        break
            self.show_question()

    def update_timer(self) -> None:
        self.timer_after_id = None
        if self.answered:
            return
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.timeout_question()
            return
        self.update_timer_label()
        self.timer_after_id = self.root.after(1000, self.update_timer)

    def update_timer_label(self) -> None:
        self.timer_label.config(text="Time: {}s".format(self.remaining_seconds))

    def timeout_question(self) -> None:
        self.answered = True
        self.streak = 0
        elapsed = QUESTION_TIME_SECONDS
        self.response_times.append(elapsed)
        question = self.questions[self.question_index]
        self.answer_history.append(
            {
                "number": self.question_index + 1,
                "prompt": question.prompt,
                "selected": "Timed out",
                "correct": question.choices[question.answer],
                "status": "Timed out",
                "difficulty": question.difficulty,
                "explanation": question.explanation or "Review the correct answer above.",
            }
        )
        self.update_progress()
        self.timer_label.config(text="Time's up")
        self.feedback.config(
            text="Time is up. This question is unanswered; moving on...",
            fg="#b54708",
        )
        for button in self.choice_buttons:
            button.config(state="disabled")
        self.skip_button.config(state="disabled")
        self.lifeline_button.config(state="disabled")
        self.next_button.config(state="normal")
        self.advance_after_id = self.root.after(
            FEEDBACK_DELAY_MS, self.advance_automatically
        )

    def advance_automatically(self) -> None:
        self.advance_after_id = None
        self.next_question()

    def cancel_timer(self) -> None:
        if self.timer_after_id is not None:
            self.root.after_cancel(self.timer_after_id)
            self.timer_after_id = None

    def cancel_pending_callbacks(self) -> None:
        self.cancel_timer()
        if self.advance_after_id is not None:
            self.root.after_cancel(self.advance_after_id)
            self.advance_after_id = None

    def show_results(self) -> None:
        self.progress.config(text="QUIZ COMPLETE")
        self.timer_label.config(text="")
        self.prompt.config(
            text="{}, you scored {} out of {}.".format(
                self.player_name, self.score, len(self.questions)
            )
        )
        self.choices_frame.pack_forget()
        self.review_frame.pack_forget()
        if self.score == len(self.questions):
            result_message = "Perfect score! QuizBot champion!"
        elif self.score >= 2:
            result_message = "Great job! Keep challenging yourself."
        else:
            result_message = "Good effort! Play again to beat your score."
        average_time = (
            sum(self.response_times) / len(self.response_times)
            if self.response_times
            else 0
        )
        self.feedback.config(
            text="{} question{} attempted. {} Average response: {:.1f}s. Best streak: {}.".format(
                self.attempted,
                "" if self.attempted == 1 else "s",
                result_message,
                average_time,
                self.best_streak,
            ),
            fg="#53627a",
        )
        if not self.score_saved:
            try:
                self.score_store.add_score(
                    self.player_name,
                    self.subject,
                    self.score,
                    len(self.questions),
                )
            except ScoreStoreError as error:
                messagebox.showerror(
                    "Score not saved",
                    str(error),
                    parent=self.root,
                )
            else:
                self.score_saved = True
                self.refresh_leaderboard()
        self.skip_button.pack_forget()
        self.lifeline_button.pack_forget()
        self.next_button.pack_forget()
        self.review_button.pack(side="left", padx=(8, 0))
        self.restart_button.pack(side="right")
        self.subject_button.pack(side="left")

    def toggle_answer_review(self) -> None:
        if self.review_frame.winfo_manager():
            self.review_frame.pack_forget()
            self.review_button.config(text="Review answers")
            return
        for item in self.review_table.get_children():
            self.review_table.delete(item)
        for item in self.answer_history:
            if item["status"] == "Correct":
                result_text = "Correct"
            elif item["status"] == "Incorrect":
                result_text = "Missed"
            else:
                result_text = item["status"]
            detail = "{}\nYour answer: {}\nCorrect: {}\n{}".format(
                item["prompt"],
                item["selected"],
                item["correct"],
                item["explanation"],
            )
            self.review_table.insert(
                "",
                "end",
                values=(
                    item["number"],
                    result_text,
                    item["difficulty"],
                    detail,
                ),
            )
        self.review_frame.pack(fill="both", expand=True, pady=(10, 0))
        self.review_button.config(text="Hide review")

    def restart(self) -> None:
        self.cancel_pending_callbacks()
        self.question_index = 0
        mode = self.mode_picker.get()
        if mode != "Adaptive":
            self.questions = tuple(random.sample(self.questions, len(self.questions)))
        self.score = 0
        self.attempted = 0
        self.score_saved = False
        self.streak = 0
        self.best_streak = 0
        self.lifeline_used = False
        self.answer_history = []
        self.response_times = []
        self.choices_frame.pack(fill="x", pady=(18, 8))
        self.skip_button.pack(side="left")
        self.lifeline_button.config(text="50:50 lifeline", state="normal")
        self.lifeline_button.pack(side="left", padx=(8, 0))
        self.next_button.pack(side="right")
        self.restart_button.pack_forget()
        self.subject_button.pack_forget()
        self.review_frame.pack_forget()
        self.review_button.pack_forget()
        self.show_question()

    def choose_subject(self) -> None:
        self.cancel_pending_callbacks()
        self.name_entry.delete(0, tk.END)
        self.quiz_frame.pack_forget()
        self.selection_frame.pack(fill="both", expand=True)

    def refresh_leaderboard(self) -> None:
        for item in self.leaderboard_table.get_children():
            self.leaderboard_table.delete(item)
        try:
            records = self.score_store.load_scores()
        except ScoreStoreError as error:
            self.leaderboard_status.config(
                text="Leaderboard unavailable: {}".format(error),
                fg="#b42318",
            )
            self.set_score_action_state(False)
            return
        if not records:
            self.leaderboard_status.config(
                text="No scores yet. Be the first to make the leaderboard!",
                fg="#53627a",
            )
            self.set_score_action_state(False)
            return
        ranked_records = sorted(
            enumerate(records),
            key=lambda item: (
                item[1].score / item[1].total,
                item[1].score,
                item[1].completed_at,
            ),
            reverse=True,
        )
        for rank, (record_index, record) in enumerate(ranked_records, start=1):
            self.leaderboard_table.insert(
                "",
                "end",
                iid=str(record_index),
                values=(
                    rank,
                    record.name,
                    record.subject,
                    "{}/{}".format(record.score, record.total),
                    record.completed_at[:10],
                ),
            )
        self.leaderboard_status.config(
            text="Scores are saved on this computer. Showing highest scores first.",
            fg="#53627a",
        )
        self.set_score_action_state(True)

    def set_score_action_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.delete_score_button.config(state=state)
        self.delete_player_button.config(state=state)
        self.clear_scores_button.config(state=state)

    def delete_selected_score(self) -> None:
        selection = self.leaderboard_table.selection()
        if not selection:
            messagebox.showinfo(
                "Select a score",
                "Choose a score from the list first.",
                parent=self.root,
            )
            return
        selected_iid = selection[0]
        values = self.leaderboard_table.item(selected_iid, "values")
        try:
            record_index = int(selected_iid)
        except (TypeError, ValueError):
            messagebox.showerror(
                "Could not delete score",
                "The selected score is no longer valid. Refresh the leaderboard and try again.",
                parent=self.root,
            )
            self.refresh_leaderboard()
            return
        if not messagebox.askyesno(
            "Delete score",
            "Delete {}'s {} score of {}?".format(values[1], values[2], values[3]),
            parent=self.root,
        ):
            return
        try:
            self.score_store.delete_score(record_index)
        except (ScoreStoreError, ValueError) as error:
            messagebox.showerror("Could not delete score", str(error), parent=self.root)
            self.refresh_leaderboard()
            return
        self.refresh_leaderboard()
        self.leaderboard_status.config(text="Score deleted.", fg="#18794e")

    def delete_selected_player(self) -> None:
        selection = self.leaderboard_table.selection()
        if not selection:
            messagebox.showinfo(
                "Select a player",
                "Choose one of the player's scores from the list first.",
                parent=self.root,
            )
            return
        values = self.leaderboard_table.item(selection[0], "values")
        player_name = str(values[1])
        if not messagebox.askyesno(
            "Delete player",
            "Delete all saved scores for {}?".format(player_name),
            parent=self.root,
        ):
            return
        try:
            deleted_count = self.score_store.delete_player(player_name)
        except (ScoreStoreError, ValueError) as error:
            messagebox.showerror("Could not delete player", str(error), parent=self.root)
            self.refresh_leaderboard()
            return
        self.refresh_leaderboard()
        self.leaderboard_status.config(
            text="Deleted {} score{} for {}.".format(
                deleted_count,
                "" if deleted_count == 1 else "s",
                player_name,
            ),
            fg="#18794e",
        )

    def clear_all_scores(self) -> None:
        if not messagebox.askyesno(
            "Clear leaderboard",
            "Delete every saved score and player? This cannot be undone.",
            parent=self.root,
        ):
            return
        try:
            deleted_count = self.score_store.clear_scores()
        except ScoreStoreError as error:
            messagebox.showerror("Could not clear scores", str(error), parent=self.root)
            self.refresh_leaderboard()
            return
        self.refresh_leaderboard()
        self.leaderboard_status.config(
            text="Cleared {} saved score{}.".format(
                deleted_count,
                "" if deleted_count == 1 else "s",
            ),
            fg="#18794e",
        )


def main() -> None:
    root = tk.Tk()
    QuizApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
