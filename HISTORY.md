# History

All notable changes to this project will be documented in this file. This project adheres to [Semantic Versioning](http://semver.org/).

## 0.4.0 (2026-04-20)

- `dist api-snapshot`: reads from source `__init__.py` directly (no wheel required); catches `__all__` changes immediately without rebuilding.
- `dist api-snapshot`: contract now includes both top-level package exports and per-submodule entries.
- `dist api-snapshot`: mismatch output now shows explicit added/removed symbols per module instead of raw JSON dumps.
- `dist verify`: fixed `_verify_contract` to fall back to `module/__init__.py` when `module.py` is not found in the wheel.

## 0.3.1 (2026-04-20)

- Fixed the `hatch` combined-readme plugin hook.

## 0.3.0 (2026-04-17)

- Added `version` subgroup: `show`, `set`, `bump`, `check-source`.
- Added `tag` subgroup: `dryrun`, `create`, `push`.
- Added `dist` subgroup: `verify`, `wheel-smoke`, `api-snapshot`.
- Reorganized CLI into Click subgroups for a cleaner, grouped help interface.

## 0.2.0 (2026-04-17)

- Added a `hatch` readme hook to combine `README` and `HISTORY` on build.

## 0.1.0 (2026-04-16)

- First release
