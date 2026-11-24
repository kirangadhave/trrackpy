from __future__ import annotations

import asyncio
import threading

import pytest

import trrack_widget._persist as persist
from trrack_widget._persist import Debouncer

_DELAY_MS = 10
_PAST_DELAY_S = 0.05


class ThreadsUnavailableError(RuntimeError):
    """Stands in for a timer thread that the platform cannot start."""


@pytest.fixture(autouse=True)
def no_threads(monkeypatch):
    monkeypatch.setattr(persist, "_threads_available", lambda: False)

    def refuse(*_args, **_kwargs):
        raise ThreadsUnavailableError

    monkeypatch.setattr(threading, "Timer", refuse)


def test_burst_in_running_loop_runs_callback_once_after_delay():
    calls: list[int] = []
    debouncer = Debouncer(_DELAY_MS, lambda: calls.append(1))

    async def scenario() -> None:
        for _ in range(5):
            debouncer.schedule()
        assert calls == []
        await asyncio.sleep(_PAST_DELAY_S)

    asyncio.run(scenario())
    assert calls == [1]


def test_cancel_before_delay_stops_callback():
    calls: list[int] = []
    debouncer = Debouncer(_DELAY_MS, lambda: calls.append(1))

    async def scenario() -> bool:
        debouncer.schedule()
        cancelled = debouncer.cancel()
        await asyncio.sleep(_PAST_DELAY_S)
        return cancelled

    assert asyncio.run(scenario()) is True
    assert calls == []


def test_cancel_with_nothing_pending_returns_false():
    debouncer = Debouncer(_DELAY_MS, lambda: None)
    assert debouncer.cancel() is False


def test_cancel_after_callback_ran_returns_false():
    debouncer = Debouncer(_DELAY_MS, lambda: None)

    async def scenario() -> bool:
        debouncer.schedule()
        await asyncio.sleep(_PAST_DELAY_S)
        return debouncer.cancel()

    assert asyncio.run(scenario()) is False


def test_schedule_without_running_loop_runs_callback_at_once():
    calls: list[int] = []
    debouncer = Debouncer(_DELAY_MS, lambda: calls.append(1))
    debouncer.schedule()
    assert calls == [1]
    assert debouncer.cancel() is False


def test_schedule_without_loop_drops_earlier_pending_call():
    calls: list[int] = []
    debouncer = Debouncer(_DELAY_MS, lambda: calls.append(1))

    async def scenario() -> None:
        debouncer.schedule()
        await asyncio.to_thread(debouncer.schedule)
        await asyncio.sleep(_PAST_DELAY_S)

    asyncio.run(scenario())
    assert calls == [1]
