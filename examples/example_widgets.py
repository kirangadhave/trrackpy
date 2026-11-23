"""The widgets that the example notebooks share."""

from __future__ import annotations

import anywidget
import traitlets


class Counter(anywidget.AnyWidget):
    """A button that counts its clicks."""

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


class FilterPanel(anywidget.AnyWidget):
    """A small form with a text, a number, a flag, and a list."""

    _esm = """
    const TAGS = ["red", "green", "blue"];

    export default {
      render({ model, el }) {
        el.style.cssText = "display:grid;gap:8px;max-width:320px;font:14px sans-serif";

        const search = document.createElement("input");
        search.placeholder = "search";
        search.oninput = () => {
          model.set("search", search.value);
          model.save_changes();
        };

        const slider = document.createElement("input");
        slider.type = "range";
        slider.min = 0;
        slider.max = 1;
        slider.step = 0.05;
        const sliderLabel = document.createElement("label");
        slider.onchange = () => {
          model.set("threshold", Number(slider.value));
          model.save_changes();
        };

        const enabled = document.createElement("input");
        enabled.type = "checkbox";
        enabled.onchange = () => {
          model.set("enabled", enabled.checked);
          model.save_changes();
        };
        const enabledLabel = document.createElement("label");
        enabledLabel.append(enabled, " enabled");

        const tagRow = document.createElement("div");
        const tagBoxes = TAGS.map((tag) => {
          const box = document.createElement("input");
          box.type = "checkbox";
          box.onchange = () => {
            const picked = TAGS.filter((_, i) => tagBoxes[i].checked);
            model.set("tags", picked);
            model.save_changes();
          };
          const label = document.createElement("label");
          label.style.marginRight = "8px";
          label.append(box, " " + tag);
          tagRow.append(label);
          return box;
        });

        const draw = () => {
          search.value = model.get("search");
          slider.value = model.get("threshold");
          sliderLabel.textContent = `threshold: ${model.get("threshold")}`;
          enabled.checked = model.get("enabled");
          const tags = model.get("tags");
          tagBoxes.forEach((box, i) => (box.checked = tags.includes(TAGS[i])));
        };
        model.on("change", draw);
        draw();

        el.append(search, sliderLabel, slider, enabledLabel, tagRow);
      },
    };
    """
    search = traitlets.Unicode("").tag(sync=True)
    threshold = traitlets.Float(0.5).tag(sync=True)
    enabled = traitlets.Bool(default_value=True).tag(sync=True)
    tags = traitlets.List(traitlets.Unicode(), []).tag(sync=True)
