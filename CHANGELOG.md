# Changelog

`trrack` and `trrack-widget` share one version number. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## Unreleased

## 0.1.1 - 2026-11-24

### Added

- `Trrackable` takes `buttons` and `graph` to show or hide the row of buttons and the history graph. Set either one later, such as `tracked.graph = False`.
- The History button shows and hides the graph.
- Drag the left edge of the history graph to resize it. The lock button turns resizing off.
- `Persisted` and `Trrackable` run in the browser on Pyodide, such as in a marimo WASM notebook.

### Changed

- In a narrow notebook, the controls move below the widget.
- With `debounce_ms`, `undo()`, `redo()`, and `go_to()` record a change that waits for the debounce before they move. Before, they dropped it.
- A subclass of `Persisted` or `Trrackable` replaces its parent on the same widget, so one change is recorded once.

### Fixed

- `close()` is safe to call more than once, and a new wrapper works on a widget whose wrapper you closed.
- With `debounce_ms`, `save()` and the save at interpreter exit include a change that waits for the debounce.

## 0.1.0 - 2026-11-23

The first release after two alphas, 0.0.1a1 and 0.0.1a2.

### Added

- `ProvenanceGraph` in `trrack` keeps every state as a node in a tree. It supports `commit`, `undo`, `redo`, `go_to`, and `relabel`. A commit after `undo` starts a new branch.
- `ProvenanceGraph.to_dict` and `ProvenanceGraph.from_dict` turn a graph into a JSON-compatible dict and back.
- `Persisted` in `trrack-widget` saves the state of an anywidget widget and restores it when the widget loads again. It has `state`, `save`, `reset`, and `close`.
- `Trrackable` records each change to an anywidget widget as a node in a branching history. It has `undo`, `redo`, `go_to`, and `label`.
- `Trrackable` takes `debounce_ms` to record a burst of changes as one node, `traits` to record some traits only, and `label_formatter` to write node labels.
- `Trrackable` and `Persisted` take a `store` to keep their data between sessions. `Trrackable` can open a store that `Persisted` saved.
- `Store` is the protocol for a store: any object with `save` and `load` methods.
- `JsonFileStore` keeps data in a JSON file and writes it atomically.
- `to_state` and `from_state` help a store keep plain values in its own shape, such as one URL parameter per value.
- `trrack_widget` exports `JsonFileStore`, `Store`, `to_state`, and `from_state`, so one import covers the common case.
- A save that fails shows its error under the widget. The widget keeps working.
- A saved value that the widget rejects is skipped. A message under the widget names the trait.
