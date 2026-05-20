# Copilot Instructions

## Scope of edits
For any code change request, edit ONLY files in `backend/services/` unless the
user explicitly names another path. Never modify:
- `.github/**`, `.vscode/**`, `scripts/**`, `*.sh`
- Any file you have not been explicitly asked to change

If you think another file needs editing, STOP and ask before proposing the edit.

## Implementation context
`backend/services/inventory_service.py` is a pure in-memory Python module
using a module-level `dict` (`_stock`). There is NO database, NO Postgres,
NO SQLAlchemy. Fixes must be pure Python (locks, atomic functions, asyncio
primitives). Do not propose SQL, `SELECT FOR UPDATE`, advisory locks,
deadlock retry on `40P01`, or any database-layer solution.

## Bug pattern
Concurrency bugs in this codebase are TOCTOU on `_stock`. The correct fix
is a single function that reads-checks-writes atomically while holding the
event loop (no `await` between check and write), or an `asyncio.Lock` around
the critical section.
