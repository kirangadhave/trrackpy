"""Branching tree-based provenance tracking for Python.

Pure model with no UI dependencies: a :class:`ProvenanceGraph` of full-state
snapshots, plus an optional :class:`Store` seam for persistence.
"""

from __future__ import annotations

from importlib.metadata import version

from .graph import Node, ProvenanceGraph
from .persist import JsonFileStore, Store

__all__ = ["JsonFileStore", "Node", "ProvenanceGraph", "Store"]
__version__ = version("trrack")
