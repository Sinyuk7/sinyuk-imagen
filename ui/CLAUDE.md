# UI Layer — CLAUDE.md

> 面向 AI 编码助手（Claude / GPT / Code Agent）的 UI 层设计规范  
> 核心目标：用“数据流 + 状态 + 事件”构建 UI，而不是写流程控制代码

---

# 1. 一句话架构

UI = **状态收集器 + 事件触发器 + 结果渲染器**

用户操作 → 事件 → 状态转换 → Service → 返回结果 → UI 更新

---

# 2. UI 层职责（强约束）

UI 层只做 4 件事：

1. 收集用户输入（组件 = 状态）
2. 构造 `TaskConfig`
3. 调用 `ImageService`
4. 渲染结果（Gallery / Error）

---

## ❌ UI 禁止做

- Provider 逻辑
- API 调用细节
- 参数转换
- prompt 加工
- 错误解析
- 使用 global 状态

---

# 3. 分层架构（不可违反）

UI (Gradio)
  │
  ├── ConfigManager（只读）
  │
  └── ImageService（唯一入口）
        │
        └── Provider（UI 不可见）

原则：

- UI 不能接触 Provider
- UI 只能调用 Service

---

# 4. 数据流模型（核心）

组件（state） → 事件（trigger） → 函数（transform） → 输出（state）

映射：

- 组件 = 状态
- 事件 = 触发
- 函数 = 状态转换
- return = UI 更新

---

# 5. Gradio 事件设计模式

## 5.1 单向数据流

input.change(fn, inputs=input, outputs=output)

---

## 5.2 多输入多输出

btn.click(fn, inputs=[a, b], outputs=[c, d])

---

## 5.3 组件联动

provider.change(on_provider_change, provider, model)

---

## 5.4 事件链（推荐）

btn.click(step1).then(step2).then(step3)

支持：

- then
- success
- failure

原则：

- 拆小函数
- 用链表达流程

---

## 5.5 多触发统一处理

gr.on(
    triggers=[btn.click, input.submit],
    fn=process,
    inputs=[input],
    outputs=[output]
)

---

# 6. 状态管理（关键）

## ✅ 推荐

state = gr.State()

btn.click(fn, inputs=[input, state], outputs=[output, state])

规则：

- state 必须输入 + 输出
- 每次更新都是状态迁移

---

## ❌ 禁止

global data

原因：

- 并发不安全
- 会丢数据
- 不可追踪

---

# 7. TaskConfig 构造（UI → Service 边界）

TaskConfig(
    prompt=prompt,
    provider=provider,
    model=model,
    params={
        "image_count": int,
        "aspect_ratio": str
    },
    extra=dict
)

规则：

- params = 通用参数
- extra = Provider 专属参数（JSON）
- UI 不做任何转换

---

# 8. 标准事件流（核心）

generate_btn.click → on_generate()

on_generate():

1. 解析 JSON（advanced_params）
2. 构造 TaskConfig
3. 调用 image_service.generate()
4. 返回结果

---

## 返回规则（必须遵守）

if result.success:
    return result.images
else:
    raise gr.Error(result.error)

---

# 9. ConfigManager 可用能力

只允许使用：

- get_provider_names()
- get_active_provider_name()
- get_models(provider)
- get_ui_config()

只读，不做写操作（默认）

---

# 10. UI 组件结构（标准布局）

Blocks
 ├── Markdown（标题）
 ├── Row
 │   ├── Column（控制区）
 │   │   ├── Textbox（prompt）
 │   │   ├── Dropdown（provider）
 │   │   ├── Dropdown（model）
 │   │   ├── Slider（image_count）
 │   │   ├── Dropdown（aspect_ratio）
 │   │   ├── Accordion（advanced JSON）
 │   │   └── Button（generate）
 │   └── Column（输出区）
 │       └── Gallery

---

# 11. 事件绑定（必须遵循）

## Provider → Model 联动

provider.change → on_provider_change

逻辑：

- 读取 models
- return gr.update(...)

---

## Generate 事件

generate_btn.click → on_generate

流程：

- 校验 JSON
- 构造 TaskConfig
- 调用 service
- 返回 images 或 error

---

# 12. UI 设计模式（推荐）

## 小函数 + 事件链

btn.click(step1).then(step2).then(step3)

---

## 数据流优先（不要写控制流）

❌ 不要：

if provider == xxx

✅ 要：

provider change → 自动更新 model

---

## 显式状态流

fn(inputs=[..., state], outputs=[..., state])

---

# 13. 常见模式

## Pipeline

btn.click(step1, inputs=a, outputs=b)
btn.click(step2, inputs=b, outputs=c)

---

## 自动联动

cart.change(update_total, cart, total)

---

# 14. 错误处理规范

必须：

raise gr.Error("message")

禁止：

- return None
- print
- 吞异常

---

# 15. Gradio 关键坑

## 参数顺序必须一致

inputs=[a, b] → fn(a, b)

---

## 更新组件必须用 gr.update

return gr.update(choices=models, value=models[0])

---

## JSON 必须校验

data = json.loads(text)

必须保证：

- 合法 JSON
- 是 dict

---

# 16. 扩展指南

## 新增通用参数

1. 添加组件
2. 加入 inputs
3. 写入 params

---

## 新增 Provider 参数

不改 UI

直接 JSON → extra

---

## 新增 Provider

只改 config.yaml

UI 自动生效

---

# 17. 反模式（必须避免）

- 在函数内部操作组件
- UI 直接调用 Provider
- 使用 global
- 一个函数做所有事
- 依赖执行顺序而不是数据流

---

# 18. 核心原则（最终）

1. UI 只负责收集与展示
2. 所有状态必须显式传递
3. 所有 UI 更新必须通过 return
4. 每个函数只做一件事
5. 用事件链表达流程

---

# ✅ 最终总结

用「组件 = 状态 + 事件驱动 + 小函数」构建数据流  
而不是写流程控制 UI