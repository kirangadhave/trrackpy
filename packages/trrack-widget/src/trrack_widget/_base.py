"""What Persisted and Trrackable share: a target widget and its tracked values."""

from __future__ import annotations

import contextlib
import weakref
from typing import TYPE_CHECKING, Any

import anywidget
import traitlets

from trrack_widget._tracked import TrackedValues

if TYPE_CHECKING:
    from collections.abc import Generator

    from trrack_widget._persist import CoalescedWriter

# The wrapper of each class that currently follows a widget. Two wrappers of
# one class on one widget would both react to every change, which happens when
# a notebook cell that creates the wrapper runs again.
_active: weakref.WeakKeyDictionary[Any, dict[str, weakref.ref[TargetWidget]]] = (
    weakref.WeakKeyDictionary()
)


class TargetWidget(anywidget.AnyWidget):
    """A widget that shows another widget and follows some of its traits."""

    target = anywidget.WidgetTrait().tag(sync=True)
    error = traitlets.Unicode("").tag(sync=True)

    def __init__(self, target: Any, **kwargs: Any) -> None:
        super().__init__(target=target, **kwargs)
        self._values = TrackedValues(target, [])
        self._writer: CoalescedWriter | None = None
        # Set while this object changes the target or itself, so its own
        # observers can tell those changes from the user's.
        self._internal = False

    @contextlib.contextmanager
    def _guard(self) -> Generator[None]:
        self._internal = True
        try:
            yield
        finally:
            self._internal = False

    @property
    def state(self) -> dict:
        """The current values of the tracked traits, keyed by trait name."""
        return self._values.read()

    def _set_values(self, values: dict) -> None:
        with self._guard():
            rejected = self._values.write(values)
        if rejected:
            self.error = "Ignored a saved value. " + " ".join(rejected)

    def _on_save_result(self, error: Exception | None) -> None:
        self.error = "" if error is None else f"Could not save: {error}"

    def _on_target_change(self, _change: dict) -> None:
        raise NotImplementedError

    def _follow_target(self) -> None:
        """Start to observe the target, in place of an earlier wrapper."""
        wrappers = _active.setdefault(self.target, {})
        # anywidget gives each instance its own subclass, so the class object
        # cannot be the key.
        kind = type(self).__name__
        previous = wrappers.get(kind, lambda: None)()
        if previous is not None:
            previous._unfollow_target()  # noqa: SLF001
        wrappers[kind] = weakref.ref(self)
        self._values.observe(self._on_target_change)

    def _unfollow_target(self) -> None:
        # A wrapper that failed in its constructor has no target.
        if self.target is None:
            return
        self._values.unobserve(self._on_target_change)
        if self._writer is not None:
            self._writer.flush_if_pending()

    def save(self) -> None:
        """Write to the store now.

        Raises the store's error if the save fails.
        """
        if self._writer is not None:
            self._writer.flush()

    def close(self) -> None:
        """Stop following the target, save any pending change, and close."""
        self._unfollow_target()
        super().close()
