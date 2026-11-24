from __future__ import annotations

import json
import time

import anywidget
import pytest
import traitlets
from helpers import FlakyStore, RecordingStore

from trrack import JsonFileStore
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
    assert tt.to_dict()["value"]["tracked"] == ["count"]


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
    assert payload["type"] == "graph"
    assert payload["value"]["tracked"] == ["count"]

    fresh = Counter()
    restored = Trrackable.from_dict(payload, fresh)
    assert restored.to_dict()["value"]["tree"] == payload["value"]["tree"]
    assert fresh.count == 1  # current node's state applied to the new target

    # Recording still works on the restored widget.
    fresh.count = 5
    assert restored.nodes[restored.current_id]["state"] == {"count": 5}


def test_file_store_restores_on_init(tmp_path):
    path = tmp_path / "state.json"

    first = Counter()
    tt1 = Trrackable(first, store=JsonFileStore(path))
    first.count = 7
    tt1.save()

    second = Counter()
    tt2 = Trrackable(second, store=JsonFileStore(path))
    # File is authoritative: the fresh target adopts the saved current state.
    assert second.count == 7
    assert len(tt2.nodes) == 2


def test_store_receives_graph_payload(tmp_path):
    store = JsonFileStore(tmp_path / "via_store.json")
    counter = Counter()
    tt = Trrackable(counter, store=store)
    counter.count = 3
    tt.save()
    payload = store.load()
    assert payload is not None
    assert payload["type"] == "graph"
    assert payload["value"]["tree"]["nodes"]  # the store received the payload


def test_file_store_writes_on_each_mutation(tmp_path):
    path = tmp_path / "state.json"
    counter = Counter()
    tt = Trrackable(counter, store=JsonFileStore(path))

    counter.count = 1
    counter.count = 2
    tt.save()
    after_commits = json.loads(path.read_text(encoding="utf-8"))
    assert after_commits["type"] == "graph"
    assert after_commits["value"]["tracked"] == ["count"]
    assert len(after_commits["value"]["tree"]["nodes"]) == 3

    # Navigation is a mutation too: it moves current_id and must be saved.
    tt.undo()
    tt.save()
    after_undo = json.loads(path.read_text(encoding="utf-8"))
    assert after_undo["type"] == "graph"
    assert (
        after_undo["value"]["tree"]["current_id"]
        != after_commits["value"]["tree"]["current_id"]
    )


def test_store_payload_without_type_keeps_history():
    first = Counter()
    tt1 = Trrackable(first)
    first.count = 1
    first.count = 2
    tt1.undo()
    bare_graph = tt1.to_dict()["value"]
    assert "type" not in bare_graph

    second = Counter()
    tt2 = Trrackable(second, store=RecordingStore(bare_graph))
    assert second.count == 1
    assert len(tt2.nodes) == 3
    assert tt2.to_dict()["value"]["tree"] == bare_graph["tree"]


def test_restore_accepts_payload_without_type():
    first = Counter()
    tt1 = Trrackable(first)
    first.count = 1
    bare_graph = tt1.to_dict()["value"]

    second = Counter()
    restored = Trrackable.from_dict(bare_graph, second)
    assert second.count == 1
    assert len(restored.nodes) == 2


def test_state_envelope_becomes_root_of_new_graph():
    store = RecordingStore({"type": "state", "value": {"count": 4}})
    counter = Counter()
    tt = Trrackable(counter, store=store)

    assert counter.count == 4
    assert len(tt.nodes) == 1
    assert tt.nodes[tt.current_id]["state"] == {"count": 4}
    assert tt.nodes[tt.current_id]["parent"] is None

    counter.count = 5
    tt.save()
    assert store.data is not None
    assert store.data["type"] == "graph"
    assert len(store.data["value"]["tree"]["nodes"]) == 2


def test_state_envelope_leaves_store_unchanged_until_a_change():
    saved = {"type": "state", "value": {"count": 4}}
    store = RecordingStore(saved)
    Trrackable(Counter(), store=store)
    assert store.data == saved


def test_state_envelope_ignores_untracked_keys():
    store = RecordingStore({"type": "state", "value": {"count": 4, "other": 1}})
    counter = Counter()
    tt = Trrackable(counter, store=store)

    assert counter.count == 4
    assert not hasattr(counter, "other")
    assert tt.nodes[tt.current_id]["state"] == {"count": 4}


def test_no_persist_without_store(tmp_path):
    counter = Counter()
    tt = Trrackable(counter)
    counter.count = 1
    tt.save()
    assert list(tmp_path.iterdir()) == []


def test_target_is_synced_as_a_widget_reference():
    counter = Counter()
    tt = Trrackable(counter)
    assert tt.target is counter
    assert tt.get_state()["target"] == f"anywidget:{counter.model_id}"


def test_target_must_be_a_widget():
    with pytest.raises(traitlets.TraitError, match="target"):
        Trrackable(traitlets.HasTraits())


def test_marimo_formats_bare_trrackable_as_one_widget():
    pytest.importorskip("marimo")
    from marimo._output.formatting import try_format

    tt = Trrackable(Counter())
    assert try_format(tt).data.count("<marimo-anywidget") == 1


def test_failed_background_save_shows_an_error_then_clears():
    store = FlakyStore()
    counter = Counter()
    tt = Trrackable(counter, store=store)
    assert tt.error == ""

    store.broken = True
    counter.count = 1
    time.sleep(0.15)
    assert tt.error == "Could not save: disk is full"

    store.broken = False
    counter.count = 2
    time.sleep(0.15)
    assert tt.error == ""


def test_bad_saved_state_value_is_skipped_and_reported():
    store = RecordingStore({"type": "state", "value": {"count": "abc"}})
    counter = Counter()

    tt = Trrackable(counter, store=store)

    assert counter.count == 0
    assert "count" in tt.error


def test_broken_store_does_not_block_construction():
    store = FlakyStore()
    store.broken = True

    tt = Trrackable(Counter(), store=store)

    assert len(tt.nodes) == 1
    assert tt.error == "Could not save: disk is full"


def test_new_trrackable_replaces_the_old_one_on_the_same_widget():
    counter = Counter()
    first = Trrackable(counter)
    second = Trrackable(counter)

    counter.count = 1

    assert len(first.nodes) == 1
    assert len(second.nodes) == 2


def test_close_stops_recording():
    counter = Counter()
    tt = Trrackable(counter)

    tt.close()
    counter.count = 1

    assert len(tt.nodes) == 1


def test_buttons_and_graph_show_by_default():
    tt = Trrackable(Counter())

    assert tt.buttons is True
    assert tt.graph is True


def test_hidden_controls_are_synced_to_the_frontend():
    tt = Trrackable(Counter(), buttons=False, graph=False)

    state = tt.get_state()
    assert state["buttons"] is False
    assert state["graph"] is False


def test_graph_can_be_hidden_after_construction():
    tt = Trrackable(Counter())

    tt.graph = False

    assert tt.get_state()["graph"] is False


def test_hidden_controls_still_record_and_navigate():
    counter = Counter()
    tt = Trrackable(counter, buttons=False, graph=False)

    counter.count = 1
    tt.undo()

    assert len(tt.nodes) == 2
    assert counter.count == 0


def test_control_visibility_is_not_saved():
    tt = Trrackable(Counter(), buttons=False, graph=False)

    assert set(tt.to_dict()["value"]) == {"tracked", "tree"}


def test_from_dict_sets_control_visibility():
    payload = Trrackable(Counter()).to_dict()

    restored = Trrackable.from_dict(payload, Counter(), buttons=False, graph=False)

    assert restored.buttons is False
    assert restored.graph is False
