import marimo

__generated_with = "0.23.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import anywidget
    import traitlets

    from trrack_widget import Trrackable

    return Trrackable, anywidget, traitlets


@app.cell(hide_code=True)
def _(anywidget, traitlets):
    class Counter(anywidget.AnyWidget):
        _esm = """
        export default {
          render({ model, el }) {
            const wrap = document.createElement("div");
            wrap.style.cssText = "display:flex;gap:8px;align-items:center;font-family:system-ui;";
            const label = document.createElement("span");
            const btn = document.createElement("button");
            btn.textContent = "bump";
            btn.style.cssText = "padding:4px 12px;cursor:pointer;";
            const update = () => { label.textContent = `count: ${model.get("count")}`; };
            update();
            const onClick = () => {
              model.set("count", model.get("count") + 1);
              model.save_changes();
            };
            btn.addEventListener("click", onClick);
            model.on("change:count", update);
            wrap.append(label, btn);
            el.appendChild(wrap);
            return () => {
              btn.removeEventListener("click", onClick);
              model.off("change:count", update);
            };
          }
        };
        """
        count = traitlets.Int(0).tag(sync=True)

    return (Counter,)


@app.cell
def _(Counter, Trrackable):
    counter = Counter()
    tt = Trrackable(counter)
    tt.view
    return


@app.cell(hide_code=True)
def _(anywidget, traitlets):
    class ColorMixer(anywidget.AnyWidget):
        r = traitlets.Int(99).tag(sync=True)
        g = traitlets.Int(102).tag(sync=True)
        b = traitlets.Int(241).tag(sync=True)

        _esm = """
        export default {
          render({ model, el }) {
            el.style.cssText = "font-family:system-ui;display:flex;flex-direction:column;gap:8px;width:220px;";
            const swatch = document.createElement("div");
            swatch.style.cssText = "height:64px;border-radius:8px;border:1px solid #e5e7eb;";
            const hex = document.createElement("div");
            hex.style.cssText = "font-size:13px;font-variant-numeric:tabular-nums;color:#374151;";
            const channels = ["r", "g", "b"];
            const paint = () => {
              const [r, g, b] = channels.map((c) => model.get(c));
              swatch.style.background = `rgb(${r}, ${g}, ${b})`;
              const toHex = (v) => v.toString(16).padStart(2, "0");
              hex.textContent = `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase();
            };
            el.appendChild(swatch);
            el.appendChild(hex);
            for (const c of channels) {
              const row = document.createElement("label");
              row.style.cssText = "display:flex;align-items:center;gap:8px;font-size:12px;";
              const tag = document.createElement("span");
              tag.textContent = c.toUpperCase();
              tag.style.width = "12px";
              const slider = document.createElement("input");
              slider.type = "range";
              slider.min = "0";
              slider.max = "255";
              slider.value = model.get(c);
              slider.style.flex = "1";
              slider.addEventListener("input", () => {
                model.set(c, Number(slider.value));
                model.save_changes();
              });
              model.on(`change:${c}`, () => {
                slider.value = model.get(c);
                paint();
              });
              row.appendChild(tag);
              row.appendChild(slider);
              el.appendChild(row);
            }
            paint();
          },
        };
        """

    return (ColorMixer,)


@app.cell
def _(ColorMixer, Trrackable):
    color = ColorMixer()
    tt_color = Trrackable(color, debounce_ms=300)
    tt_color.view
    return (tt_color,)


@app.cell
def _(tt_color):
    tt_color.to_dict()
    return


if __name__ == "__main__":
    app.run()
