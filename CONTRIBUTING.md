# Contributing to trrackpy

Thanks for contributing.

## Layout

trrackpy is a [uv](https://docs.astral.sh/uv/) workspace with two packages:

- `packages/trrack` is the core: the branching history model
  (`ProvenanceGraph`) and the `Store` protocol for saving it. Pure Python, no
  UI dependencies.
- `packages/trrack-widget` has the two [anywidget](https://anywidget.dev)
  wrappers: `Persisted` and `Trrackable`. It uses `trrack` from the local
  workspace, never the published package.
- `examples` has runnable marimo notebooks.

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

Some pages embed live notebooks from `docs/live`. They run in the browser on
wheels built from your checkout. Build them before you serve the site, and
again after a change to a package or a live notebook:

```sh
docs/live/build.sh
```

The `Docs` workflow publishes the site to GitHub Pages. Run it by hand from
the Actions tab. The release workflow also runs it as its last job. CI builds
the site on each pull request, and a broken link fails the build.

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
- Python is linted with ruff (`select = ["ALL"]`) and type-checked with `ty`.
  Both must stay clean.
- `from __future__ import annotations` is required at the top of every module.
- New files fall under the repository's BSD-3-Clause license.
- A change that a user can see gets a line under "Unreleased" in
  `CHANGELOG.md`.

## Where to add things

- A change to the model or its algorithms goes in `packages/trrack`.
- UI and widget wiring goes in `packages/trrack-widget`.
- A new store implements the `trrack.Store` protocol. See
  [Stores](https://kirangadhave.me/trrackpy/stores/).
- A new example notebook goes in `examples/persisted` or
  `examples/trrackable`.

## Releasing

Both packages release in lockstep. They always carry the same version, and one
tag publishes both. The version string in each `pyproject.toml` is static, so
you bump both.

A pre-release uses a [PEP 440](https://peps.python.org/pep-0440/) suffix:
`0.0.1a1`, `0.0.1b1`, or `0.0.1rc1`. `pip` and `uv` skip pre-releases unless
you ask for them:

- `pip install --pre`
- `uv pip install --prerelease=allow`

A pre-release claims the name and tests the pipeline. Users get it only when
they ask for a pre-release.

### How a release runs

`.github/workflows/release.yml` publishes the packages. It starts in two ways:

- A tag push (`vX.Y.Z` or `vX.Y.Za1`) publishes to PyPI.
- A manual dispatch with `target=testpypi` publishes to TestPyPI as a dry run.
  A dispatch with `target=pypi` publishes to real PyPI by hand.

The jobs run in this order:

1. Build both packages. The run fails if the two versions differ. It also
   fails if a tag does not match the package version.
2. Publish each package in its own job.
3. On a tag, draft a GitHub Release with the wheels and sdists attached.
4. On a tag, publish the docs site.

Publishing uses [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC), so the repository holds no API tokens.

Each publish job runs in its own GitHub Environment. PyPI needs each pending
publisher to have a distinct `(owner, repo, workflow, environment)` tuple. One
workflow that publishes two projects would break that rule without separate
environments.

| Index | trrack | trrack-widget | Approval gate |
| --- | --- | --- | --- |
| PyPI | `pypi` | `pypi-widget` | required reviewer |
| TestPyPI | `testpypi` | `testpypi-widget` | none, for fast dry runs |

### Cutting a release

1. Set `version` in both package `pyproject.toml` files to the same value.
2. Optional: do a dry run.
    1. Go to Actions, then Release, then Run workflow. Set `target=testpypi`.
    2. Check that both packages appear on test.pypi.org.
    3. Install the widget to check that it pulls the core:

       ```sh
       uv pip install --prerelease=allow \
         --index-url https://test.pypi.org/simple/ \
         --extra-index-url https://pypi.org/simple/ trrack-widget
       ```

       The extra index supplies `anywidget`, which TestPyPI does not have.
3. In `CHANGELOG.md`, rename "Unreleased" to the new version and its date. Add
   a new empty "Unreleased" section above it.
4. Tag the release and push the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`.
5. In the run, approve the `pypi` and `pypi-widget` deployments.
6. Review the drafted GitHub Release, then publish it.

### One-time setup

This repository already has the four GitHub Environments above. It also has a
pending or registered trusted publisher for each project on each index.
