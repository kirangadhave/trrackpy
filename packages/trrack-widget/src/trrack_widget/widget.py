"""The Trrackable widget: records a widget's state as a history you can navigate."""

from __future__ import annotations

import datetime as dt
import pathlib
from typing import TYPE_CHECKING, Any

import traitlets

from trrack import Node, ProvenanceGraph
from trrack.persist import Store, graph_envelope, read_envelope
from trrack_widget._base import TargetWidget
from trrack_widget._persist import CoalescedWriter, Debouncer
from trrack_widget._tracked import TrackedValues

if TYPE_CHECKING:
    from collections.abc import Callable

_STATIC = pathlib.Path(__file__).parent / "static"


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class Trrackable(TargetWidget):
    """Record a widget's state as a branching history with undo and redo.

    Wraps ``target`` and adds a node to the history each time a tracked trait
    changes. Displaying a ``Trrackable`` shows the target with the history
    controls next to it. If a save fails, the error appears under them.

    The controls are a row of buttons and the history graph. Set ``buttons``
    and ``graph`` to show or hide them.

    Examples:
        ```python
        from trrack_widget import Trrackable

        tracked = Trrackable(counter)
        tracked  # displays the counter and its history
        tracked.undo()
        ```

        ```python
        tracked = Trrackable(counter, graph=False)  # buttons only
        tracked.graph = True  # show the graph
        ```
    """

    nodes = traitlets.Dict().tag(sync=True)
    current_id = traitlets.Unicode().tag(sync=True)
    buttons = traitlets.Bool(default_value=True).tag(sync=True)
    graph = traitlets.Bool(default_value=True).tag(sync=True)
    _relabel = traitlets.Dict(allow_none=True).tag(sync=True)

    _esm = _STATIC / "controls.js"

    def __init__(  # noqa: PLR0913 — rich public constructor: target + optional config
        self,
        target: Any,
        traits: list[str] | None = None,
        *,
        debounce_ms: int = 0,
        store: Store | None = None,
        restore: dict | None = None,
        label_formatter: Callable[[dict, dict], str] | None = None,
        buttons: bool = True,
        graph: bool = True,
        **kwargs: Any,
    ) -> None:
        """Wrap ``target`` and record its tracked traits.

        Args:
            target (Any): The widget to track. It must be an anywidget.
            traits (list[str], optional): Trait names to record. Defaults to
                the target's public synced traits. A loaded history keeps the
                trait names it was saved with.
            debounce_ms (int, optional): Record a burst of changes within this
                many milliseconds as one node. ``0`` records every change.
                Useful for sliders.
            store (Store, optional): Where to save, such as
                ``JsonFileStore("state.json")``. When the store already holds
                a history, that history is loaded. State saved by
                ``Persisted`` loads as the first node of a new history.
            restore (dict, optional): A ``to_dict()`` payload to load, in
                place of the store.
            label_formatter (Callable[[dict, dict], str], optional): Builds a
                node's label from the old and new tracked values. Defaults to
                a list of what changed, such as ``count: 1 → 2``.
            buttons (bool, optional): Show the row of buttons. Defaults to
                ``True``.
            graph (bool, optional): Show the history graph. Defaults to
                ``True``. The History button in the row also shows and hides
                it.
            **kwargs (Any): Forwarded to ``anywidget.AnyWidget``.

        Raises:
            ValueError: If the store or ``restore`` holds a payload that is not
                in a known format.
        """
        super().__init__(target, buttons=buttons, graph=graph, **kwargs)
        self._label_formatter = label_formatter
        self._commit_debouncer = (
            Debouncer(debounce_ms, self._commit) if debounce_ms > 0 else None
        )
        self._writer = (
            CoalescedWriter(store, self.to_dict, self._on_save_result)
            if store is not None
            else None
        )

        saved = restore
        if saved is None and store is not None:
            saved = store.load()
        kind, value = read_envelope(saved) if saved is not None else (None, {})
        if kind == "graph":
            self._values = TrackedValues(target, value["tracked"])
            self._tree = ProvenanceGraph.from_dict(value["tree"])
        else:
            # A state payload holds values only, so the tracked traits come
            # from the caller or from the target.
            self._values = TrackedValues(target, traits)
            self._set_values(value)
            self._tree = ProvenanceGraph(self.state, now=_now())

        self._sync_tree()
        self._set_values(self._tree.current.state)
        self._follow_target()
        self.observe(self._on_current_id_change, names="current_id")
        self.observe(self._on_relabel, names="_relabel")

        # Write on construction only when the store is empty. Loading leaves
        # the store as it was, so opening a saved file never rewrites it. A
        # store that fails here must not stop the widget from loading.
        if self._writer is not None and saved is None:
            self._writer.flush_quietly()

    def _sync_tree(self) -> None:
        snapshot = self._tree.to_dict()
        self.nodes = snapshot["nodes"]
        with self._guard():
            self.current_id = snapshot["current_id"]

    def _commit(self) -> None:
        new_state = self.state
        label = (
            self._label_formatter(self._tree.current.state, new_state)
            if self._label_formatter is not None
            else None
        )
        self._tree.commit(new_state, now=_now(), label=label)
        self._sync_tree()
        self._schedule_persist()

    def _on_target_change(self, _change: dict) -> None:
        if self._internal:
            return
        if self._commit_debouncer is not None:
            self._commit_debouncer.schedule()
        else:
            self._commit()

    def _cancel_pending_commit(self) -> bool:
        return self._commit_debouncer is not None and self._commit_debouncer.cancel()

    def flush(self) -> None:
        """Record a pending debounced change now, if there is one."""
        if self._cancel_pending_commit():
            self._commit()

    def _schedule_persist(self) -> None:
        if self._writer is not None:
            self._writer.schedule()

    def _unfollow_target(self) -> None:
        self.flush()
        super()._unfollow_target()

    def _navigate(self, move: Callable[[], Node | None]) -> None:
        # A change that waits for the debounce belongs to the node that the
        # history leaves, so it must not land on the node it goes to.
        self._cancel_pending_commit()
        node = move()
        if node is None:
            return
        self._sync_tree()
        self._set_values(node.state)
        self._schedule_persist()

    def _on_current_id_change(self, change: dict) -> None:
        if not self._internal:
            self.go_to(change["new"])

    def _on_relabel(self, change: dict) -> None:
        request = change["new"]
        if not request:
            return
        node_id = request.get("id")
        text = request.get("text")
        if node_id is None or text is None:
            return
        self.label(text, node_id)

    def undo(self) -> None:
        """Go back one step, and set the target to that state."""
        self._navigate(self._tree.undo)

    def redo(self) -> None:
        """Go forward to the newest next step, and set the target to it."""
        self._navigate(self._tree.redo)

    def go_to(self, node_id: str) -> None:
        """Jump to a node, and set the target to its state.

        Args:
            node_id (str): The id of the node to go to.
        """
        self._navigate(lambda: self._tree.go_to(node_id))

    def label(self, text: str, node_id: str | None = None) -> None:
        """Rename a node.

        Args:
            text (str): The new label.
            node_id (str, optional): The node to rename. Defaults to the
                current node.
        """
        self._tree.relabel(text, node_id)
        self._sync_tree()
        self._schedule_persist()

    def to_dict(self) -> dict:
        """Serialize the tracked trait names and the whole history."""
        return graph_envelope(
            {"tracked": list(self._values.names), "tree": self._tree.to_dict()}
        )

    @classmethod
    def from_dict(  # noqa: PLR0913 — the same optional config as the constructor
        cls,
        data: dict,
        target: Any,
        *,
        debounce_ms: int = 0,
        label_formatter: Callable[[dict, dict], str] | None = None,
        buttons: bool = True,
        graph: bool = True,
    ) -> Trrackable:
        """Rebuild a ``Trrackable`` from ``to_dict()`` output.

        Args:
            data (dict): The saved payload.
            target (Any): The widget to track. It is set to the saved state.
            debounce_ms (int, optional): See ``Trrackable``.
            label_formatter (Callable[[dict, dict], str], optional): See
                ``Trrackable``.
            buttons (bool, optional): See ``Trrackable``.
            graph (bool, optional): See ``Trrackable``.

        Returns:
            Trrackable: A widget that tracks ``target`` with the saved history.
        """
        return cls(
            target,
            debounce_ms=debounce_ms,
            label_formatter=label_formatter,
            restore=data,
            buttons=buttons,
            graph=graph,
        )
