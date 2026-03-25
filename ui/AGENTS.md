# ui/AGENTS.md

- Scope: `ui/`
- Role: view + orchestration
- Prefer read [ARCHITECTURE.md](/Users/shenyeke01/Documents/Workspace/sinyuk-imagen/ui/ARCHITECTURE.md)
- Keep UI logic thin
- Do not add provider logic here
- Do not bypass `core.api`
- Prefer `core.schemas` contracts
- Keep events explicit
- Keep state local
- Avoid hidden FS side effects
