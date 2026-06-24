# trrackpy

[![CI](https://github.com/kirangadhave/trrackpy/actions/workflows/ci.yml/badge.svg)](https://github.com/kirangadhave/trrackpy/actions/workflows/ci.yml)
[![PyPI - trrack](https://img.shields.io/pypi/v/trrack?label=trrack)](https://pypi.org/project/trrack/)
[![PyPI - trrack-widget](https://img.shields.io/pypi/v/trrack-widget?label=trrack-widget)](https://pypi.org/project/trrack-widget/)

Branching, tree-based provenance tracking for Python.

Record state as a branching graph of snapshots you can navigate — undo, redo,
jump to any node, or branch off an earlier state. Use the pure core on its own,
or the widget to give any [anywidget](https://anywidget.dev) (in
[marimo](https://marimo.io) or Jupyter) a full history with navigation controls.

## Packages

| Package | What | Docs |
| --- | --- | --- |
| [`trrack`](https://pypi.org/project/trrack/) | The core branching provenance model. Pure Python, no UI dependencies. | [packages/trrack](packages/trrack/README.md) |
| [`trrack-widget`](https://pypi.org/project/trrack-widget/) | An anywidget (`Trrackable`) that adds provenance controls to any widget. | [packages/trrack-widget](packages/trrack-widget/README.md) |

## Contributing

This is a [uv](https://docs.astral.sh/uv/) workspace. See
[CONTRIBUTING.md](CONTRIBUTING.md) for setup, the dev loop, and the release
flow; agents, see [AGENTS.md](AGENTS.md).

## License

BSD-3-Clause. trrackpy is a Python sibling of
[trrackjs](https://github.com/Trrack/trrackjs), bringing the same provenance
model to the Python ecosystem.
