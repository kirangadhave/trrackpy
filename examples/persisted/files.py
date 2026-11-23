import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Persisted: files

    `Persisted` saves a widget's state and restores it the next time it loads.
    `JsonFileStore` keeps that state in a JSON file.

    Change a widget, restart the kernel, and run the notebook again. Each
    widget comes back as you left it.
    """)
    return


@app.cell
def _():
    import pathlib

    import marimo as mo
    from example_widgets import Counter, FilterPanel
    from wigglystuff import Slider2D

    from trrack_widget import JsonFileStore, Persisted

    DATA = pathlib.Path(__file__).parent / "data"
    return Counter, DATA, FilterPanel, JsonFileStore, Persisted, Slider2D, mo


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A counter
    """)
    return


@app.cell
def _(Counter, DATA, JsonFileStore, Persisted):
    counter = Persisted(Counter(), store=JsonFileStore(DATA / "counter.json"))
    counter
    return (counter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A form with several values
    """)
    return


@app.cell
def _(DATA, FilterPanel, JsonFileStore, Persisted):
    panel = Persisted(FilterPanel(), store=JsonFileStore(DATA / "panel.json"))
    panel
    return (panel,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A wigglystuff widget

    Pass the trait names to save when you want some of them only.
    """)
    return


@app.cell
def _(DATA, JsonFileStore, Persisted, Slider2D):
    slider = Persisted(
        Slider2D(), ["x", "y"], store=JsonFileStore(DATA / "slider.json")
    )
    slider
    return (slider,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Start over

    `reset()` puts a widget back to the values it started with, and saves them.
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
