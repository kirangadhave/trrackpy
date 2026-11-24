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


@app.cell
def _():
    import pathlib

    import anywidget
    import traitlets

    from trrack_widget import JsonFileStore, Persisted

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

    FILE = pathlib.Path("counter.json")
    return Counter, FILE, JsonFileStore, Persisted


@app.cell
def _(Counter, FILE, JsonFileStore, Persisted):
    Persisted(Counter(), store=JsonFileStore(FILE))
    return


@app.cell(hide_code=True)
def _(FILE, mo):
    refresh = mo.ui.refresh(default_interval="1s", label=f"Saved in {FILE}")
    reload = mo.ui.button(
        value=0, on_click=lambda n: n + 1, label="Make a new widget from the file"
    )
    refresh
    return refresh, reload


@app.cell(hide_code=True)
def _(FILE, mo, refresh):
    refresh
    mo.md(
        f"```json\n{FILE.read_text()}\n```"
        if FILE.exists()
        else "_Nothing is saved yet. Click the counter._"
    )
    return


@app.cell(hide_code=True)
def _(reload):
    reload
    return


@app.cell
def _(Counter, FILE, JsonFileStore, Persisted, mo, reload):
    mo.stop(reload.value == 0)
    Persisted(Counter(), store=JsonFileStore(FILE))
    return


if __name__ == "__main__":
    app.run()
