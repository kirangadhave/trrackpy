from __future__ import annotations

import json

import pytest

import trrack
from trrack.persist import (
    JsonFileStore,
    graph_envelope,
    read_envelope,
    read_json,
    state_envelope,
    write_json_atomic,
)


def test_read_json_missing_returns_none(tmp_path):
    assert read_json(tmp_path / "absent.json") is None


def test_write_then_read_round_trip(tmp_path):
    path = tmp_path / "state.json"
    write_json_atomic(path, {"count": 1})
    assert read_json(path) == {"count": 1}


def test_overwrite_leaves_valid_json_and_no_temp_file(tmp_path):
    path = tmp_path / "state.json"
    write_json_atomic(path, {"count": 1})
    write_json_atomic(path, {"count": 2})
    assert json.loads(path.read_text(encoding="utf-8")) == {"count": 2}
    assert list(path.parent.iterdir()) == [path]


def test_json_file_store_round_trip(tmp_path):
    store = JsonFileStore(tmp_path / "state.json")
    assert store.load() is None
    store.save({"count": 7})
    assert store.load() == {"count": 7}


def test_graph_envelope_tags_the_value_as_graph():
    assert graph_envelope({"a": 1}) == {"type": "graph", "value": {"a": 1}}


def test_state_envelope_tags_the_value_as_state():
    assert state_envelope({"a": 1}) == {"type": "state", "value": {"a": 1}}


def test_read_envelope_reads_a_payload_without_type_as_a_graph():
    data = {"tracked": ["value"], "tree": {"nodes": {}}}
    assert read_envelope(data) == ("graph", data)


@pytest.mark.parametrize(
    ("build", "kind"),
    [(graph_envelope, "graph"), (state_envelope, "state")],
)
def test_read_envelope_returns_the_type_and_the_value(build, kind):
    assert read_envelope(build({"a": 1})) == (kind, {"a": 1})


def test_read_envelope_rejects_an_unknown_type():
    with pytest.raises(ValueError, match="other"):
        read_envelope({"type": "other", "value": {}})


def test_package_exports_the_envelope_functions():
    assert trrack.graph_envelope is graph_envelope
    assert trrack.state_envelope is state_envelope
    assert trrack.read_envelope is read_envelope
