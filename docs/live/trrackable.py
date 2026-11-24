import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
async def _():
    import sys

    import marimo as mo

    # In the browser, install the wheels that the docs build placed next to this
    # notebook. In a local session the workspace already provides the packages.
    if sys.platform == "emscripten":
        import micropip
        from pyodide.http import pyfetch

        public = mo.notebook_location() / "public"
        listing = await pyfetch(str(public / "wheels.txt"))
        names = (await listing.string()).split()
        await micropip.install([str(public / name) for name in names])
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    Click the counter, then undo and click again to start a branch.
    """)
    return


@app.cell
def _():
    # The docs pages show the code between these two markers.
    # --8<-- [start:example]
    import anywidget
    import traitlets

    from trrack_widget import Trrackable

    class Counter(anywidget.AnyWidget):
        _esm = """
        export default {
          render({ model, el }) {
            const button = document.createElement("button");
            const draw = () => (button.textContent = `count: ${model.get("count")}`);
            button.onclick = () => {
              model.set("count", model.get("count") + 1);
              model.save_changes();
            };
            model.on("change:count", draw);
            draw();
            el.append(button);
          },
        };
        """
        count = traitlets.Int(0).tag(sync=True)

    Trrackable(Counter())
    # --8<-- [end:example]
    return


if __name__ == "__main__":
    app.run()
