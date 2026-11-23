"""Shared persistence helpers: trait inference and coalesced store writes."""

from __future__ import annotations

import asyncio
import threading
from typing import TYPE_CHECKING, Any

import anywidget

if TYPE_CHECKING:
    from collections.abc import Callable

    from trrack.persist import Store

# A burst of mutations within this window collapses into a single store write.
_PERSIST_DEBOUNCE_MS = 150


def infer_traits(target: Any) -> list[str]:
    """Return the trait names of ``target`` that hold its user-facing state.

    Args:
        target (Any): The widget to inspect.

    Returns:
        The synced traits of ``target``, without the traits that each anywidget
        has and without private traits.
    """
    base = set(anywidget.AnyWidget.class_traits(sync=True))
    return [
        name
        for name in target.traits(sync=True)
        if name not in base and not name.startswith("_")
    ]


class CoalescedWriter:
    """Write a payload to a store, with one write for each burst of changes.

    Args:
        store (Store): The persistence backend that receives each write.
        payload (Callable[[], dict]): Builds the data to save. The writer calls
            it at write time, so each write holds the latest state.
    """

    def __init__(self, store: Store, payload: Callable[[], dict]) -> None:
        self._store = store
        self._payload = payload
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()
        # The timer fires on a worker thread that lacks the thread-local
        # runtime context of marimo. The write must go back to the loop of the
        # thread that scheduled it.
        self._loop: asyncio.AbstractEventLoop | None = None

    def schedule(self) -> None:
        """Start the coalesce window, or restart it if a write is pending."""
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            timer = threading.Timer(_PERSIST_DEBOUNCE_MS / 1000, self._on_timer)
            timer.daemon = True
            self._timer = timer
            timer.start()

    def flush(self) -> None:
        """Cancel a pending write and write the payload immediately."""
        with self._lock:
            timer = self._timer
            self._timer = None
        if timer is not None:
            timer.cancel()
        self._write()

    def _on_timer(self) -> None:
        with self._lock:
            self._timer = None
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(self._write)
        else:
            self._write()

    def _write(self) -> None:
        self._store.save(self._payload())
