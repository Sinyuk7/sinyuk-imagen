# core/AGENTS.md

**Scope**: `core/` - domain + service + runtime  
**Generated**: 2026-04-01

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Entry point | `api.py` - public facade |
| Tasking logic | `tasking/_internal/` - store, lifecycle, runtime |
| Generation | `generation/_internal/` - providers, gateway |
| Contracts | `schemas/` - stable data structures |
| Config | `config/` - settings management |

## STRUCTURE
```
core/
├── api.py              # Public API facade
├── tasking/            # Task lifecycle management
│   └── _internal/      # store, runtime, policies
├── generation/         # Generation orchestration
│   └── _internal/      # provider base, gateway, registry
├── schemas/            # Data contracts
├── config/             # Configuration
└── utils/              # Cross-cutting utilities
```

## CONVENTIONS
- No `core -> ui` imports (enforced)
- `_internal/` = private implementation detail
- Facade at edge (`api.py`, `_api_*.py`)
- Pure transforms inside `_internal`
- Schemas immutable, versioned

## ANTI-PATTERNS
- Leaking FS details upward → Use schemas only
- UI logic in core → Move to ui/
- Direct provider imports → Use gateway only
- Hidden state in transforms → Explicit params only
