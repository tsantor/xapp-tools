# xapp-tools

![Coverage](https://img.shields.io/badge/coverage-83.76%25-green)

## Purpose

`xapp-tools` is an installable package of reusable build and development tooling for Python projects.
Its role is to provide automation that is broadly useful across repositories, not app-specific behavior.

## Usage

```
uv add xapp-tools --dev
xapp-tools --help
```

Available commands:

- `api-snapshot` — capture a public API snapshot
- `check-version-source` — ensure no hardcoded `__version__` in package source
- `coverage-badge` — update the coverage badge in README
- `update-deps` — refresh all dependencies to their latest versions via uv
- `verify-dist` — verify wheel and sdist build artifacts
- `wheel-smoke` — smoke-test an installed wheel

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
- Project feature commands (for example stock/portfolio behavior)
- One-off scripts tightly coupled to a specific app's runtime behavior

## Tests

Tests live under `tests/`.
Keep these tests separate from app-level test suites so tool behavior remains portable and easy to reuse across projects.
