# core/AGENTS.md

- Scope: `core/`
- Role: domain + service + runtime
- Prefer read [ARCHITECTURE.md](/Users/shenyeke01/Documents/Workspace/sinyuk-imagen/core/ARCHITECTURE.md)
- No `core -> ui` imports
- Keep UI concerns at facade edge
- Keep side effects explicit
- Keep schemas stable
- Avoid leaking FS details upward
- Prefer pure transforms inside internals
- Keep tasking and generation boundaries clear
