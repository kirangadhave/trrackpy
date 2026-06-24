# Contributing to trrackpy

Thanks for contributing. This guide gets you from a fresh clone to a green pull
request.

## Layout

trrackpy is a [uv](https://docs.astral.sh/uv/) workspace with two packages:

- `packages/trrack` — the **core**: a pure-Python branching provenance model
  (`ProvenanceGraph`) plus a `Store` persistence seam. Zero UI dependencies.
- `packages/trrack-widget` — the **widget**: an [anywidget](https://anywidget.dev)
  that wraps any widget with time-travel controls (`Trrackable`). It depends on
  `trrack` through the local workspace source, never the published package.

The split is deliberate: the core can be used on its own to track the history of
anything, and the widget is just one consumer of it.

## Setup

The frontend bundle (`src/trrack_widget/static/controls.js`) is a gitignored
build artifact. Build it **before** `uv sync` so the editable install can ship
it:

```sh
cd packages/trrack-widget
pnpm install
pnpm run build
cd ../..
uv sync
```

## Frontend dev loop

The controls UI is a React + TypeScript component in
`packages/trrack-widget/js/controls.tsx`, bundled by esbuild. Rebuild on every
save with:

```sh
cd packages/trrack-widget
pnpm run dev
```

With `ANYWIDGET_HMR=1 uv run marimo edit trrack-widget-demo.py` the rebuilt
bundle hot-swaps into active cells without a kernel restart.

## Checks before a PR

Run the full gate, or let pre-commit do it for you:

```sh
uv run pytest
uv run ruff check
uv run ruff format --check
uv run ty check
cd packages/trrack-widget && pnpm run lint && pnpm run typecheck && cd ../..
```

```sh
uvx pre-commit run --all-files
```

## Conventions

- [Conventional commits](https://www.conventionalcommits.org/): `feat:`, `fix:`,
  `chore:`, `docs:`, `refactor:`, `test:`.
- Python is linted with ruff (`select = ["ALL"]`) and type-checked with `ty`;
  both must stay clean. `from __future__ import annotations` is required at the
  top of every module.
- New files fall under the repository's BSD-3-Clause license.

## Where to add things

- A change to the model or its algorithms goes in `packages/trrack`.
- UI and widget wiring goes in `packages/trrack-widget`.
- A new persistence backend implements the `trrack.Store` protocol
  (`save(dict) -> None`, `load() -> dict | None`) — no registry or plugin
  machinery to touch.

## Releasing

Both packages release **in lockstep**: they always carry the same version and
are published together by one tag. The version string in each
`pyproject.toml` is static — bump both.

Pre-releases use [PEP 440](https://peps.python.org/pep-0440/) suffixes
(`0.0.1a1`, `0.0.1b1`, `0.0.1rc1`). `pip`/`uv` ignore pre-releases unless asked
(`pip install --pre`, `uv pip install --prerelease=allow`), so a pre-release
claims the name and exercises the pipeline without reaching general users.

### How a release runs

`.github/workflows/release.yml` does the publishing. It triggers two ways:

- **Tag push** (`vX.Y.Z` / `vX.Y.Za1`) → publishes to **PyPI**.
- **Manual dispatch** with `target=testpypi` → publishes to **TestPyPI** (a dry
  run); `target=pypi` is the manual escape hatch to real PyPI.

The job order is: build both packages (a guard fails the run if the two
versions differ, or if a tag's version doesn't match) → one publish job per
package → on a tag, a **draft** GitHub Release with the wheels/sdists attached.

Publishing uses [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC) — no API tokens. Each publish job runs in its own GitHub Environment so
the two pending publishers have distinct `(owner, repo, workflow, environment)`
tuples; PyPI requires that uniqueness, which a monorepo publishing two projects
from one workflow would otherwise violate. The environments:

| Index | trrack | trrack-widget | Approval gate |
| --- | --- | --- | --- |
| PyPI | `pypi` | `pypi-widget` | required reviewer |
| TestPyPI | `testpypi` | `testpypi-widget` | none (fast dry runs) |

### Cutting a release

1. Bump the `version` in **both** package `pyproject.toml`s to the same value.
2. (Optional) Dry run: Actions → Release → Run workflow → `target=testpypi`, then
   verify both appear on test.pypi.org. Installing the widget pulls the core:
   `uv pip install --prerelease=allow --index-url https://test.pypi.org/simple/
   --extra-index-url https://pypi.org/simple/ trrack-widget` (the extra index
   supplies `anywidget`, which is not on TestPyPI).
3. Tag and push: `git tag vX.Y.Z && git push origin vX.Y.Z`.
4. Approve the `pypi` and `pypi-widget` deployments in the run.
5. Review and publish the drafted GitHub Release.

One-time infrastructure (already configured for this repo): the four GitHub
Environments above, and a pending/registered trusted publisher per project on
each index.
