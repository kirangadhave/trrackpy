import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Trrackable: files

    `Trrackable` records each change to a widget as a node in a history. Use
    the controls next to the widget to undo, redo, or jump to any node.
    `JsonFileStore` keeps the history in a JSON file.

    Change a widget, restart the kernel, and run the notebook again. The
    history comes back with it.
    """)
    return


@app.cell
def _():
    import pathlib

    import marimo as mo
    from example_widgets import Counter, FilterPanel
    from wigglystuff import Slider2D

    from trrack_widget import JsonFileStore, Trrackable

    DATA = pathlib.Path(__file__).parent / "data"
    return Counter, DATA, FilterPanel, JsonFileStore, Slider2D, Trrackable, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A counter
    """)
    return


@app.cell
def _(Counter, DATA, JsonFileStore, Trrackable):
    counter = Trrackable(Counter(), store=JsonFileStore(DATA / "counter.json"))
    counter
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A form with several values

    `debounce_ms` records a burst of changes, such as typing, as one node.
    """)
    return


@app.cell
def _(DATA, FilterPanel, JsonFileStore, Trrackable):
    panel = Trrackable(
        FilterPanel(),
        debounce_ms=300,
        store=JsonFileStore(DATA / "panel.json"),
    )
    panel
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A wigglystuff widget

    Pass the trait names to record when you want some of them only.
    """)
    return


@app.cell
def _(DATA, JsonFileStore, Slider2D, Trrackable):
    slider = Trrackable(
        Slider2D(),
        ["x", "y"],
        debounce_ms=300,
        store=JsonFileStore(DATA / "slider.json"),
    )
    slider
    return


if __name__ == "__main__":
    app.run()
