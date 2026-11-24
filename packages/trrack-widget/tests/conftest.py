from __future__ import annotations

import pytest

import trrack_widget._persist as persist


@pytest.fixture(autouse=True)
def short_save_window(monkeypatch):
    """Batch saves over 20 ms, so no test waits for the real window."""
    monkeypatch.setattr(persist, "_PERSIST_DEBOUNCE_MS", 20)
