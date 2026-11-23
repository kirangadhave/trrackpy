import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Trrackable: SQLite

    A store is any object with `save(dict)` and `load()`. This one keeps each
    widget's history as one row in a SQLite table, so many widgets share one
    database file.

    Change a widget, restart the kernel, and run the notebook again. The
    history comes back with it.
    """)
    return


@app.cell
def _():
    import contextlib
    import json
    import pathlib
    import sqlite3

    import marimo as mo
    from example_widgets import Counter, FilterPanel
    from wigglystuff import Slider2D

    from trrack_widget import Trrackable

    DATABASE = pathlib.Path(__file__).parent / "data" / "trrackable.sqlite"
    DATABASE.parent.mkdir(exist_ok=True)
    return (
        Counter,
        DATABASE,
        FilterPanel,
        Slider2D,
        Trrackable,
        contextlib,
        json,
        mo,
        pathlib,
        sqlite3,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The store

    It saves the payload as it is, so the same store works for `Persisted`.
    Each call opens its own connection, because a save can run on a background
    thread.
    """)
    return


@app.cell
def _(contextlib, json, pathlib, sqlite3):
    class SqliteStore:
        """Keep a widget's saved payload as one row in a SQLite table."""

        def __init__(self, path: str | pathlib.Path, key: str) -> None:
            self._path = path
            self._key = key
            self._run(
                "CREATE TABLE IF NOT EXISTS widget_state "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )

        def _run(self, sql: str, params: tuple = ()) -> tuple | None:
            with contextlib.closing(sqlite3.connect(self._path)) as db, db:
                return db.execute(sql, params).fetchone()

        def save(self, data: dict) -> None:
            self._run(
                "INSERT INTO widget_state VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (self._key, json.dumps(data)),
            )

        def load(self) -> dict | None:
            row = self._run(
                "SELECT value FROM widget_state WHERE key = ?", (self._key,)
            )
            return json.loads(row[0]) if row else None

    return (SqliteStore,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A counter
    """)
    return


@app.cell
def _(Counter, DATABASE, SqliteStore, Trrackable):
    counter = Trrackable(Counter(), store=SqliteStore(DATABASE, "counter"))
    counter
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A form with several values
    """)
    return


@app.cell
def _(DATABASE, FilterPanel, SqliteStore, Trrackable):
    panel = Trrackable(
        FilterPanel(),
        debounce_ms=300,
        store=SqliteStore(DATABASE, "panel"),
    )
    panel
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A wigglystuff widget
    """)
    return


@app.cell
def _(DATABASE, Slider2D, SqliteStore, Trrackable):
    slider = Trrackable(
        Slider2D(),
        ["x", "y"],
        debounce_ms=300,
        store=SqliteStore(DATABASE, "slider"),
    )
    slider
    return


if __name__ == "__main__":
    app.run()
