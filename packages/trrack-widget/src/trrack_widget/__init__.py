"""Save and track the state of anywidget widgets.

``Persisted`` saves a widget's state and restores it. ``Trrackable`` records
every change as a history with undo and redo. The store names from ``trrack``
are here too, so one import covers the common case.
"""

from __future__ import annotations

from importlib.metadata import version

from trrack import JsonFileStore, Store, from_state, to_state

from .persisted import Persisted
from .widget import Trrackable

__all__ = [
    "JsonFileStore",
    "Persisted",
    "Store",
    "Trrackable",
    "from_state",
    "to_state",
]
__version__ = version("trrack-widget")
