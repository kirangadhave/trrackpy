"""Stores for tests."""

from __future__ import annotations


class RecordingStore:
    """An in-memory store that keeps each payload it receives."""

    def __init__(self, data: dict | None = None) -> None:
        self.data = data
        self.saves: list[dict] = []

    def save(self, data: dict) -> None:
        self.data = data
        self.saves.append(data)

    def load(self) -> dict | None:
        return self.data


class FlakyStore(RecordingStore):
    """A store whose saves fail while ``broken`` is set."""

    broken = False

    def save(self, data: dict) -> None:
        if self.broken:
            msg = "disk is full"
            raise OSError(msg)
        super().save(data)
