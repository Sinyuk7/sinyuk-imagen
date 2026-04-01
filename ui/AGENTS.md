# ui/AGENTS.md

**Scope**: `ui/` - view + orchestration  
**Generated**: 2026-04-01

## WHERE TO LOOK
| Task | Location |
|------|----------|
| App entry | `app.py` - Gradio app init |
| Dashboard | `dashboard/_internal/` - task list, metrics |
| Generation UI | `generation/_internal/` - controls, presenter |
| Layout | `layout/_internal/` - shared components |
| Events | `events.py` - event bus |

## STRUCTURE
```
ui/
├── app.py              # Main Gradio application
├── _app_*.py           # App page modules
├── dashboard/          # Task dashboard
│   └── _internal/      # handlers, presenters, view models
├── generation/         # Generation controls
│   └── _internal/      # params, controls, output, status
├── layout/             # Shared UI components
│   └── _internal/      # component library
└── events.py           # Event system
```

## CONVENTIONS
- UI logic thin, delegate to core
- `_internal/` = internal helpers
- `_app_*.py` pattern for page modules
- Always use `core.api` facade
- Events explicit, typed

## ANTI-PATTERNS
- Provider logic in UI → Move to core/
- Bypass core.api → Always use facade
- Direct FS access → Use core abstractions
- Hidden state → Explicit state_machine usage
