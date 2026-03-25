# ui/ARCHITECTURE.md

## 角色
- view
- orchestration
- collect inputs
- bind events
- build `TaskConfig`
- render `TaskSnapshot` / `GenerationResult`
- own `StateMachine`

## 下游依赖
- `core.api`
- `core._api_ui_context`
- `core.schemas.UIContext`
- `core.schemas.ProviderUIContext`
- `core.schemas.TaskConfig`
- `core.schemas.BrowserTaskState`
- `core.schemas.TaskSnapshot`
- `core.schemas.TaskManagerMetricsSnapshot`
- `core.schemas.GenerationResult`
- `core.schemas.TaskErrorCode`

## 数据流
- init:
  `ui.app.build_app`
  → `core.api.get_ui_context`
  → `core._api_ui_context.build_ui_context`
  → `BasicParamsPanel` / handlers
- preview:
  `input.change`
  → `prepare_reference_preview`
  → `core.api.prepare_reference_image`
  → `ImageGenerationService.prepare_reference_image`
  → `ReferenceImagePreparer.prepare`
  → slider render
- submit:
  `click`
  → `GenerateHandler.handle_generate`
  → `TaskConfig`
  → `core.api.submit_generation_task`
  → `TaskManager.submit`
  → `TaskRuntime.enqueue_task`
- refresh:
  `load/tick/change`
  → `TaskDashboardHandler`
  → `core.api.list_tasks/get_task_metrics`
  → `TaskDashboardPresenter`
  → `OutputPresenter`
  → render
- provider switch:
  `Dropdown.change`
  → `ProviderHandler`
  → `UIContext.providers`
  → `gr.update`
- browser state:
  `BrowserState/State`
  → `BrowserTaskState.from_value`
  → `list_tasks`
  → `BrowserTaskState.to_value`

## 耦合点
- direct: import `core.api`
- direct: import `core.schemas.*`
- direct: `UIContext` drives control options
- direct: `TaskSnapshot` drives render states
- indirect: via `DashboardHandlerPort`
- indirect: app shell wires generation ↔ dashboard
- implicit: `BrowserTaskState` dict shape
- implicit: `TaskConfig.ui_token_override`
- implicit: `prepared_reference_image_path`
- implicit: temp file lifecycle
- implicit: aspect_ratio flip semantics

## 风险
- `core.schemas.ui` is UI-shaped
- `BrowserTaskState` lives in core
- UI reads many core contracts
- facade is thin; schema leak remains
- preview path leaks FS concerns
- token override crosses layer boundary
- slider temp cleanup mixes UI + FS
- dashboard render depends on core status model
