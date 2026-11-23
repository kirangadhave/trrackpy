# Examples

marimo notebooks that show `Persisted` and `Trrackable` with different stores.

Each notebook wraps the same three widgets:

- a counter
- a form with a text, a number, a flag, and a list
- `Slider2D` from [wigglystuff](https://github.com/koaning/wigglystuff)

## Run one

From the repository root:

```sh
uv run marimo edit examples/persisted/files.py
```

## Persisted

Start here. `Persisted` saves a widget's state and restores it.

| Notebook | Where the state lives |
| --- | --- |
| [persisted/files.py](persisted/files.py) | JSON files, with the built-in `JsonFileStore` |
| [persisted/query_params.py](persisted/query_params.py) | The URL, with a store written in the notebook |
| [persisted/sqlite.py](persisted/sqlite.py) | A SQLite database, with a store written in the notebook |

## Trrackable

`Trrackable` records every change as a history with undo and redo.

| Notebook | Where the history lives |
| --- | --- |
| [trrackable/files.py](trrackable/files.py) | JSON files, with the built-in `JsonFileStore` |
| [trrackable/sqlite.py](trrackable/sqlite.py) | A SQLite database, with a store written in the notebook |

There is no URL example for `Trrackable`. A history grows with every change,
and it does not fit in a URL.

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
