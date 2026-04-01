# tests/AGENTS.md

**Scope**: `tests/` - test suite  
**Generated**: 2026-04-01

## WHERE TO LOOK
| Task | Location |
|------|----------|
| Fixtures | `conftest.py` - shared pytest fixtures |
| Dashboard | `test_task_dashboard_*.py` - UI tests |
| Tasking | `test_task_store_*.py` - store tests |
| Output | `test_output_presenter.py` - presenter tests |
| Imports | `test_imports.py`, `test_no_circular.py` - structure |

## CONVENTIONS
- Pytest default
- Fixtures in conftest.py
- Test file: `test_*.py`
- Use pytest fixtures for mocking

## COMMANDS
```bash
pytest                    # Run all tests
pytest -x                 # Stop on first fail
pytest tests/test_*.py    # Specific test file
```