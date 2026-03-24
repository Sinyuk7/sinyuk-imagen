# 总体设计与需求 (Design)

## 1. 背景与目标 (Context & Goals)

### Why
- [当前问题 / 痛点]
- [为什么现在要做]

### Goals
- [目标 1]
- [目标 2]

---

## 2. 范围与变更内容 (Scope & Changes)

### In Scope
- [核心变更 1]
- [核心变更 2]
- [如有 BREAKING 变更，请标注 **BREAKING** 并说明影响]

### Out of Scope / Non-Goals
- [明确不做的事 1]
- [明确不做的事 2]

---

## 3. 技术方案 (Technical Approach)

### Architecture / Module Changes
- [模块划分、目录结构、边界变化]
- [新增 / 删除 / 重构模块]

### Affected Files / 物理文件变更
<!-- 用于锁定修改范围（Blast Radius），不要使用 checkbox -->
- 创建：`path/to/new_file.py`
- 修改：`path/to/existing_file.py`
- 删除：`path/to/obsolete_file.py`

### Core Flow / API Contracts
- [入口函数 / 调用链]
- [输入 / 输出 / 错误处理约定]
- [兼容性策略（是否保留旧入口）]

### Data Structures / Type Contracts
- [新增或修改的数据结构 / 类型 / DTO]
- [关键字段变化]

---

## 4. 备选方案与权衡 (Alternatives & Trade-offs)

### Considered Alternatives
- 方案 A：[描述]
  - 不采用原因：[说明]
- 方案 B：[可选]

### Trade-offs
- 优点：[为什么选当前方案]
- 成本 / 风险：[当前方案的代价]

---

## 5. 依赖、约束与风险 (Dependencies, Constraints & Risks)

### Dependencies / Preconditions
- [依赖模块 / 外部系统 / 配置]

### Constraints
- [必须遵守的边界，例如：`_internal/` 不可跨模块访问]
- [性能 / 稳定性 / 兼容性约束]

### Risks
- [技术风险 1]
- [技术风险 2]

---

## 6. 验证与完成标准 (Validation & Done Criteria)

### Validation
- [需要通过的检查：compileall / mypy / import / 测试等]
- [需要人工确认的行为]

### Done Criteria
- [完成标准 1]
- [完成标准 2]

---

## 7. 迁移与回滚 (Migration & Rollback)

### Migration Plan
- [平滑迁移 / 一次性切换 / 兼容层策略]

### Rollback Plan
- [失败时如何回退]