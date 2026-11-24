"""The traits of a widget that a wrapper reads, sets, and observes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import anywidget
import traitlets

if TYPE_CHECKING:
    from collections.abc import Callable


def infer_traits(target: Any) -> list[str]:
    """List the traits that hold a widget's own state.

    Args:
        target (Any): The widget to inspect.

    Returns:
        list[str]: The synced traits of ``target``, leaving out private traits
        and the ones every anywidget has.
    """
    base = set(anywidget.AnyWidget.class_traits(sync=True))
    return [
        name
        for name in target.traits(sync=True)
        if name not in base and not name.startswith("_")
    ]


class TrackedValues:
    """The tracked traits of one widget.

    Args:
        target (Any): The widget that owns the traits.
        names (list[str], optional): Trait names to track. Defaults to the
            target's public synced traits.
    """

    def __init__(self, target: Any, names: list[str] | None = None) -> None:
        self._target = target
        self.names = list(names) if names is not None else infer_traits(target)

    def read(self) -> dict:
        """Return the current value of each tracked trait, keyed by name."""
        return {name: getattr(self._target, name) for name in self.names}

    def write(self, values: dict) -> list[str]:
        """Set each tracked trait that ``values`` has a value for.

        Args:
            values (dict): New values, keyed by trait name. Keys that are not
                tracked have no effect.

        Returns:
            list[str]: One message for each value that its trait rejected. The
            widget keeps its current value for those traits.
        """
        rejected = []
        for name in self.names:
            if name not in values:
                continue
            # A saved value can stop fitting its trait, for example after a
            # hand edit of the saved file.
            try:
                setattr(self._target, name, values[name])
            except traitlets.TraitError as error:
                rejected.append(str(error))
        return rejected

    def observe(self, callback: Callable[[dict], None]) -> None:
        """Call ``callback`` each time a tracked trait changes."""
        self._target.observe(callback, names=self.names)

    def unobserve(self, callback: Callable[[dict], None]) -> None:
        """Stop the calls that ``observe`` started."""
        self._target.unobserve(callback, names=self.names)
