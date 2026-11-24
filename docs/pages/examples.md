# Examples

Runnable marimo notebooks are in the
[examples folder](https://github.com/kirangadhave/trrackpy/tree/main/examples)
of the repository.

Each notebook wraps the same three widgets with a different store:

- a counter
- a form with a text, a number, a flag, and a list
- `Slider2D` from [wigglystuff](https://github.com/koaning/wigglystuff)

## Run one

Clone the repository, then from its root:

```sh
uv sync
uv run marimo edit examples/persisted/files.py
```

## Persisted

| Notebook | Where the state lives |
| --- | --- |
| [files.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/persisted/files.py) | JSON files, with the built-in `JsonFileStore` |
| [query_params.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/persisted/query_params.py) | The URL, with a store written in the notebook |
| [sqlite.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/persisted/sqlite.py) | A SQLite database, with a store written in the notebook |

![The Persisted example notebook](assets/persisted.png)

## Trrackable

| Notebook | Where the history lives |
| --- | --- |
| [files.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/trrackable/files.py) | JSON files, with the built-in `JsonFileStore` |
| [sqlite.py](https://github.com/kirangadhave/trrackpy/blob/main/examples/trrackable/sqlite.py) | A SQLite database, with a store written in the notebook |

![The Trrackable example notebook](assets/trrackable.png)
