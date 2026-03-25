# core/ARCHITECTURE.md

## 角色
- domain
- service
- runtime orchestration
- validation
- task queue
- provider execution
- artifact ownership

## 上游调用
- `ui.app.build_app` → `core.api.get_ui_context`
- `ui._app_generation.prepare_reference_preview`
  → `core.api.prepare_reference_image`
- `ui.generation._internal.handlers.GenerateHandler.handle_generate`
  → `core.api.submit_generation_task`
- `ui.dashboard._internal.handler.TaskDashboardHandler`
  → `core.api.list_tasks`
- `ui.dashboard._internal.handler.TaskDashboardHandler`
  → `core.api.get_task_metrics`

## 数据入口
- `UIContext` request: app init
- preview input: `{path, divisible_by, aspect_ratio}`
- task input: `TaskConfig`
- browser query: `[task_ids]`
- metrics query: `[]`
- token input: `TaskConfig.ui_token_override`

## 数据处理流
- ui context:
  `core.api.get_ui_context`
  → runtime
  → `build_ui_context`
  → `UIContext`
- preview:
  `{path, divisible_by, aspect_ratio}`
  → facade validate
  → `ImageGenerationService.prepare_reference_image`
  → `ReferenceImagePreparer.prepare`
  → `PreparedReferenceImage`
- submit:
  `TaskConfig`
  → facade validate
  → artifact stage
  → `store.create_task`
  → runtime queue
- execute:
  runtime worker
  → `ImageGenerationService.generate`
  → normalize/validate
  → `ProviderGateway.build_provider_request`
  → `get_or_create_provider`
  → `provider.generate`
- finish:
  artifact materialize
  → `store.finish_success/failure/timeout`
  → `TaskSnapshot`
- query:
  `list_tasks/get_task_metrics`
  → `TaskSnapshot/metrics`
  → UI

## 反向耦合
- no explicit `core -> ui` import
- no `from ui`
- no `import ui`
- `core.api` is UI-facing facade
- `core.schemas.ui` is UI-shaped
- validation rebuilds `UIContext`
- `BrowserTaskState` is core-owned UI state

## 风险
- UI concepts inside core schemas
- `UIContext` couples config to UI shape
- `BrowserTaskState` weakens boundary
- `ui_token_override` leaks auth policy upward
- `prepared_reference_image_path` leaks staging detail
- task artifacts couple runtime to FS
- result paths are presentation-aware
- thin facade exposes schema churn to UI
