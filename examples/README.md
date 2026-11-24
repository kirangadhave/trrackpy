# Examples

marimo notebooks that show `Persisted` and `Trrackable` with different stores.

<!-- --8<-- [start:widgets] -->
Each notebook wraps the same three widgets:

- a counter
- a form with a text, a number, a flag, and a list
- `Slider2D` from [wigglystuff](https://github.com/koaning/wigglystuff)
<!-- --8<-- [end:widgets] -->

## Run one

From the repository root:

```sh
uv run marimo edit examples/persisted/files.py
```

## Persisted

Start here. `Persisted` saves a widget's state and restores it.

<!-- --8<-- [start:persisted] -->
| Notebook | Where the state lives |
| --- | --- |
| [persisted/files.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/persisted/files.py) | JSON files, with the built-in `JsonFileStore` |
| [persisted/query_params.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/persisted/query_params.py) | The URL, with a store written in the notebook |
| [persisted/sqlite.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/persisted/sqlite.py) | A SQLite database, with a store written in the notebook |
<!-- --8<-- [end:persisted] -->

## Trrackable

`Trrackable` records every change as a history with undo and redo.

<!-- --8<-- [start:trrackable] -->
| Notebook | Where the history lives |
| --- | --- |
| [trrackable/files.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/trrackable/files.py) | JSON files, with the built-in `JsonFileStore` |
| [trrackable/sqlite.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/trrackable/sqlite.py) | A SQLite database, with a store written in the notebook |
<!-- --8<-- [end:trrackable] -->

There is no URL example for `Trrackable`, because a history does not fit in a
URL.

## Layout

```
examples/
  example_widgets.py   the counter and the form, shared by every notebook
  persisted/
  trrackable/
```

The notebooks import `example_widgets` through the `pythonpath` setting for
marimo in `pyproject.toml`. Each notebook saves into a `data` folder next to
it, which git ignores.
