# ui/generation/_internal/AGENTS.md

**Scope**: `ui/generation/_internal/` - generation UI components  
**Generated**: 2026-04-01

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Controls | `controls.py` - main control panel |
| Basic params | `basic_params.py` - model, prompt inputs |
| Advanced params | `advanced_params.py` - aspect ratio, count |
| Output | `output.py` - result display |
| Presenter | `presenter.py` - view model mapping |
| View model | `view_model.py` - UI state structures |
| Status | `status_formatter.py` - status text |
| Handlers | `handlers.py` - event handlers |
| Components | `components.py`, `component_base.py` - reusable |
| Log | `log_renderer.py` - execution log |

## CONVENTIONS
- Components inherit from `component_base.py`
- Presenter maps core → view model
- Handlers thin, delegate to core.api
- Slider adapter for Gradio quirks

## ANTI-PATTERNS
- Business logic in handlers → Move to core
- Direct store access → Use presenter
- Gradio leaks outside components → Abstract in component_base