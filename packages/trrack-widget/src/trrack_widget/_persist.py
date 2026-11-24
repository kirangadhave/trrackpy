"""Debounced callbacks and store writes for the widgets."""

from __future__ import annotations

import asyncio
import atexit
import contextlib
import sys
import threading
import weakref
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from trrack.persist import Store

# A burst of mutations within this window collapses into a single store write.
_PERSIST_DEBOUNCE_MS = 150


def _threads_available() -> bool:
    # Pyodide cannot start a thread, so a timer thread is not an option there.
    return sys.platform != "emscripten"


class Debouncer:
    """Run a callback once, after calls to ``schedule`` stop for a while.

    Args:
        delay_ms (float): How long to wait after the last ``schedule`` call.
        callback (Callable[[], None]): What to run.
    """

    def __init__(self, delay_ms: float, callback: Callable[[], None]) -> None:
        self._delay_s = delay_ms / 1000
        self._callback = callback
        self._timer: threading.Timer | None = None
        self._handle: asyncio.Handle | None = None
        self._lock = threading.Lock()
        # Counts the waits. A timer can fire in the moment that a cancel or a
        # new wait replaces it, and the count tells that timer it is stale.
        self._wait = 0

    def schedule(self) -> None:
        """Start the wait, or restart it if one is in progress.

        Without thread support, the wait runs on the running event loop. If no
        loop is running, nothing can run the callback later, so it runs now.
        """
        if not _threads_available():
            self._schedule_on_loop()
            return
        # The timer fires on a worker thread, which has none of marimo's
        # thread-local runtime context. The callback runs on the event loop of
        # the thread that called schedule().
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._wait += 1
            timer = threading.Timer(self._delay_s, self._fire, (self._wait, loop))
            timer.daemon = True
            self._timer = timer
            timer.start()

    def cancel(self) -> bool:
        """Drop a pending call.

        Returns:
            bool: Whether a call was pending.
        """
        with self._lock:
            timer = self._timer
            handle = self._handle
            self._timer = None
            self._handle = None
            self._wait += 1
        if handle is not None:
            handle.cancel()
        if timer is not None:
            timer.cancel()
        return timer is not None or handle is not None

    def _schedule_on_loop(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            self.cancel()
            self._callback()
            return
        with self._lock:
            if self._handle is not None:
                self._handle.cancel()
            self._handle = loop.call_later(self._delay_s, self._fire_on_loop)

    def _fire_on_loop(self) -> None:
        with self._lock:
            self._handle = None
        self._callback()

    def _fire(self, wait: int, loop: asyncio.AbstractEventLoop | None) -> None:
        with self._lock:
            if wait != self._wait:
                return
            self._timer = None
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(self._callback)
        else:
            self._callback()


class CoalescedWriter:
    """Save to a store, writing once per burst of changes.

    Args:
        store (Store): Where to save.
        payload (Callable[[], dict]): Builds the data to save. It is called at
            write time, so each write holds the latest state.
        on_result (Callable[[Exception | None], None], optional): Called after
            each write with the error, or ``None`` if the write worked.
        drain (Callable[[], bool], optional): Puts work that is not in the
            payload yet into it, and returns whether there was any. It runs
            before a write that the owner asks for, and at interpreter exit.
    """

    def __init__(
        self,
        store: Store,
        payload: Callable[[], dict],
        on_result: Callable[[Exception | None], None] | None = None,
        *,
        drain: Callable[[], bool] | None = None,
    ) -> None:
        self._store = store
        self._payload = payload
        self._on_result = on_result
        self._drain = drain
        self._debouncer = Debouncer(_PERSIST_DEBOUNCE_MS, self.flush_quietly)
        # A timer write and a direct write can run on different threads. A
        # store must never see two saves at one time.
        self._write_lock = threading.Lock()
        _writers.add(self)

    def schedule(self) -> None:
        """Write soon. Calls close together share one write."""
        self._debouncer.schedule()

    def flush(self) -> None:
        """Write now, in place of any pending write. Raises if the save fails."""
        if self._drain is not None:
            self._drain()
        self._debouncer.cancel()
        self._write()

    def flush_quietly(self) -> None:
        """Write now, and report a failure through ``on_result`` only."""
        self._debouncer.cancel()
        with contextlib.suppress(Exception):
            self._write()

    def flush_if_pending(self) -> None:
        """Write now if a write is waiting. Reports a failure, never raises."""
        drained = self._drain is not None and self._drain()
        if self._debouncer.cancel() or drained:
            self.flush_quietly()

    def _write(self) -> None:
        with self._write_lock:
            try:
                self._store.save(self._payload())
            except Exception as error:
                self._report(error)
                raise
            self._report(None)

    def _report(self, error: Exception | None) -> None:
        if self._on_result is not None:
            self._on_result(error)


_writers: weakref.WeakSet[CoalescedWriter] = weakref.WeakSet()


def _flush_all_at_exit() -> None:
    for writer in list(_writers):
        # One writer that fails must not stop the others from saving.
        with contextlib.suppress(Exception):
            writer.flush_if_pending()


# The timer thread is a daemon, so the interpreter does not wait for it.
# Without this hook, a change made just before exit is never saved. One hook
# serves every writer, so a notebook that makes many writers adds no more.
atexit.register(_flush_all_at_exit)
