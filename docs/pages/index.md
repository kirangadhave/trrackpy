# trrackpy

Track the state of [anywidget](https://anywidget.dev) widgets.

Click the counter, undo, and click again:

<iframe class="live-example" src="live/trrackable/" title="Live Trrackable example" height="360"></iframe>

This is the code that runs above:

```python
--8<-- "docs/live/trrackable.py:example"
```

- [`Persisted`](persisted.md) saves a widget's state and restores it the next
  time it loads.
- [`Trrackable`](trrackable.md) records every change as a history you can
  navigate.
- A [store](stores.md) decides where the state lives: a file, a database, the
  URL. Write your own with two methods.

## Where to start

1. [Install](install.md) the package.
2. Follow the [Quickstart](quickstart.md).
3. Read the guides for [Persisted](persisted.md) and
   [Trrackable](trrackable.md).
4. Run an [example notebook](examples.md).
