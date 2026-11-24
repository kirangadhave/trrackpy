from __future__ import annotations

import anywidget
import traitlets

from trrack_widget._tracked import TrackedValues


class Point(anywidget.AnyWidget):
    _esm = "export default { render() {} };"
    x = traitlets.Int(0).tag(sync=True)
    y = traitlets.Int(0).tag(sync=True)
    _private = traitlets.Int(0).tag(sync=True)
    local = traitlets.Int(0)


def test_names_default_to_the_public_synced_traits():
    assert sorted(TrackedValues(Point()).names) == ["x", "y"]


def test_read_returns_the_named_traits_only():
    point = Point(x=1, y=2)

    assert TrackedValues(point, ["x"]).read() == {"x": 1}


def test_write_sets_tracked_traits_and_skips_other_keys():
    point = Point()

    rejected = TrackedValues(point, ["x"]).write({"x": 5, "y": 9})

    assert rejected == []
    assert (point.x, point.y) == (5, 0)


def test_write_keeps_the_current_value_for_a_rejected_value():
    point = Point(x=1)

    rejected = TrackedValues(point).write({"x": "abc", "y": 4})

    assert len(rejected) == 1
    assert "x" in rejected[0]
    assert (point.x, point.y) == (1, 4)


def test_observe_reports_tracked_changes_until_unobserve():
    point = Point()
    values = TrackedValues(point, ["x"])
    seen = []

    def record(change: dict) -> None:
        seen.append(change["name"])

    values.observe(record)
    point.x = 1
    point.y = 1
    values.unobserve(record)
    point.x = 2

    assert seen == ["x"]
