# Contributing to trrackpy

Thanks for contributing. This guide gets you from a fresh clone to a green pull
request.

## Layout

trrackpy is a [uv](https://docs.astral.sh/uv/) workspace with two packages:

- `packages/trrack` is the core: the branching history model
  (`ProvenanceGraph`) and the `Store` protocol for saving it. Pure Python, no
  UI dependencies.
- `packages/trrack-widget` has the two [anywidget](https://anywidget.dev)
  wrappers: `Persisted` and `Trrackable`. It uses `trrack` from the local
  workspace, never the published package.
- `examples` has runnable marimo notebooks.

The core works on its own, to track the history of anything. The widgets are
one use of it.

## Setup

The frontend bundles in `src/trrack_widget/static/` are gitignored build
output. Build them before `uv sync`, so the editable install includes them:

```sh
cd packages/trrack-widget
pnpm install
pnpm run build
cd ../..
uv sync
```

## Frontend dev loop

The frontend is TypeScript in `packages/trrack-widget/js`, bundled by esbuild:

- `controls.tsx`: the history controls for `Trrackable` (Preact).
- `persisted.ts`: the view for `Persisted`.
- `compose.ts`: what both share. It shows the wrapped widget and the error
  line.

Rebuild on every save with:

```sh
cd packages/trrack-widget
pnpm run dev
```

With `ANYWIDGET_HMR=1 uv run marimo edit examples/trrackable/files.py`, the
rebuilt bundle loads into the open notebook without a kernel restart.

## Docs

The site is built with [Zensical](https://zensical.org) from `docs/pages` and
`mkdocs.yml`. The API reference comes from the docstrings.

```sh
uv run --group docs zensical serve    # preview with live reload
uv run --group docs zensical build    # write the site to ./site
```

The `Docs` workflow publishes the site to GitHub Pages. Run it by hand from
the Actions tab. The release workflow also runs it as its last job.

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
- A new store is a class with `save(dict) -> None` and
  `load() -> dict | None`. See the `trrack.Store` protocol.
- A new example notebook goes in `examples/persisted` or
  `examples/trrackable`.

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
