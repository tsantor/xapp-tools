# xapp-tools

![Coverage](https://img.shields.io/badge/coverage-66.43%25-yellow)

## Purpose

`xapp-tools` is an installable package of reusable build and development tooling for Xapp-based Python projects.
Its role is to provide automation that is broadly useful across repositories, not app-specific behavior.

## Usage

```bash
uv add xapp-tools --dev
xapp-tools --help
```

Available commands:

**`version`** — Version management

- `xapp-tools version show` — print the current version from `pyproject.toml`
- `xapp-tools version set X.Y.Z` — set an explicit version (strict SemVer)
- `xapp-tools version bump [patch|minor|major]` — bump the version
- `xapp-tools version check-source` — ensure no hardcoded `__version__` in source

**`tag`** — Git tag management

- `xapp-tools tag dryrun` — print the tag without creating it
- `xapp-tools tag create` — create an annotated local git tag
- `xapp-tools tag push` — push the tag to origin

**`dist`** — Distribution artifacts

- `xapp-tools dist verify` — verify wheel and sdist build artifacts
- `xapp-tools dist wheel-smoke` — smoke-test the installed wheel in a clean venv
- `xapp-tools dist api-snapshot` — capture or verify the public API contract

**Top-level**

- `xapp-tools coverage-badge` — update the coverage badge in README
- `xapp-tools update-deps` — refresh all dependencies to latest versions via `uv`

## Reuse Policy

Tools in this package should be written so they can be reused in other Python projects with little or no modification.
When project values are needed, prefer metadata/config introspection (for example from `pyproject.toml`) over hardcoded constants.

## Scope Boundaries

Only generic tooling belongs in this package.

Allowed examples:

- Dependency maintenance helpers
- Packaging/public API verification scripts
- Repository metadata utilities
- Generic release/build checks

Not allowed examples:

- Application/domain business logic
- Project feature commands
- One-off scripts tightly coupled to a specific app's runtime behavior

##

This packages offers a `hatch` hook that combines the `README` with the `HISTORY`.

In the package which implements `xapp-tools` add the follwoing the `pyproject.toml`:

```toml
requires = ["hatchling", "xapp-tools"]
build-backend = "hatchling.build"

[tool.hatch.metadata.hooks.combined-readme]
```

Or simply use ``hatch-fancy-pypi-readme`.
