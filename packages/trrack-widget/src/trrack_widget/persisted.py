"""The Persisted widget: saves a widget's state and restores it on reload."""

from __future__ import annotations

import copy
import pathlib
from typing import Any

from trrack.persist import Store, from_state, read_envelope
from trrack_widget._base import TargetWidget
from trrack_widget._persist import CoalescedWriter
from trrack_widget._tracked import TrackedValues

_STATIC = pathlib.Path(__file__).parent / "static"


class Persisted(TargetWidget):
    """Save a widget's state and restore it the next time it loads.

    Wraps ``target`` and writes its tracked traits to a store whenever they
    change. Create it again with the same store and the widget picks up where
    it left off. Displaying a ``Persisted`` shows the target. If a save fails,
    the error appears under it.

    The store decides where the state lives. Use ``JsonFileStore`` for a file,
    or pass any object with ``save(dict)`` and ``load()``.

    Examples:
        ```python
        from trrack_widget import JsonFileStore, Persisted

        persisted = Persisted(counter, store=JsonFileStore("state.json"))
        persisted  # displays the counter
        ```
    """

    _esm = _STATIC / "persisted.js"
    _kind = "persisted"

    def __init__(
        self,
        target: Any,
        traits: list[str] | None = None,
        *,
        store: Store,
        **kwargs: Any,
    ) -> None:
        """Wrap ``target`` and keep its tracked traits in a store.

        Args:
            target (Any): The widget to save. It must be an anywidget.
            traits (list[str], optional): Trait names to save. Defaults to the
                target's public synced traits.
            store (Store): Where to save.
            **kwargs (Any): Forwarded to ``anywidget.AnyWidget``.

        Raises:
            ValueError: If the store holds a ``Trrackable`` graph, or a payload
                that is not in a known format.
        """
        saved = store.load()
        kind, value = read_envelope(saved) if saved is not None else ("state", {})
        if kind == "graph":
            # Saving here would overwrite the graph.
            msg = (
                "This store holds a Trrackable graph, and Persisted would "
                "overwrite it. Use Trrackable, or pass a different store."
            )
            raise ValueError(msg)

        super().__init__(target, **kwargs)
        self._values = TrackedValues(target, traits)
        self._writer = CoalescedWriter(
            store, lambda: from_state(self.state), self._on_save_result
        )
        # Copied so a later in-place change to a list or dict value cannot
        # alter what reset() goes back to.
        self._initial = copy.deepcopy(self.state)
        self._follow_target()

        # Restoring must not write back what was just loaded.
        self._set_values(value)

        # A store that fails here must not stop the widget from loading.
        if saved is None:
            self._writer.flush_quietly()

    def _on_target_change(self, _change: dict) -> None:
        if not self._internal and self._writer is not None:
            self._writer.schedule()

    def reset(self) -> None:
        """Put the widget back to the values it started with, and save them.

        The starting values are the ones the widget had before any saved
        state was loaded. If the save fails, the error appears under the
        widget.
        """
        self._set_values(copy.deepcopy(self._initial))
        if self._writer is not None:
            self._writer.flush_quietly()
