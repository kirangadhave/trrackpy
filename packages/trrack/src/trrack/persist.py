"""JSON persistence for a full-snapshot ProvenanceGraph.

A ``Store`` is the single extension seam: anything with ``save(dict)`` and
``load() -> dict | None`` can back persistence, so a future backend (a database,
browser storage, a remote service) is a drop-in without a plugin registry.
``JsonFileStore`` is the only implementation today.

v1 serializes the entire graph on every save: cost is O(total nodes x snapshot
size). That is imperceptible at interactive scale (tens-hundreds of small-state
nodes) and only matters with very large graphs or large per-node state. The
scaling answer, when needed, is a diff-node model -- store patches between nodes
with periodic full-state checkpoints, so per-save cost tracks changed state
rather than total state. Out of scope here; tracked as a future option.
"""

from __future__ import annotations

import json
import pathlib
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import os


@runtime_checkable
class Store(Protocol):
    """A persistence backend for a serialized provenance payload."""

    def save(self, data: dict) -> None:
        """Persist ``data``, replacing any previously saved payload."""
        ...

    def load(self) -> dict | None:
        """Return the saved payload, or ``None`` if nothing is stored."""
        ...


def write_json_atomic(path: str | os.PathLike[str], data: dict) -> None:
    """Write ``data`` as JSON, replacing ``path`` atomically.

    The write goes to a sibling temp file first and is then moved into place
    with ``Path.replace`` so a crash mid-write can never leave a half-written,
    unparsable file at ``path``.
    """
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


def read_json(path: str | os.PathLike[str]) -> dict | None:
    """Return the parsed JSON at ``path``, or ``None`` if it does not exist."""
    path = pathlib.Path(path)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


class JsonFileStore:
    """A ``Store`` that round-trips the payload through one JSON file."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        """Back persistence with the JSON file at ``path``."""
        self._path = path

    def save(self, data: dict) -> None:
        """Write ``data`` to the file, atomically replacing prior contents."""
        write_json_atomic(self._path, data)

    def load(self) -> dict | None:
        """Return the file's parsed payload, or ``None`` if it is absent."""
        return read_json(self._path)
