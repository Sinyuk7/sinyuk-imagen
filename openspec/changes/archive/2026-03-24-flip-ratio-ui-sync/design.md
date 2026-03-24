# 总体设计与需求 (Design)

## 1. 背景与目标 (Context & Goals)

### Why
- **UI 显示与实际值不一致**：当用户选中 "Swap Width/Height" (`flip_checked`) 后，下拉菜单仍显示原始值（如 `2:3`），但实际传递给生成器的是翻转后的值（`3:2`），造成用户困惑
- **Provider 切换逻辑不完整**：切换 Provider 时，`aspect_ratio` 下拉菜单会重置为新 Provider 的默认选项，但没有考虑当前的 `flip_checked` 状态

### Goals
- 当 `flip_checked` 改变时，同步更新 `aspect_ratio` 下拉菜单的 **choices** 和 **value**（如 `2:3` → `3:2`）
- 当 Provider 切换时，根据当前 `flip_checked` 状态正确设置 `aspect_ratio` 的选项

---

## 2. 范围与变更内容 (Scope & Changes)

### In Scope
- 新增 `FlipRatioHandler` 处理 flip_ratio 切换事件
- 修改 `ProviderHandler.handle_provider_change` 以接收 `flip_checked` 参数
- 新增 `FlipRatioResponse` 数据结构
- 绑定 `flip_ratio` 组件的 change 事件以更新 `aspect_ratio` 下拉菜单

### Out of Scope / Non-Goals
- 不修改 core 层的 aspect_ratio 处理逻辑
- 不改变 `get_effective_aspect_ratio` 函数（它仍用于参考图预览和生成请求）
- 不影响其他 UI 组件的行为

---

## 3. 技术方案 (Technical Approach)

### Architecture / Module Changes
- 在 `ui/generation/_internal/handlers.py` 中新增 `FlipRatioHandler` 类
- 修改 `ProviderHandler` 以支持 `flip_checked` 感知
- 无新模块创建，变更集中在 Presentation Layer

### Affected Files / 物理文件变更
- 修改：`ui/generation/_internal/handlers.py` - 新增 FlipRatioHandler，修改 ProviderHandler
- 修改：`ui/generation/contracts.py` - 新增 FlipRatioResponse 数据结构
- 修改：`ui/_app_generation.py` - 绑定 flip_ratio change 事件，更新 provider change 输入

### Core Flow / API Contracts

**flip_ratio 切换流程：**
```
flip_ratio.change
  → FlipRatioHandler.handle_flip_change(flip_checked, current_ratio, provider_name)
  → 返回 FlipRatioResponse(aspect_ratio_update)
  → 更新 aspect_ratio 下拉菜单
```

**provider 切换流程（修改后）：**
```
provider.change
  → ProviderHandler.handle_provider_change(provider_name, current_token, flip_checked, state_machine)
  → 返回 GenerationResponse（aspect_ratio_update 根据 flip_checked 翻转）
```

### Data Structures / Type Contracts

**新增 `FlipRatioResponse`：**
```python
@dataclass(frozen=True)
class FlipRatioResponse:
    aspect_ratio_update: GradioUpdateValue

    def to_output_tuple(self) -> tuple[GradioUpdateValue]:
        return (self.aspect_ratio_update,)
```

**辅助函数：**
```python
def flip_ratio_value(ratio: str) -> str:
    """翻转单个 ratio 值，如 '2:3' → '3:2'"""
    if ":" not in ratio or ratio == "original":
        return ratio
    w, h = ratio.split(":")
    return f"{h}:{w}"

def flip_ratio_choices(choices: list[str], should_flip: bool) -> list[str]:
    """翻转整个 choices 列表"""
    if not should_flip:
        return choices
    return [flip_ratio_value(c) for c in choices]
```

---

## 4. 备选方案与权衡 (Alternatives & Trade-offs)

### Considered Alternatives
- 方案 A：仅在内部计算时翻转，UI 保持不变（当前行为）
  - 不采用原因：用户困惑，UI 显示与实际行为不一致
- 方案 B：移除 flip_checked，让用户直接选择翻转后的比例
  - 不采用原因：需要修改配置文件，增加选项数量（每个比例都要列两次）

### Trade-offs
- 优点：UI 直观反映实际行为，用户体验提升
- 成本：需要额外的事件绑定和处理器，增加少量代码复杂度

---

## 5. 依赖、约束与风险 (Dependencies, Constraints & Risks)

### Dependencies / Preconditions
- 依赖 `BasicParamsPanel` 提供 `flip_ratio` 和 `aspect_ratio` 组件
- 依赖 `ProviderUIContext.aspect_ratios` 提供原始比例列表

### Constraints
- `_internal/` 模块不可被外部直接导入
- 必须保持 `GenerationResponse.to_output_tuple()` 的返回顺序不变

### Risks
- 低风险：事件绑定顺序可能影响 UI 更新时序，需验证

---

## 6. 验证与完成标准 (Validation & Done Criteria)

### Validation
- `python -m compileall ui/` 无语法错误
- `python app.py` 可正常启动
- 手动测试：选中 flip_ratio 后，aspect_ratio 下拉菜单选项正确翻转
- 手动测试：切换 Provider 后，aspect_ratio 根据 flip_ratio 状态正确显示

### Done Criteria
- flip_ratio 选中时，aspect_ratio 下拉菜单的 choices 和 value 同步翻转
- Provider 切换后，aspect_ratio 正确反映当前 flip_ratio 状态
- 生成请求中 `aspect_ratio` 参数值与 UI 显示一致

---

## 7. 迁移与回滚 (Migration & Rollback)

### Migration Plan
- 一次性切换，无兼容层需求
- 纯 UI 层变更，不影响已保存的任务或配置

### Rollback Plan
- 回退 3 个文件的修改即可恢复原有行为
