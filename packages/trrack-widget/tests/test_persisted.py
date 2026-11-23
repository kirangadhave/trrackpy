from __future__ import annotations

import json
import time

import anywidget
import pytest
import traitlets
from helpers import FlakyStore, RecordingStore

from trrack import JsonFileStore
from trrack_widget import Persisted

# Longer than the save window that conftest.py sets, so a pending save lands.
_AFTER_COALESCE_WINDOW_S = 0.15


class Counter(anywidget.AnyWidget):
    _esm = "export default { render() {} };"
    count = traitlets.Int(0).tag(sync=True)
    step = traitlets.Int(1).tag(sync=True)


def test_empty_store_gets_state_envelope_on_construction():
    store = RecordingStore()
    Persisted(Counter(), store=store)
    assert store.saves == [{"type": "state", "value": {"count": 0, "step": 1}}]


def test_change_and_flush_saves_new_value():
    store = RecordingStore()
    counter = Counter()
    persisted = Persisted(counter, store=store)

    counter.count = 3
    persisted.save()

    assert store.data == {"type": "state", "value": {"count": 3, "step": 1}}


def test_burst_of_changes_gives_one_write():
    store = RecordingStore()
    counter = Counter()
    Persisted(counter, store=store)
    assert len(store.saves) == 1

    for i in range(1, 6):
        counter.count = i
    assert len(store.saves) == 1  # the burst is still inside the window
    time.sleep(_AFTER_COALESCE_WINDOW_S)

    assert len(store.saves) == 2
    assert store.saves[-1]["value"]["count"] == 5


def test_second_persisted_restores_value_onto_new_target():
    store = RecordingStore()
    first = Counter()
    writer = Persisted(first, store=store)
    first.count = 7
    writer.save()

    second = Counter()
    reader = Persisted(second, store=store)

    assert second.count == 7
    assert reader.state == {"count": 7, "step": 1}


def test_saved_key_that_is_not_tracked_has_no_effect():
    store = RecordingStore(
        {"type": "state", "value": {"count": 4, "step": 9, "other": 1}}
    )
    counter = Counter()
    persisted = Persisted(counter, ["count"], store=store)

    assert counter.count == 4
    assert counter.step == 1
    assert not hasattr(counter, "other")
    assert persisted.state == {"count": 4}


def test_graph_envelope_raises():
    store = RecordingStore({"type": "graph", "value": {"tracked": [], "tree": {}}})
    with pytest.raises(ValueError, match="Trrackable"):
        Persisted(Counter(), store=store)
    assert store.saves == []


def test_payload_without_type_raises():
    store = RecordingStore({"tracked": ["count"], "tree": {}})
    with pytest.raises(ValueError, match="Trrackable"):
        Persisted(Counter(), store=store)
    assert store.saves == []


def test_failed_construction_leaves_target_unobserved():
    store = RecordingStore({"type": "graph", "value": {"tracked": [], "tree": {}}})
    counter = Counter()
    with pytest.raises(ValueError, match="Trrackable"):
        Persisted(counter, store=store)

    counter.count = 1
    time.sleep(_AFTER_COALESCE_WINDOW_S)

    assert store.saves == []


def test_json_file_store_writes_state_file(tmp_path):
    path = tmp_path / "state.json"
    counter = Counter()
    persisted = Persisted(counter, store=JsonFileStore(path))

    counter.count = 2
    persisted.save()

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "type": "state",
        "value": {"count": 2, "step": 1},
    }


def test_state_and_target():
    counter = Counter()
    persisted = Persisted(counter, store=RecordingStore())

    counter.count = 6

    assert persisted.state == {"count": 6, "step": 1}
    assert persisted.target is counter


def test_restore_does_not_write_to_store():
    store = RecordingStore({"type": "state", "value": {"count": 4, "step": 2}})
    counter = Counter()
    Persisted(counter, store=store)
    assert counter.count == 4

    time.sleep(_AFTER_COALESCE_WINDOW_S)

    assert store.saves == []


def test_change_after_restore_writes_to_store():
    store = RecordingStore({"type": "state", "value": {"count": 4}})
    counter = Counter()
    persisted = Persisted(counter, store=store)

    counter.count = 5
    persisted.save()

    assert store.saves == [{"type": "state", "value": {"count": 5, "step": 1}}]


def test_reset_returns_widget_to_start_values_and_saves_them():
    store = RecordingStore()
    counter = Counter(count=2)
    persisted = Persisted(counter, store=store)
    counter.count = 9
    counter.step = 5

    persisted.reset()

    assert persisted.state == {"count": 2, "step": 1}
    assert store.data == {"type": "state", "value": {"count": 2, "step": 1}}


def test_reset_uses_values_from_before_the_restore():
    store = RecordingStore({"type": "state", "value": {"count": 4, "step": 2}})
    counter = Counter()
    persisted = Persisted(counter, store=store)
    assert counter.count == 4

    persisted.reset()

    assert persisted.state == {"count": 0, "step": 1}
    assert store.data == {"type": "state", "value": {"count": 0, "step": 1}}


def test_reset_writes_once():
    store = RecordingStore()
    counter = Counter()
    persisted = Persisted(counter, store=store)
    counter.count = 3
    persisted.save()
    writes = len(store.saves)

    persisted.reset()
    time.sleep(_AFTER_COALESCE_WINDOW_S)

    assert len(store.saves) == writes + 1


def test_target_is_synced_as_a_widget_reference():
    counter = Counter()
    persisted = Persisted(counter, store=RecordingStore())
    assert persisted.get_state()["target"] == f"anywidget:{counter.model_id}"


def test_target_must_be_a_widget():
    with pytest.raises(traitlets.TraitError, match="target"):
        Persisted(traitlets.HasTraits(), store=RecordingStore())


def test_failed_background_save_shows_an_error():
    store = FlakyStore()
    counter = Counter()
    persisted = Persisted(counter, store=store)
    assert persisted.error == ""

    store.broken = True
    counter.count = 1
    time.sleep(_AFTER_COALESCE_WINDOW_S)

    assert persisted.error == "Could not save: disk is full"


def test_error_clears_after_the_next_good_save():
    store = FlakyStore()
    counter = Counter()
    persisted = Persisted(counter, store=store)
    store.broken = True
    counter.count = 1
    time.sleep(_AFTER_COALESCE_WINDOW_S)
    assert persisted.error

    store.broken = False
    counter.count = 2
    time.sleep(_AFTER_COALESCE_WINDOW_S)

    assert persisted.error == ""
    assert store.data == {"type": "state", "value": {"count": 2, "step": 1}}


def test_flush_raises_and_shows_the_error():
    store = FlakyStore()
    persisted = Persisted(Counter(), store=store)
    store.broken = True

    with pytest.raises(OSError, match="disk is full"):
        persisted.save()

    assert persisted.error == "Could not save: disk is full"


def test_package_exports_the_store_names():
    import trrack
    import trrack_widget

    assert trrack_widget.JsonFileStore is trrack.JsonFileStore
    assert trrack_widget.Store is trrack.Store
    assert trrack_widget.to_state is trrack.to_state
    assert trrack_widget.from_state is trrack.from_state


def test_bad_saved_value_is_skipped_and_reported():
    store = RecordingStore({"type": "state", "value": {"count": "abc", "step": 2}})
    counter = Counter()

    persisted = Persisted(counter, store=store)

    assert persisted.state == {"count": 0, "step": 2}
    assert "count" in persisted.error
    assert "Ignored" in persisted.error


def test_unrecognized_payload_raises_a_clear_error():
    with pytest.raises(ValueError, match="Unrecognized"):
        Persisted(Counter(), store=RecordingStore({}))
    with pytest.raises(ValueError, match="Unrecognized"):
        Persisted(Counter(), store=RecordingStore({"type": "state", "value": None}))


def test_new_wrapper_replaces_the_old_one_on_the_same_widget():
    store = RecordingStore()
    counter = Counter()
    Persisted(counter, store=store)
    Persisted(counter, store=store)
    writes = len(store.saves)

    counter.count = 1
    time.sleep(_AFTER_COALESCE_WINDOW_S)

    assert len(store.saves) == writes + 1


def test_close_stops_saving():
    store = RecordingStore()
    counter = Counter()
    persisted = Persisted(counter, store=store)
    counter.count = 1

    persisted.close()
    writes = len(store.saves)
    assert store.data == {"type": "state", "value": {"count": 1, "step": 1}}

    counter.count = 2
    time.sleep(_AFTER_COALESCE_WINDOW_S)

    assert len(store.saves) == writes


def test_broken_store_does_not_block_construction():
    store = FlakyStore()
    store.broken = True

    persisted = Persisted(Counter(), store=store)

    assert persisted.state == {"count": 0, "step": 1}
    assert persisted.error == "Could not save: disk is full"


def test_reset_with_a_broken_store_resets_and_reports():
    store = FlakyStore()
    counter = Counter()
    persisted = Persisted(counter, store=store)
    counter.count = 5
    store.broken = True

    persisted.reset()

    assert counter.count == 0
    assert persisted.error == "Could not save: disk is full"


def test_saves_do_not_overlap():
    import threading

    class SlowStore(RecordingStore):
        active = 0
        most_active = 0

        def save(self, data: dict) -> None:
            self.active += 1
            self.most_active = max(self.most_active, self.active)
            time.sleep(0.02)
            self.active -= 1
            super().save(data)

    store = SlowStore()
    persisted = Persisted(Counter(), store=store)
    threads = [threading.Thread(target=persisted.save) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert store.most_active == 1


def test_pending_save_is_written_at_exit():
    from trrack_widget._persist import _flush_at_exit

    store = RecordingStore()
    counter = Counter()
    persisted = Persisted(counter, store=store)
    counter.count = 3

    import weakref

    writer = persisted._writer
    assert writer is not None
    _flush_at_exit(weakref.ref(writer))

    assert store.data == {"type": "state", "value": {"count": 3, "step": 1}}

    writes = len(store.saves)
    _flush_at_exit(weakref.ref(writer))
    assert len(store.saves) == writes
