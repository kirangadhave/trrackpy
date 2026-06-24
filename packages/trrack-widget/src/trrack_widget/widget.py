"""The Trrackable anywidget: records a target widget's state into a graph."""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import pathlib
import threading
from typing import TYPE_CHECKING, Any

import anywidget
import traitlets

from trrack import Node, ProvenanceGraph
from trrack.persist import JsonFileStore, Store

if TYPE_CHECKING:
    import os
    from collections.abc import Callable, Iterator

_STATIC = pathlib.Path(__file__).parent / "static"

# A burst of mutations within this window collapses into a single store write.
_PERSIST_DEBOUNCE_MS = 150


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _in_marimo() -> bool:
    """Whether code is running inside a live marimo kernel.

    marimo being importable is not enough — it may be installed alongside a
    Jupyter kernel. Display routing differs by host, so the check must be the
    runtime, not the import.
    """
    try:
        import marimo as mo  # noqa: PLC0415
    except ImportError:
        return False
    return mo.running_in_notebook()


class Trrackable(anywidget.AnyWidget):
    """Record a target widget's state as a branching provenance tree.

    Holds a direct Python reference to ``target`` and a :class:`ProvenanceGraph`
    that is the single source of truth. ``nodes`` and ``current_id`` are synced
    to the frontend, which is a thin view/controller over the tree.
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
        persist_path: str | os.PathLike[str] | None = None,
        store: Store | None = None,
        restore: dict | None = None,
        label_formatter: Callable[[dict, dict], str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Wrap ``target``, recording its synced traits into a provenance graph.

        Args:
            target: The widget whose state is tracked.
            traits: Trait names to record; inferred from ``target`` if omitted.
            debounce_ms: Collapse a burst of changes within this window into one
                commit; ``0`` records every change.
            persist_path: Convenience for ``store=JsonFileStore(persist_path)``.
            store: A persistence backend. When it holds saved state, that state
                is authoritative and is adopted on construction.
            restore: A :meth:`to_dict` payload to rebuild from directly, instead
                of inferring state from ``target`` or loading from a store.
            label_formatter: Builds a node's label from the previous and new
                tracked-trait states, ``(old, new) -> str``. Both are dicts
                keyed by tracked trait name. When omitted, a before→after diff
                of the changed traits is used. Useful for shortening noisy
                values, e.g. rounding floats.
            kwargs: Forwarded to :class:`anywidget.AnyWidget`.
        """
        super().__init__(**kwargs)
        self._target = target
        self._label_formatter = label_formatter
        self._controls_view: Any = None
        # One guard for both observers: recording must not fire on playback,
        # and playback must not fire on the current_id bump that ends a record.
        self._internal = False
        # When > 0, a burst of changes within this many milliseconds collapses
        # into a single commit. Useful for high-frequency sources like slider
        # drags.
        self._debounce_ms = debounce_ms
        self._debounce_timer: threading.Timer | None = None
        self._debounce_lock = threading.Lock()
        # Captured when a commit is scheduled (on the kernel thread). The timer
        # fires on a worker thread that lacks marimo's thread-local runtime
        # context, so the actual commit is marshaled back onto this loop.
        self._loop: asyncio.AbstractEventLoop | None = None
        if store is not None:
            self._store: Store | None = store
        elif persist_path is not None:
            self._store = JsonFileStore(persist_path)
        else:
            self._store = None
        self._persist_timer: threading.Timer | None = None
        self._persist_lock = threading.Lock()

        saved = restore
        if saved is None and self._store is not None:
            saved = self._store.load()
        if saved is not None:
            self._tracked = list(saved["tracked"])
            self._tree = ProvenanceGraph.from_dict(saved["tree"])
        else:
            if traits is None:
                base = set(anywidget.AnyWidget.class_traits(sync=True))
                traits = [
                    name
                    for name in target.traits(sync=True)
                    if name not in base and not name.startswith("_")
                ]
            self._tracked = list(traits)
            self._tree = ProvenanceGraph(self._snapshot(), now=_now())

        self._sync_tree()
        with self._guard():
            for name, value in self._tree.current.state.items():
                setattr(self._target, name, value)
        target.observe(self._on_target_change, names=self._tracked)
        self.observe(self._on_current_id_change, names="current_id")
        self.observe(self._on_relabel, names="_relabel")

        # Write the initial state only when we created it, so loading an
        # existing store does not immediately rewrite identical data.
        if self._store is not None and saved is None:
            self._persist_now()

    @contextlib.contextmanager
    def _guard(self) -> Iterator[None]:
        self._internal = True
        try:
            yield
        finally:
            self._internal = False

    def _snapshot(self) -> dict:
        return {name: getattr(self._target, name) for name in self._tracked}

    def _sync_tree(self) -> None:
        snapshot = self._tree.to_dict()
        self.nodes = snapshot["nodes"]
        with self._guard():
            self.current_id = snapshot["current_id"]

    def _commit(self) -> None:
        new_state = self._snapshot()
        label = (
            self._label_formatter(self._tree.current.state, new_state)
            if self._label_formatter is not None
            else None
        )
        node = self._tree.commit(new_state, now=_now(), label=label)
        self.nodes = self._tree.to_dict()["nodes"]
        with self._guard():
            self.current_id = node.id
        self._schedule_persist()

    def _on_target_change(self, _change: dict) -> None:
        if self._internal:
            return
        if self._debounce_ms > 0:
            self._schedule_commit()
        else:
            self._commit()

    def _schedule_commit(self) -> None:
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
        with self._debounce_lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
            timer = threading.Timer(self._debounce_ms / 1000, self._commit_debounced)
            timer.daemon = True
            self._debounce_timer = timer
            timer.start()

    def _commit_debounced(self) -> None:
        with self._debounce_lock:
            self._debounce_timer = None
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(self._commit)
        else:
            self._commit()

    def _cancel_pending_commit(self) -> None:
        with self._debounce_lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
                self._debounce_timer = None

    def flush(self) -> None:
        """Immediately commit a pending debounced change, if any."""
        with self._debounce_lock:
            timer = self._debounce_timer
            self._debounce_timer = None
        if timer is not None:
            timer.cancel()
            self._commit()

    def _schedule_persist(self) -> None:
        if self._store is None:
            return
        try:
            self._loop = asyncio.get_running_loop()
        except RuntimeError:
            self._loop = None
        with self._persist_lock:
            if self._persist_timer is not None:
                self._persist_timer.cancel()
            timer = threading.Timer(
                _PERSIST_DEBOUNCE_MS / 1000, self._persist_debounced
            )
            timer.daemon = True
            self._persist_timer = timer
            timer.start()

    def _persist_debounced(self) -> None:
        with self._persist_lock:
            self._persist_timer = None
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(self._persist_now)
        else:
            self._persist_now()

    def _persist_now(self) -> None:
        if self._store is None:
            return
        self._store.save(self.to_dict())

    def flush_persist(self) -> None:
        """Immediately write any pending coalesced state to the store."""
        with self._persist_lock:
            timer = self._persist_timer
            self._persist_timer = None
        if timer is not None:
            timer.cancel()
        self._persist_now()

    def _apply(self, node: Node) -> None:
        with self._guard():
            self.current_id = node.id
            for name, value in node.state.items():
                setattr(self._target, name, value)
        self._schedule_persist()

    def _on_current_id_change(self, change: dict) -> None:
        if self._internal:
            return
        self._cancel_pending_commit()
        node = self._tree.go_to(change["new"])
        with self._guard():
            for name, value in node.state.items():
                setattr(self._target, name, value)
        self._schedule_persist()

    def _on_relabel(self, change: dict) -> None:
        request = change["new"]
        if not request:
            return
        node_id = request.get("id")
        text = request.get("text")
        if node_id is None or text is None:
            return
        self._tree.relabel(text, node_id)
        self.nodes = self._tree.to_dict()["nodes"]
        self._schedule_persist()

    def undo(self) -> None:
        """Move to the parent state, applying it to the target."""
        self._cancel_pending_commit()
        node = self._tree.undo()
        if node is not None:
            self._apply(node)

    def redo(self) -> None:
        """Move to the newest child state, applying it to the target."""
        self._cancel_pending_commit()
        node = self._tree.redo()
        if node is not None:
            self._apply(node)

    def go_to(self, node_id: str) -> None:
        """Jump to ``node_id``, applying its state to the target."""
        self._cancel_pending_commit()
        self._apply(self._tree.go_to(node_id))

    def label(self, text: str, node_id: str | None = None) -> None:
        """Set the label of ``node_id`` (default: current node) to ``text``."""
        self._tree.relabel(text, node_id)
        self.nodes = self._tree.to_dict()["nodes"]
        self._schedule_persist()

    def to_dict(self) -> dict:
        """Serialize the tracked traits and the whole graph."""
        return {"tracked": list(self._tracked), "tree": self._tree.to_dict()}

    @classmethod
    def from_dict(
        cls,
        data: dict,
        target: Any,
        *,
        debounce_ms: int = 0,
        label_formatter: Callable[[dict, dict], str] | None = None,
    ) -> Trrackable:
        """Rebuild a Trrackable from :meth:`to_dict` output, wrapping ``target``."""
        return cls(
            target,
            debounce_ms=debounce_ms,
            label_formatter=label_formatter,
            restore=data,
        )

    @property
    def widget(self) -> Any:
        """The wrapped target widget, for display."""
        return self._target

    @property
    def controls(self) -> Any:
        """The provenance-tree control UI on its own.

        Under marimo this is a ``mo.ui.anywidget`` wrapper around the control
        widget rather than the :class:`Trrackable` itself. The wrapper renders
        the same controls but has no display hook, so it can be embedded in
        :attr:`view` — and displayed by itself — without re-entering
        :meth:`_display_` (which would otherwise recurse, since the view embeds
        the controls). Falls back to the raw widget when marimo is absent.
        """
        try:
            import marimo as mo  # noqa: PLC0415
        except ImportError:
            return self
        if self._controls_view is None:
            self._controls_view = mo.ui.anywidget(self)
        return self._controls_view

    @property
    def view(self) -> Any:
        """Target widget and controls side by side, widget filling the row.

        ``widths=[1, 0]`` lets the widget grow into the space the controls
        don't use. Passing the controls as a live object (rather than embedding
        their rendered HTML) keeps them a hydrated marimo element. Falls back to
        ``ipywidgets.HBox`` when marimo is not installed.
        """
        try:
            import marimo as mo  # noqa: PLC0415
        except ImportError:
            import ipywidgets  # noqa: PLC0415

            return ipywidgets.HBox([self.widget, self.controls])

        return mo.hstack(
            [self.widget, self.controls],
            justify="start",
            align="start",
            widths=[1, 0],
        )

    def _display_(self) -> Any:
        """Render a bare ``Trrackable`` as :attr:`view` under marimo.

        This is marimo's display hook, consulted before any other formatter, so
        returning the widget in a cell shows the target and its controls
        together. ``.widget`` and ``.controls`` still render each half alone.
        """
        return self.view

    def _repr_mimebundle_(self, **kwargs: Any) -> Any:
        """Jupyter display hook: a bare ``Trrackable`` renders as :attr:`view`.

        marimo renders via :meth:`_display_` and only reaches this hook to sync
        widget state, where the composite must not be built — so under marimo
        this defers to the plain control-widget bundle. In other hosts it is the
        display path, so it emits an ``HBox`` of the target and controls. The box
        references ``self`` by model id, so the frontend draws the controls
        without re-entering this hook.
        """
        if _in_marimo():
            return super()._repr_mimebundle_(**kwargs)
        try:
            import ipywidgets  # noqa: PLC0415
        except ImportError:
            return super()._repr_mimebundle_(**kwargs)
        return ipywidgets.HBox([self.widget, self])._repr_mimebundle_(**kwargs)
