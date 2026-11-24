"""Saving and loading provenance payloads.

A store is any object with ``save(dict)`` and ``load() -> dict | None``, so it
can keep the payload anywhere: a file, a database, a URL. ``JsonFileStore``
keeps it in a JSON file.

Saved payloads are tagged, ``{"type": ..., "value": ...}``, so a reader knows
what it loaded:

- ``"graph"``: a serialized ``ProvenanceGraph``.
- ``"state"``: the current tracked values, keyed by name.

A payload with no ``type`` key but with a ``tree`` is read as a graph.

A store that saves the payload whole never looks inside it. A store that keeps
plain values in its own shape uses ``to_state`` and ``from_state``.

Each save writes the whole graph, so its cost grows with the number of nodes
and the size of each snapshot.
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
        value (dict): The serialized graph.

    Returns:
        dict: The payload ``{"type": "graph", "value": value}``.
    """
    return {"type": _GRAPH, "value": value}


def from_state(state: dict) -> dict:
    """Turn plain tracked values into a payload a store can return.

    Use it in a store's ``load`` when the store keeps the values in its own
    shape.

    Args:
        state (dict): The tracked values, keyed by name.

    Returns:
        dict: The payload to return from ``load``.

    Examples:
        ```python
        def load(self) -> dict | None:
            state = self._read_values()
            return from_state(state) if state else None
        ```
    """
    return {"type": _STATE, "value": state}


def to_state(payload: dict) -> dict:
    """Get the plain tracked values out of a saved payload.

    Use it in a store's ``save`` when the store keeps the values in its own
    shape, such as one URL parameter per value.

    Args:
        payload (dict): The payload passed to ``save``.

    Returns:
        dict: The tracked values, keyed by name.

    Raises:
        ValueError: If the payload is a ``Trrackable`` graph, which does not
            fit a store of plain values.

    Examples:
        ```python
        def save(self, data: dict) -> None:
            for name, value in to_state(data).items():
                self._write_value(name, value)
        ```
    """
    kind, value = read_envelope(payload)
    if kind != _STATE:
        msg = (
            "This payload is a Trrackable graph, not plain state. Save it "
            "whole, or use this store with Persisted."
        )
        raise ValueError(msg)
    return value


def read_envelope(data: dict) -> tuple[str, dict]:
    """Return the type and the value of a saved payload.

    Args:
        data (dict): A payload that a store loaded.

    Returns:
        tuple[str, dict]: ``("graph", value)`` or ``("state", value)``. A
        payload with no ``type`` key but with a ``tree`` is a graph, and its
        value is ``data``.

    Raises:
        ValueError: If the payload is not one of those shapes.

    Examples:
        ```python
        kind, value = read_envelope(store.load())
        if kind == "state":
            apply_values(value)
        ```
    """
    if "type" not in data:
        if "tree" not in data:
            msg = "Unrecognized saved payload. It has no 'type' key."
            raise ValueError(msg)
        return _GRAPH, data
    kind, value = data["type"], data.get("value")
    if kind not in (_GRAPH, _STATE) or not isinstance(value, dict):
        msg = (
            f"Unrecognized saved payload of type {kind!r}. Expected "
            f'"{_GRAPH}" or "{_STATE}", with a dict as its value.'
        )
        raise ValueError(msg)
    return kind, value


@runtime_checkable
class Store(Protocol):
    """A place to keep a saved payload."""

    def save(self, data: dict) -> None:
        """Save ``data``, replacing what was saved before."""
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
        """Save to and load from the JSON file at ``path``.

        Args:
            path (str | os.PathLike[str]): The path of the file. Missing
                parent folders are created on the first save.
        """
        self._path = path

    def save(self, data: dict) -> None:
        """Write ``data`` to the file, atomically replacing prior contents."""
        write_json_atomic(self._path, data)

    def load(self) -> dict | None:
        """Return the file's parsed payload, or ``None`` if it is absent."""
        return read_json(self._path)
