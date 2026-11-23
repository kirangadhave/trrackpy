"""Branching history for Python state.

``ProvenanceGraph`` keeps every state as a node in a tree. A ``Store`` saves a
payload somewhere, such as a file. Pure Python, with no UI dependencies.
"""

from __future__ import annotations

from importlib.metadata import version

from .graph import Node, ProvenanceGraph
from .persist import JsonFileStore, Store, from_state, to_state

__all__ = [
    "JsonFileStore",
    "Node",
    "ProvenanceGraph",
    "Store",
    "from_state",
    "to_state",
]
__version__ = version("trrack")
