# Trrackable

`Trrackable` records every change to a widget as a history you can undo, redo,
and branch.

```python
from trrack_widget import Trrackable

tracked = Trrackable(counter)
tracked                    # shows the counter and its history
```

See [How the history works](concepts.md).

Try it here:

<iframe class="live-example" src="live/trrackable/" title="Live Trrackable example" height="360" loading="lazy"></iframe>

## Navigate

Use the controls next to the widget, or call the same actions from Python:

```python
tracked.undo()
tracked.redo()
tracked.go_to(node_id)          # jump to any node
tracked.label("before tuning")  # name the current node
```

Going back and then changing the widget starts a
[branch](concepts.md#branches).

## Find a node id

`go_to` takes a node id. The history is in `tracked.nodes`, a dict from id to
node. `tracked.current_id` is the id of the current node:

```python
tracked.current_id                           # id of the current node

for node_id, node in tracked.nodes.items():
    print(node_id, node["label"])            # every node, with its label

root_id = next(i for i, n in tracked.nodes.items() if n["parent"] is None)
tracked.go_to(root_id)                       # back to the first state
```

## Read the values

`state` holds the current values. `target` is the wrapped widget:

```python
tracked.state              # the current values, as a dict
tracked.target             # the wrapped widget
tracked.target.count = 3   # change a value, and it records a node
```

## Show and hide the controls

The controls are a row of buttons and the history graph. Pass `buttons` and
`graph` to choose which ones show:

```python
Trrackable(counter, graph=False)                  # buttons only
Trrackable(counter, buttons=False, graph=False)   # the widget only
```

The History button in the row shows and hides the graph. You can do the same
from Python:

```python
tracked.graph = True
```

`tracked.undo()` and the other actions work with the controls hidden.

## Resize the graph

Hover over the graph and drag the handle on its left edge. Click the lock
button to keep the width.

In a narrow notebook, the controls move below the widget.

## Record less

A slider or a text field changes many times in a second. `debounce_ms` records
a burst of changes as one node:

```python
Trrackable(slider, debounce_ms=300)
```

A change waits `debounce_ms` before it becomes a node. Call `flush()` to
record it now:

```python
tracked.flush()            # record the pending change
```

`save()`, `close()`, `undo()`, `redo()`, and `go_to()` record a pending change
first. Call `flush()` before `to_dict()` to include it. `flush()` does nothing
when no change is pending.

Pass trait names to record some of them only:

```python
Trrackable(slider, ["x", "y"])
```

## Name the nodes

Each node gets a [label](concepts.md#labels) from what changed. Pass
`label_formatter` to write your own from the old and new values:

```python
Trrackable(
    slider,
    label_formatter=lambda old, new: f"x = {new['x']:.2f}",
)
```

## Keep the history

Pass a store to keep the history between sessions:

```python
from trrack_widget import JsonFileStore

Trrackable(counter, store=JsonFileStore("history.json"))
```

Saves follow the same rules as in `Persisted`: see
[when the state is saved](persisted.md#when-the-state-is-saved) and
[when a save fails](persisted.md#when-a-save-fails).

Call `save()` to save now and `close()` when you are done. `close()` records a
pending change, saves, and closes the widget:

```python
tracked.save()
tracked.close()
```

`Trrackable` can open a store that [`Persisted`](persisted.md) saved. See
[Stores](stores.md) to write your own store and to read the saved data.

## Copy a history to another widget

`to_dict()` gives the whole history as plain data. `Trrackable.from_dict`
loads it onto a widget and sets the widget to the saved state:

```python
data = tracked.to_dict()

other = Trrackable.from_dict(data, other_counter)
```

`from_dict` takes the same `debounce_ms`, `label_formatter`, `buttons`, and
`graph` options as `Trrackable`.
