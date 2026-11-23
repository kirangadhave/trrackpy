"""JSON persistence for provenance payloads.

A ``Store`` is the single extension seam: anything with ``save(dict)`` and
``load() -> dict | None`` can back persistence, so a future backend (a database,
browser storage, a remote service) is a drop-in without a plugin registry.
``JsonFileStore`` is the only implementation today.

Each saved payload is an envelope ``{"type": ..., "value": ...}``. The ``type``
tells a reader which of the two shapes ``value`` has:

- ``"graph"``: a serialized ``ProvenanceGraph`` with its full history.
- ``"state"``: one snapshot of the tracked values, without history.

A payload without a ``type`` key is a bare graph. ``read_envelope`` reads that
payload as a graph, so a file that has no envelope stays loadable.

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

_GRAPH = "graph"
_STATE = "state"


def graph_envelope(value: dict) -> dict:
    """Wrap a serialized provenance graph in an envelope.

    Args:
        value (dict): The serialized graph, with its full history.

    Returns:
        dict: The payload ``{"type": "graph", "value": value}``.
    """
    return {"type": _GRAPH, "value": value}


def state_envelope(value: dict) -> dict:
    """Wrap one snapshot of tracked values in an envelope.

    Args:
        value (dict): The tracked values, keyed by name, without history.

    Returns:
        dict: The payload ``{"type": "state", "value": value}``.
    """
    return {"type": _STATE, "value": value}


def read_envelope(data: dict) -> tuple[str, dict]:
    """Return the type and the value of a saved payload.

    Args:
        data (dict): A payload that a ``Store`` loaded. A payload without a
            ``type`` key is a bare graph.

    Returns:
        tuple[str, dict]: ``("graph", value)`` or ``("state", value)``. For a
        payload without a ``type`` key, the value is ``data``.

    Raises:
        ValueError: If ``type`` is not ``"graph"`` or ``"state"``.

    ```python
    kind, value = read_envelope(store.load())
    if kind == "state":
        apply_values(value)
    ```
    """
    if "type" not in data:
        return _GRAPH, data
    kind = data["type"]
    if kind not in (_GRAPH, _STATE):
        msg = f'Unknown payload type {kind!r}. Use "{_GRAPH}" or "{_STATE}".'
        raise ValueError(msg)
    return kind, data["value"]


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
