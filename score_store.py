"""Local persistent storage for QuizBot scores."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class ScoreStoreError(Exception):
    pass


@dataclass(frozen=True)
class ScoreRecord:
    name: str
    subject: str
    score: int
    total: int
    completed_at: str


class ScoreStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            data_directory = Path(
                os.environ.get("LOCALAPPDATA") or str(Path.home())
            ) / "QuizBot"
            path = data_directory / "scores.json"
        self.path = Path(path)

    def load_scores(self) -> Tuple[ScoreRecord, ...]:
        try:
            contents = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ()
        except (OSError, UnicodeError) as error:
            raise ScoreStoreError(
                "Could not read the saved leaderboard: {}".format(error)
            ) from error

        try:
            data = json.loads(contents)
        except json.JSONDecodeError as error:
            raise ScoreStoreError(
                "The saved leaderboard file is not valid JSON: {}".format(error)
            ) from error

        if not isinstance(data, list):
            raise ScoreStoreError("The saved leaderboard must contain a list of scores.")

        records = []
        for item in data:
            if not isinstance(item, dict):
                raise ScoreStoreError("The saved leaderboard contains an invalid score.")
            name = item.get("name")
            subject = item.get("subject")
            score = item.get("score")
            total = item.get("total")
            completed_at = item.get("completed_at")
            if (
                not isinstance(name, str)
                or not name.strip()
                or not isinstance(subject, str)
                or not subject.strip()
                or type(score) is not int
                or type(total) is not int
                or total < 1
                or not 0 <= score <= total
                or not isinstance(completed_at, str)
            ):
                raise ScoreStoreError("The saved leaderboard contains an invalid score.")
            records.append(ScoreRecord(name, subject, score, total, completed_at))
        return tuple(records)

    def add_score(
        self, name: str, subject: str, score: int, total: int
    ) -> ScoreRecord:
        if not name.strip() or not subject.strip():
            raise ValueError("A player name and subject are required.")
        if total < 1 or not 0 <= score <= total:
            raise ValueError("Score must be between zero and the total questions.")

        records = list(self.load_scores())
        record = ScoreRecord(
            name=name.strip(),
            subject=subject.strip(),
            score=score,
            total=total,
            completed_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        )
        records.append(record)
        self._write_scores(records)
        return record

    def delete_score(self, index: int) -> ScoreRecord:
        records = list(self.load_scores())
        if type(index) is not int or not 0 <= index < len(records):
            raise ValueError("Select a score that exists in the leaderboard.")
        deleted = records.pop(index)
        self._write_scores(records)
        return deleted

    def delete_player(self, name: str) -> int:
        normalized_name = name.strip().casefold()
        if not normalized_name:
            raise ValueError("Player name cannot be empty.")
        records = list(self.load_scores())
        remaining = [
            record for record in records if record.name.casefold() != normalized_name
        ]
        deleted_count = len(records) - len(remaining)
        if deleted_count:
            self._write_scores(remaining)
        return deleted_count

    def clear_scores(self) -> int:
        records = list(self.load_scores())
        if records:
            self._write_scores([])
        return len(records)

    def _write_scores(self, records: List[ScoreRecord]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps([asdict(item) for item in records], indent=2) + "\n",
                encoding="utf-8",
            )
        except (OSError, UnicodeError) as error:
            raise ScoreStoreError(
                "Could not save the score to {}: {}".format(self.path, error)
            ) from error

    def leaderboard(self, limit: int = 5) -> Tuple[ScoreRecord, ...]:
        if limit < 1:
            raise ValueError("Leaderboard limit must be positive.")
        records: List[ScoreRecord] = list(self.load_scores())
        records.sort(
            key=lambda item: (
                item.score / item.total,
                item.score,
                item.completed_at,
            ),
            reverse=True,
        )
        return tuple(records[:limit])
