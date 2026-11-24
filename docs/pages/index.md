# trrackpy

Track the state of [anywidget](https://anywidget.dev) widgets.

```python
from trrack_widget import JsonFileStore, Persisted, Trrackable

Persisted(counter, store=JsonFileStore("state.json"))   # comes back as you left it
Trrackable(counter)                                      # undo, redo, and branch
```

- [`Persisted`](persisted.md) saves a widget's state and restores it the next
  time it loads.
- [`Trrackable`](trrackable.md) records every change as a history you can
  navigate.
- A [store](stores.md) decides where the state lives: a file, a database, the
  URL. Write your own with two methods.

Both work with any [anywidget](https://anywidget.dev).

## Where to start

1. [Install](install.md) the package.
2. Read [Persisted](persisted.md). It is the simpler of the two.
3. Run an [example notebook](examples.md).
