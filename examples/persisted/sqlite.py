import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Persisted: SQLite

    A store is any object with `save(dict)` and `load()`. This one keeps each
    widget's payload as one row in a SQLite table, so many widgets share one
    database file.

    Change a widget, restart the kernel, and run the notebook again. Each
    widget comes back as you left it.
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

    from trrack_widget import Persisted

    DATABASE = pathlib.Path(__file__).parent / "data" / "persisted.sqlite"
    DATABASE.parent.mkdir(exist_ok=True)
    return (
        Counter,
        DATABASE,
        FilterPanel,
        Persisted,
        Slider2D,
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

    It saves the payload as it is, so it needs no conversion. Each call opens
    its own connection, because a save can run on a background thread.
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
def _(Counter, DATABASE, Persisted, SqliteStore):
    counter = Persisted(Counter(), store=SqliteStore(DATABASE, "counter"))
    counter
    return (counter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A form with several values
    """)
    return


@app.cell
def _(DATABASE, FilterPanel, Persisted, SqliteStore):
    panel = Persisted(FilterPanel(), store=SqliteStore(DATABASE, "panel"))
    panel
    return (panel,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A wigglystuff widget
    """)
    return


@app.cell
def _(DATABASE, Persisted, Slider2D, SqliteStore):
    slider = Persisted(Slider2D(), ["x", "y"], store=SqliteStore(DATABASE, "slider"))
    slider
    return (slider,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Start over
    """)
    return


@app.cell
def _(counter, mo, panel, slider):
    mo.ui.button(
        label="Reset all",
        on_click=lambda _: [widget.reset() for widget in (counter, panel, slider)],
    )
    return


if __name__ == "__main__":
    app.run()
