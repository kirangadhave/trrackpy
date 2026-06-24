from __future__ import annotations

import json
import time

import anywidget
import pytest
import traitlets

from trrack_widget import Trrackable


class Counter(anywidget.AnyWidget):
    _esm = "export default { render() {} };"
    count = traitlets.Int(0).tag(sync=True)


def test_recording_builds_tree_and_syncs_current():
    counter = Counter()
    tt = Trrackable(counter)

    # Root captured at construction.
    assert len(tt.nodes) == 1
    root_id = tt.current_id

    counter.count = 1
    counter.count = 2

    assert len(tt.nodes) == 3
    current = tt.nodes[tt.current_id]
    assert current["state"] == {"count": 2}
    assert current["parent"] != root_id  # advanced down the tree


def test_tracked_traits_exclude_widget_internals():
    counter = Counter()
    tt = Trrackable(counter)
    assert tt._tracked == ["count"]


def test_frontend_navigation_applies_snapshot_to_target():
    counter = Counter()
    tt = Trrackable(counter)
    root_id = tt.current_id
    counter.count = 1
    counter.count = 2
    assert counter.count == 2

    # Simulate a frontend click setting current_id back to root.
    tt.current_id = root_id
    assert counter.count == 0
    # Applying a snapshot must NOT append a node.
    assert len(tt.nodes) == 3


def test_python_undo_redo_and_branch():
    counter = Counter()
    tt = Trrackable(counter)
    counter.count = 1
    tt.undo()
    assert counter.count == 0
    counter.count = 9  # branch off root
    assert counter.count == 9
    assert len(tt.nodes) == 3
    tt.redo()  # newest child of current leaf -> no-op here
    tt.go_to(tt.nodes[tt.current_id]["id"])  # idempotent


def test_label_relabels_current_node():
    counter = Counter()
    tt = Trrackable(counter)
    counter.count = 1
    tt.label("checkpoint")
    assert tt.nodes[tt.current_id]["label"] == "checkpoint"


def test_label_formatter_builds_node_labels():
    counter = Counter()
    tt = Trrackable(
        counter,
        label_formatter=lambda old, new: f"{old['count']}=>{new['count']}",
    )
    counter.count = 1
    counter.count = 2
    labels = [tt.nodes[nid]["label"] for nid in tt.nodes]
    assert "0=>1" in labels
    assert "1=>2" in labels


def test_default_label_used_without_formatter():
    counter = Counter()
    tt = Trrackable(counter)
    counter.count = 1
    assert tt.nodes[tt.current_id]["label"] == "count: 0 → 1"


def test_debounce_coalesces_rapid_changes():
    counter = Counter()
    tt = Trrackable(counter, debounce_ms=50)
    for i in range(1, 6):
        counter.count = i
    time.sleep(0.2)
    # The whole burst collapses into a single commit at the final value.
    assert len(tt.nodes) == 2
    assert tt.nodes[tt.current_id]["state"] == {"count": 5}


def test_flush_commits_pending_debounced_change():
    counter = Counter()
    tt = Trrackable(counter, debounce_ms=10000)
    counter.count = 1
    counter.count = 2
    assert len(tt.nodes) == 1  # still within the (long) debounce window
    tt.flush()
    assert len(tt.nodes) == 2
    assert tt.nodes[tt.current_id]["state"] == {"count": 2}


def test_navigation_cancels_pending_debounced_change():
    counter = Counter()
    tt = Trrackable(counter, debounce_ms=10000)
    counter.count = 1
    tt.flush()  # commit a real node so undo has somewhere to go
    counter.count = 5  # pending burst
    tt.undo()  # navigating away discards the uncommitted burst
    tt.flush()
    assert len(tt.nodes) == 2
    assert counter.count == 0


def test_to_dict_from_dict_restores_tree_and_target():
    counter = Counter()
    tt = Trrackable(counter)
    counter.count = 1
    counter.count = 2
    tt.undo()  # current at count==1, target restored to 1
    assert counter.count == 1

    payload = tt.to_dict()
    assert payload["tracked"] == ["count"]

    fresh = Counter()
    restored = Trrackable.from_dict(payload, fresh)
    assert restored.to_dict()["tree"] == payload["tree"]
    assert fresh.count == 1  # current node's state applied to the new target

    # Recording still works on the restored widget.
    fresh.count = 5
    assert restored.nodes[restored.current_id]["state"] == {"count": 5}


def test_persist_path_restores_on_init(tmp_path):
    path = tmp_path / "state.json"

    first = Counter()
    tt1 = Trrackable(first, persist_path=path)
    first.count = 7
    tt1.flush_persist()

    second = Counter()
    tt2 = Trrackable(second, persist_path=path)
    # File is authoritative: the fresh target adopts the saved current state.
    assert second.count == 7
    assert len(tt2.nodes) == 2


def test_store_argument_overrides_persist_path(tmp_path):
    from trrack import JsonFileStore

    store = JsonFileStore(tmp_path / "via_store.json")
    counter = Counter()
    tt = Trrackable(counter, store=store)
    counter.count = 3
    tt.flush_persist()
    payload = store.load()
    assert payload is not None
    assert payload["tree"]["nodes"]  # the store received the payload


def test_persist_path_writes_on_each_mutation(tmp_path):
    path = tmp_path / "state.json"
    counter = Counter()
    tt = Trrackable(counter, persist_path=path)

    counter.count = 1
    counter.count = 2
    tt.flush_persist()
    after_commits = json.loads(path.read_text(encoding="utf-8"))
    assert after_commits["tracked"] == ["count"]
    assert len(after_commits["tree"]["nodes"]) == 3

    # Navigation is a mutation too: it moves current_id and must be saved.
    tt.undo()
    tt.flush_persist()
    after_undo = json.loads(path.read_text(encoding="utf-8"))
    assert after_undo["tree"]["current_id"] != after_commits["tree"]["current_id"]


def test_no_persist_without_store(tmp_path):
    counter = Counter()
    tt = Trrackable(counter)
    counter.count = 1
    tt.flush_persist()
    assert list(tmp_path.iterdir()) == []


def test_bare_widget_displays_as_view():
    pytest.importorskip("marimo")
    counter = Counter()
    tt = Trrackable(counter)

    # The display hook renders the same composite as .view (a marimo hstack).
    assert type(tt._display_()) is type(tt.view)
    # .widget and .controls remain individual viewers.
    assert tt.widget is counter
    assert tt.controls is not tt


def test_controls_viewer_is_stable_and_recursion_free():
    pytest.importorskip("marimo")
    from marimo._output.formatting import try_format

    counter = Counter()
    tt = Trrackable(counter)

    # The controls viewer is cached and is not the Trrackable itself, so it
    # carries no _display_ hook — embedding it in the view cannot recurse.
    assert tt.controls is tt.controls
    assert tt.controls is not tt

    # Formatting a bare Trrackable resolves _display_ -> view -> controls
    # without re-entering _display_ (a recursion bug would raise here).
    formatted = try_format(tt)
    assert formatted.data


def test_jupyter_mimebundle_renders_composite(monkeypatch):
    ipywidgets = pytest.importorskip("ipywidgets")
    # Force the non-marimo (Jupyter) display path.
    import trrack_widget.widget as widget_mod

    monkeypatch.setattr(widget_mod, "_in_marimo", lambda: False)

    captured = {}
    real_hbox = ipywidgets.HBox

    def spy_hbox(children, *args, **kwargs):
        captured["children"] = children
        return real_hbox(children, *args, **kwargs)

    monkeypatch.setattr(ipywidgets, "HBox", spy_hbox)

    counter = Counter()
    tt = Trrackable(counter)

    # Bare display builds an HBox of the target and the controls, and returns
    # without recursing back into this hook (a recursion bug would raise).
    bundle = tt._repr_mimebundle_()
    assert bundle is not None
    assert captured["children"] == [counter, tt]


def test_panel_layout_defaults_to_docked_and_expanded_true():
    counter = Counter()
    tt = Trrackable(counter)
    assert tt.panel_layout == "docked"
    assert tt.expanded is True


def test_panel_layout_and_expanded_are_configurable():
    counter = Counter()
    tt = Trrackable(counter, panel_layout="floating", expanded=False)
    assert tt.panel_layout == "floating"
    assert tt.expanded is False


def test_panel_layout_and_expanded_are_not_recorded():
    # UI state must never leak into the provenance payload.
    counter = Counter()
    tt = Trrackable(counter, panel_layout="floating", expanded=False)
    payload = tt.to_dict()
    assert "panel_layout" not in payload
    assert "expanded" not in payload
    assert payload["tracked"] == ["count"]
