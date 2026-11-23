"""The Trrackable widget: records a widget's state as a history you can navigate."""

from __future__ import annotations

import datetime as dt
import pathlib
from typing import TYPE_CHECKING, Any

import traitlets

from trrack import Node, ProvenanceGraph
from trrack.persist import Store, graph_envelope, read_envelope
from trrack_widget._base import TargetWidget, infer_traits
from trrack_widget._persist import CoalescedWriter, Debouncer

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

    Examples:
        ```python
        from trrack_widget import Trrackable

        tracked = Trrackable(counter)
        tracked  # displays the counter and its history
        tracked.undo()
        ```
    """

    nodes = traitlets.Dict().tag(sync=True)
    current_id = traitlets.Unicode().tag(sync=True)
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
        **kwargs: Any,
    ) -> None:
        """Wrap ``target`` and record its tracked traits.

        Args:
            target (Any): The widget to track. It must be an anywidget.
            traits (list[str], optional): Trait names to record. Defaults to
                the target's public synced traits.
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
            **kwargs (Any): Forwarded to ``anywidget.AnyWidget``.
        """
        super().__init__(target, **kwargs)
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
            self._tracked = list(value["tracked"])
            self._tree = ProvenanceGraph.from_dict(value["tree"])
        else:
            # A state payload holds values only, so the tracked traits come
            # from the caller or from the target.
            self._tracked = list(traits) if traits is not None else infer_traits(target)
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

    def _apply(self, node: Node) -> None:
        self._sync_tree()
        self._set_values(node.state)
        self._schedule_persist()

    def _on_current_id_change(self, change: dict) -> None:
        if self._internal:
            return
        self._cancel_pending_commit()
        self._apply(self._tree.go_to(change["new"]))

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
        self._cancel_pending_commit()
        node = self._tree.undo()
        if node is not None:
            self._apply(node)

    def redo(self) -> None:
        """Go forward to the newest next step, and set the target to it."""
        self._cancel_pending_commit()
        node = self._tree.redo()
        if node is not None:
            self._apply(node)

    def go_to(self, node_id: str) -> None:
        """Jump to a node, and set the target to its state.

        Args:
            node_id (str): The id of the node to go to.
        """
        self._cancel_pending_commit()
        self._apply(self._tree.go_to(node_id))

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
            {"tracked": list(self._tracked), "tree": self._tree.to_dict()}
        )

    @classmethod
    def from_dict(
        cls,
        data: dict,
        target: Any,
        *,
        debounce_ms: int = 0,
        label_formatter: Callable[[dict, dict], str] | None = None,
    ) -> Trrackable:
        """Rebuild a ``Trrackable`` from ``to_dict()`` output.

        Args:
            data (dict): The saved payload.
            target (Any): The widget to track. It is set to the saved state.
            debounce_ms (int, optional): See ``Trrackable``.
            label_formatter (Callable[[dict, dict], str], optional): See
                ``Trrackable``.

        Returns:
            Trrackable: A widget that tracks ``target`` with the saved history.
        """
        return cls(
            target,
            debounce_ms=debounce_ms,
            label_formatter=label_formatter,
            restore=data,
        )
