from __future__ import annotations

import json

from trrack.persist import JsonFileStore, read_json, write_json_atomic


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
