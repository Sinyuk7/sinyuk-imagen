# 执行任务清单 (Tasks)

> 规则：
> - 必须使用标准 Checkbox：`- [ ]` / `- [x]`
> - 每个任务必须是**可执行 + 可验证**的最小单元
> - 按依赖顺序排列（先主链路，后清理）
> - 若任务涉及多个模块或无法在单个 session 内完成，应拆分为子任务（防止卡死）

---

## 1. 数据结构与契约 (Contracts)

- [x] 1.1 在 `ui/generation/contracts.py` 中新增 `FlipRatioResponse` 数据类
  - 包含 `aspect_ratio_update: GradioUpdateValue`
  - 实现 `to_output_tuple()` 方法

---

## 2. 核心实现 (Core Implementation)

- [x] 2.1 在 `ui/generation/_internal/handlers.py` 中新增辅助函数
  - `flip_ratio_value(ratio: str) -> str` - 翻转单个 ratio 值
  - `flip_ratio_choices(choices: list[str], should_flip: bool) -> list[str]` - 翻转整个列表

- [x] 2.2 在 `ui/generation/_internal/handlers.py` 中新增 `FlipRatioHandler` 类
  - 构造函数接收 `UIContext`
  - 实现 `handle_flip_change(flip_checked, current_ratio, provider_name)` 方法
  - 返回 `FlipRatioResponse`

- [x] 2.3 修改 `ProviderHandler.handle_provider_change` 方法
  - 新增 `flip_checked: bool` 参数
  - 在构建 `aspect_ratio_update` 时调用 `flip_ratio_choices` 处理选项
  - 在设置 `value` 时根据 `flip_checked` 状态翻转默认值

---

## 3. 事件绑定 (Integration)

- [x] 3.1 修改 `ui/_app_generation.py` 中 `bind_generation_events` 函数
  - 为 `flip_ratio` 组件新增独立的 `.change` 事件绑定
  - 调用 `FlipRatioHandler.handle_flip_change`
  - 输出更新 `aspect_ratio` 组件

- [x] 3.2 修改 `ui/_app_generation.py` 中 provider 切换事件
  - 在 inputs 中添加 `flip_ratio` 组件
  - 更新 lambda 传递 `flip_checked` 参数

- [x] 3.3 更新 `ui/generation/_internal/handlers.py` 的 `__all__` 导出列表
  - 添加 `FlipRatioHandler`

---

## 4. 清理与收口 (Cleanup)

- [x] 4.1 检查 `get_effective_aspect_ratio` 函数是否仍需保留
  - 确认用于参考图预览和生成请求的场景
  - 已移除使用：UI 现在直接显示翻转后的值，不再需要内部翻转

---

## 5. 自检与验证 (Verification)

> 必须基于真实执行结果填写状态  
> 未执行项必须标记为 Not Run，禁止推测为 Pass

- [x] 5.1 运行 `python3 -m compileall ui/` 并修复错误
- [x] 5.2 运行 `python app.py` 确认应用正常启动
- [x] 5.3 手动测试：选中 flip_ratio → aspect_ratio 下拉菜单选项翻转
- [x] 5.4 手动测试：切换 Provider → aspect_ratio 根据 flip_ratio 状态正确显示
- [x] 5.5 手动测试：生成请求 → 确认 aspect_ratio 参数值与 UI 显示一致
