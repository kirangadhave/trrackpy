from __future__ import annotations

import atexit

import anywidget
import pytest
import traitlets
from helpers import RecordingStore

import trrack_widget._persist as persist
from trrack_widget import Persisted, Trrackable

_NEVER_MS = 10000


class Counter(anywidget.AnyWidget):
    _esm = "export default { render() {} };"
    count = traitlets.Int(0).tag(sync=True)


def _make(wrapper, counter):
    if wrapper is Persisted:
        return Persisted(counter, store=RecordingStore())
    return Trrackable(counter)


def _states(store):
    nodes = store.data["value"]["tree"]["nodes"]
    return [node["state"] for node in nodes.values()]


@pytest.mark.parametrize("wrapper", [Persisted, Trrackable])
def test_close_twice_does_not_raise(wrapper):
    wrapped = _make(wrapper, Counter())
    wrapped.close()
    wrapped.close()


@pytest.mark.parametrize("wrapper", [Persisted, Trrackable])
def test_close_of_a_replaced_wrapper_does_not_raise(wrapper):
    counter = Counter()
    first = _make(wrapper, counter)
    _make(wrapper, counter)
    first.close()


def test_new_wrapper_after_close_records():
    counter = Counter()
    closed = Trrackable(counter)
    closed.close()

    tracked = Trrackable(counter)
    counter.count = 1

    assert len(tracked.nodes) == 2
    assert closed is not tracked


def test_subclass_replaces_its_parent_on_one_widget():
    class Mine(Trrackable):
        pass

    counter = Counter()
    parent = Trrackable(counter)
    child = Mine(counter)
    counter.count = 1

    assert len(parent.nodes) == 1
    assert len(child.nodes) == 2


def test_undo_records_a_pending_change_first():
    counter = Counter()
    tracked = Trrackable(counter, debounce_ms=_NEVER_MS)
    counter.count = 1
    tracked.flush()
    counter.count = 5  # waits for the debounce

    tracked.undo()
    assert counter.count == 1
    assert len(tracked.nodes) == 3

    tracked.redo()
    assert counter.count == 5


def test_go_to_records_a_pending_change_first():
    counter = Counter()
    tracked = Trrackable(counter, debounce_ms=_NEVER_MS)
    root_id = tracked.current_id
    counter.count = 5  # waits for the debounce

    tracked.go_to(root_id)

    assert counter.count == 0
    assert len(tracked.nodes) == 2


def test_undo_at_the_root_keeps_widget_and_history_equal():
    counter = Counter()
    tracked = Trrackable(counter, debounce_ms=_NEVER_MS)
    counter.count = 7  # waits for the debounce

    tracked.undo()

    assert counter.count == 0
    assert tracked.nodes[tracked.current_id]["state"] == {"count": 0}
    assert len(tracked.nodes) == 2


def test_save_includes_a_pending_change():
    store = RecordingStore()
    counter = Counter()
    tracked = Trrackable(counter, debounce_ms=_NEVER_MS, store=store)
    counter.count = 9  # waits for the debounce

    tracked.save()

    assert _states(store) == [{"count": 0}, {"count": 9}]


def test_exit_saves_a_pending_change():
    store = RecordingStore()
    counter = Counter()
    Trrackable(counter, debounce_ms=_NEVER_MS, store=store)
    counter.count = 9  # waits for the debounce

    persist._flush_all_at_exit()

    assert _states(store) == [{"count": 0}, {"count": 9}]


def test_wrappers_share_one_exit_hook():
    before = atexit._ncallbacks()
    for _ in range(20):
        Persisted(Counter(), store=RecordingStore())
    assert atexit._ncallbacks() == before


def test_cancel_stops_a_timer_that_already_fired():
    calls = []
    debouncer = persist.Debouncer(_NEVER_MS, lambda: calls.append(1))
    debouncer.schedule()
    timer = debouncer._timer
    assert timer is not None

    assert debouncer.cancel() is True
    timer.function(*timer.args, **timer.kwargs)

    assert calls == []
