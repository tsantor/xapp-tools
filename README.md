# Build/Development Scripts

![Coverage](https://img.shields.io/badge/coverage-83.76%25-green)

## Purpose

The `scripts/` directory contains reusable build and development tooling for Python projects.
Its role is to hold automation that is broadly useful across repositories, not app-specific behavior.

## Reuse Policy

Scripts in this directory should be written so they can be reused in other Python projects with little or no modification.
When project values are needed, prefer metadata/config introspection (for example from `pyproject.toml`) over hardcoded constants.

## Scope Boundaries

Only generic tooling belongs here.

Allowed examples:

- Dependency maintenance helpers
- Packaging/public API verification scripts
- Repository metadata utilities
- Generic release/build checks

Not allowed examples:

- Application/domain business logic
- Project feature commands (for example stock/portfolio behavior)
- One-off scripts tightly coupled to this app’s runtime behavior

## Tests for Scripts

Tests for tooling in this directory should live under `scripts/tests/`.
Keep these tests separate from app-level test suites so script behavior remains portable and easy to reuse across projects.
