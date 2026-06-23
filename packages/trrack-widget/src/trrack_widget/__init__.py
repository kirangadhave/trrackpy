"""anywidget time-travel controls powered by trrack.

Wrap any widget with :class:`Trrackable` to record, branch, and navigate its
state, with optional persistence.
"""

from __future__ import annotations

from importlib.metadata import version

from .widget import Trrackable

__all__ = ["Trrackable"]
__version__ = version("trrack-widget")
