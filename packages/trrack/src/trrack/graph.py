"""The provenance graph model: full-state snapshot nodes and navigation."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING

from .persist import read_json, write_json_atomic

if TYPE_CHECKING:
    import os


@dataclass
class Node:
    """A single full-state snapshot and its position in the graph."""

    id: str
    parent: str | None
    children: list[str]
    created_at: str
    label: str
    state: dict


class ProvenanceGraph:
    """A branching graph of full-state snapshots.

    Pure model: no widget or marimo imports. Timestamps are supplied by the
    caller via ``now`` so the model performs no I/O and stays deterministic.
    """

    def __init__(
        self,
        root_state: dict,
        *,
        now: str,
        root_id: str | None = None,
    ) -> None:
        """Create the graph with a single root holding ``root_state``."""
        rid = root_id or uuid.uuid4().hex
        root = Node(
            id=rid,
            parent=None,
            children=[],
            created_at=now,
            label="initial",
            state=dict(root_state),
        )
        self.nodes: dict[str, Node] = {rid: root}
        self.root_id = rid
        self.current_id = rid

    @property
    def current(self) -> Node:
        """The node the graph is currently positioned at."""
        return self.nodes[self.current_id]

    @property
    def root(self) -> Node:
        """The root node the graph started from."""
        return self.nodes[self.root_id]

    @property
    def is_at_root(self) -> bool:
        """Whether the current node is the root (nothing to undo)."""
        return self.current.parent is None

    @property
    def is_at_latest(self) -> bool:
        """Whether the current node is a leaf (nothing to redo)."""
        return not self.current.children

    def commit(
        self,
        state: dict,
        *,
        now: str,
        label: str | None = None,
        node_id: str | None = None,
    ) -> Node:
        """Append ``state`` as a child of the current node and move there."""
        nid = node_id or uuid.uuid4().hex
        parent = self.current
        resolved_label = (
            label if label is not None else self._auto_label(parent.state, state)
        )
        node = Node(
            id=nid,
            parent=parent.id,
            children=[],
            created_at=now,
            label=resolved_label,
            state=dict(state),
        )
        self.nodes[nid] = node
        parent.children.append(nid)
        self.current_id = nid
        return node

    def undo(self) -> Node | None:
        """Move to the parent of the current node, or ``None`` at the root."""
        node = self.current
        if node.parent is None:
            return None
        self.current_id = node.parent
        return self.current

    def redo(self) -> Node | None:
        """Move to the newest child of the current node, or ``None`` at a leaf."""
        node = self.current
        if not node.children:
            return None
        self.current_id = node.children[-1]  # newest child (append order)
        return self.current

    def go_to(self, node_id: str) -> Node:
        """Jump to ``node_id``; raises ``KeyError`` if it is unknown."""
        if node_id not in self.nodes:
            raise KeyError(node_id)
        self.current_id = node_id
        return self.current

    def relabel(self, text: str, node_id: str | None = None) -> None:
        """Set the label of ``node_id`` (default: the current node) to ``text``."""
        self.nodes[node_id or self.current_id].label = text

    def to_dict(self) -> dict:
        """Serialize the whole graph to plain JSON-compatible data."""
        return {
            "nodes": {nid: asdict(node) for nid, node in self.nodes.items()},
            "root_id": self.root_id,
            "current_id": self.current_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ProvenanceGraph:
        """Reconstruct a graph from :meth:`to_dict` output."""
        tree = cls.__new__(cls)
        tree.nodes = {nid: Node(**nd) for nid, nd in data["nodes"].items()}
        tree.root_id = data["root_id"]
        tree.current_id = data["current_id"]
        return tree

    def save(self, path: str | os.PathLike[str]) -> None:
        """Write the serialized graph to ``path`` atomically."""
        write_json_atomic(path, self.to_dict())

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> ProvenanceGraph | None:
        """Load a graph from ``path``, or return ``None`` if it is absent."""
        data = read_json(path)
        if data is None:
            return None
        return cls.from_dict(data)

    @staticmethod
    def _auto_label(old: dict, new: dict) -> str:
        changes = []
        for key in sorted(set(old) | set(new)):
            before, after = old.get(key), new.get(key)
            if before != after:
                changes.append(f"{key}: {before} → {after}")
        return ", ".join(changes) if changes else "(no change)"
