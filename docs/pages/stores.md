# Stores

A store decides where a widget's state lives. Both `Persisted` and `Trrackable`
take one as `store=`.

## The file store

`JsonFileStore` keeps the state in a JSON file.

```python
from trrack_widget import JsonFileStore

Persisted(counter, store=JsonFileStore("state.json"))
```

It writes to a temporary file first and then moves it into place, so a crash
cannot leave a half-written file.

## Write your own

A store is any class with two methods:

```python
class MyStore:
    def save(self, data: dict) -> None: ...
    def load(self) -> dict | None: ...   # None when nothing is saved
```

`data` is a JSON-compatible dict. `save` gets it after each change, and `load`
runs one time, when the wrapper is created.

## Example: SQLite

This store saves the dict as it is, one row per widget. It works for both
wrappers.

```python
import contextlib
import json
import sqlite3


class SqliteStore:
    def __init__(self, path, key):
        self._path, self._key = path, key
        self._run(
            "CREATE TABLE IF NOT EXISTS widget_state "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )

    def _run(self, sql, params=()):
        with contextlib.closing(sqlite3.connect(self._path)) as db, db:
            return db.execute(sql, params).fetchone()

    def save(self, data):
        self._run(
            "INSERT INTO widget_state VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (self._key, json.dumps(data)),
        )

    def load(self):
        row = self._run(
            "SELECT value FROM widget_state WHERE key = ?", (self._key,)
        )
        return json.loads(row[0]) if row else None
```

```python
Persisted(counter, store=SqliteStore("app.sqlite", "counter"))
```

Each call opens its own connection, because a save can run on a background
thread.

## Example: the URL

A store for `Persisted` can keep the plain values in its own shape. `to_state`
gets them out of `data`, and `from_state` turns them back.

This store keeps a widget's state in the URL of a marimo notebook, so a link
restores the widget:

```python
import json

import marimo as mo
from trrack_widget import from_state, to_state


class QueryParamStore:
    def __init__(self, key):
        self._params = mo.query_params()
        self._key = key

    def save(self, data):
        self._params[self._key] = json.dumps(to_state(data))

    def load(self):
        raw = self._params.get(self._key)
        return from_state(json.loads(raw)) if raw else None
```

```python
Persisted(counter, store=QueryParamStore("counter"))
```

The URL then holds `?counter={"count":3}`.

!!! note "For Persisted only"

    `to_state` raises `ValueError` for a `Trrackable` history. A history grows
    with every change, and it does not fit in a URL.

## What is in the saved data

You only need this to read a saved file by hand. The data has a `type` and a
`value`:

```json
{"type": "state", "value": {"count": 3}}
```

```json
{"type": "graph", "value": {"tracked": ["count"], "tree": {"...": "..."}}}
```

`Persisted` saves `state`. `Trrackable` saves `graph`.

- `Trrackable` can open a `state` file. The state becomes the first node of a
  new history.
- `Persisted` does not open a `graph` file, because it would overwrite the
  history.
