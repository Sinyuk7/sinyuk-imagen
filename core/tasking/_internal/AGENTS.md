# core/tasking/_internal/AGENTS.md

**Scope**: `core/tasking/_internal/` - task storage & lifecycle internals  
**Generated**: 2026-04-01

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Store | `store.py` - main task store |
| Lifecycle | `store_lifecycle.py` - create/complete/cancel |
| Queries | `store_queries.py` - read operations |
| Runtime | `runtime.py` - task execution runtime |
| Records | `record.py` - task data structures |
| Policies | `policies.py` - retry, terminal rules |
| Artifacts | `artifacts.py` - output handling |

## CONVENTIONS
- Store operations atomic
- Exceptions in `exceptions.py`
- Support functions in `store_support.py`
- Terminal states handled in `store_terminal.py`

## ANTI-PATTERNS
- Direct store mutation → Use lifecycle methods only
- Exceptions not in exceptions.py → Centralize error types
- FS leaks → Keep in artifacts.py only