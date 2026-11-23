import marimo

__generated_with = "0.25.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Persisted: URL query params

    A store is any object with `save(dict)` and `load()`. This one keeps each
    widget's state as JSON under its own key in the URL, so a link restores
    the widgets.

    Change a widget and watch the address bar. Copy the URL to a new tab, and
    the widgets come back as you left them.
    """)
    return


@app.cell
def _():
    import json

    import marimo as mo
    from example_widgets import Counter, FilterPanel
    from wigglystuff import Slider2D

    from trrack_widget import Persisted, from_state, to_state

    return Counter, FilterPanel, Persisted, Slider2D, from_state, json, mo, to_state


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## The store

    `to_state` gets the plain values out of the payload, so the URL stays
    short. `from_state` turns them back into a payload on load.
    """)
    return


@app.cell
def _(from_state, json, mo, to_state):
    class QueryParamStore:
        """Keep a widget's state as JSON in one URL query parameter."""

        def __init__(self, key: str) -> None:
            self._params = mo.query_params()
            self._key = key

        def save(self, data: dict) -> None:
            self._params[self._key] = json.dumps(to_state(data), separators=(",", ":"))

        def load(self) -> dict | None:
            raw = self._params.get(self._key)
            return from_state(json.loads(raw)) if raw else None

    return (QueryParamStore,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A counter
    """)
    return


@app.cell
def _(Counter, Persisted, QueryParamStore):
    counter = Persisted(Counter(), store=QueryParamStore("counter"))
    counter
    return (counter,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A form with several values
    """)
    return


@app.cell
def _(FilterPanel, Persisted, QueryParamStore):
    panel = Persisted(FilterPanel(), store=QueryParamStore("panel"))
    panel
    return (panel,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## A wigglystuff widget
    """)
    return


@app.cell
def _(Persisted, QueryParamStore, Slider2D):
    slider = Persisted(Slider2D(), ["x", "y"], store=QueryParamStore("slider"))
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
