# core/generation/_internal/AGENTS.md

**Scope**: `core/generation/_internal/` - generation orchestration internals  
**Generated**: 2026-04-01

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Gateway | `provider_gateway.py` - main entry |
| Registry | `provider_registry.py` - provider discovery |
| Base class | `provider_base.py` - abstract provider |
| Google | `providers/google/` - Google Imagen provider |
| Resolution | `_provider_resolution.py` - provider selection |
| Materialization | `_provider_materialization.py` - provider init |
| Diagnostics | `_provider_diagnostics.py` - health checks |
| Config | `task_config.py` - generation settings |
| Reference | `reference_images.py` - image upload handling |

## STRUCTURE
```
generation/_internal/
├── provider_gateway.py           # Public interface
├── provider_registry.py          # Provider discovery
├── provider_base.py              # Abstract base
├── task_config.py                # Config structures
├── _provider_*.py                # Internal resolution
└── providers/
    └── google/                   # Google Imagen
        ├── provider.py           # Implementation
        ├── _client.py            # API client
        ├── _request_builder.py   # Request construction
        ├── _response_parser.py   # Response handling
        └── diagnostics.py        # Health checks
```

## CONVENTIONS
- Gateway = single entry point
- Providers implement `provider_base.py`
- Private helpers prefixed with `_`
- Diagnostics separate from runtime

## ANTI-PATTERNS
- Direct provider instantiation → Use gateway
- Provider-specific code outside providers/ → Keep isolated
- Leaking HTTP details → Abstract in _client.py