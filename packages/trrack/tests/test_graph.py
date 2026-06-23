from __future__ import annotations

import pytest

from trrack.graph import Node, ProvenanceGraph


def test_root_node_created_from_state():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    root = tree.root
    assert isinstance(root, Node)
    assert root.id == "r"
    assert root.parent is None
    assert root.children == []
    assert root.created_at == "t0"
    assert root.label == "initial"
    assert root.state == {"count": 0}
    assert tree.current is root
    assert tree.current_id == "r"


def test_commit_appends_child_and_advances_current():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    node = tree.commit({"count": 1}, now="t1", node_id="a")
    assert node.id == "a"
    assert node.parent == "r"
    assert node.state == {"count": 1}
    assert tree.root.children == ["a"]
    assert tree.current is node
    assert node.label == "count: 0 → 1"


def test_auto_label_multiple_traits_sorted():
    tree = ProvenanceGraph({"a": 1, "b": 1}, now="t0", root_id="r")
    node = tree.commit({"a": 2, "b": 3}, now="t1")
    assert node.label == "a: 1 → 2, b: 1 → 3"


def test_explicit_label_overrides_auto():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    node = tree.commit({"count": 1}, now="t1", label="mine")
    assert node.label == "mine"


def test_undo_moves_to_parent_and_stops_at_root():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    tree.commit({"count": 1}, now="t1", node_id="a")
    parent = tree.undo()
    assert parent is not None
    assert parent.id == "r"
    assert tree.undo() is None
    assert tree.current_id == "r"


def test_redo_follows_newest_child():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    tree.commit({"count": 1}, now="t1", node_id="a")
    tree.undo()
    tree.commit({"count": 2}, now="t2", node_id="b")  # sibling of "a"
    tree.undo()  # back to root
    newest = tree.redo()
    assert newest is not None
    assert newest.id == "b"  # newest child wins
    assert tree.redo() is None  # "b" is a leaf


def test_commit_after_undo_creates_branch():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    tree.commit({"count": 1}, now="t1", node_id="a")
    tree.undo()
    tree.commit({"count": 9}, now="t2", node_id="b")
    assert sorted(tree.root.children) == ["a", "b"]
    assert tree.nodes["a"].parent == "r"
    assert tree.nodes["b"].parent == "r"


def test_go_to_sets_current():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    tree.commit({"count": 1}, now="t1", node_id="a")
    assert tree.go_to("r").id == "r"
    assert tree.current_id == "r"


def test_go_to_unknown_raises():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    with pytest.raises(KeyError):
        tree.go_to("nope")


def test_relabel_current_and_explicit():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    tree.commit({"count": 1}, now="t1", node_id="a")
    tree.relabel("renamed")
    assert tree.nodes["a"].label == "renamed"
    tree.relabel("root!", node_id="r")
    assert tree.nodes["r"].label == "root!"


def test_to_dict_from_dict_round_trip():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    tree.commit({"count": 1}, now="t1", node_id="a")
    tree.undo()
    tree.commit({"count": 9}, now="t2", node_id="b")
    tree.go_to("a")

    d = tree.to_dict()
    assert d["root_id"] == "r"
    assert d["current_id"] == "a"
    assert set(d["nodes"]) == {"r", "a", "b"}

    restored = ProvenanceGraph.from_dict(d)
    assert restored.root_id == "r"
    assert restored.current_id == "a"
    assert sorted(restored.root.children) == ["a", "b"]
    assert restored.nodes["b"].state == {"count": 9}
    assert restored.to_dict() == d


def test_is_at_root_and_is_at_latest():
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    assert tree.is_at_root
    assert tree.is_at_latest

    tree.commit({"count": 1}, now="t1", node_id="a")
    assert not tree.is_at_root
    assert tree.is_at_latest

    tree.undo()
    assert tree.is_at_root
    assert not tree.is_at_latest


def test_save_and_load_round_trip(tmp_path):
    tree = ProvenanceGraph({"count": 0}, now="t0", root_id="r")
    tree.commit({"count": 1}, now="t1", node_id="a")
    tree.undo()
    path = tmp_path / "graph.json"

    tree.save(path)
    restored = ProvenanceGraph.load(path)

    assert restored is not None
    assert restored.to_dict() == tree.to_dict()


def test_load_missing_returns_none(tmp_path):
    assert ProvenanceGraph.load(tmp_path / "absent.json") is None
