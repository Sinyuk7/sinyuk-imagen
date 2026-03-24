# 阶段执行总结与接力棒 (Relay Summary)

## 1. 本次 Session 完成项 (Completed This Session)
- ✅ [完成项 1]
- ✅ [完成项 2]

---

## 2. 当前任务状态快照 (Task Status Snapshot)

### 已完成
- [任务编号，例如：1.1, 1.2]

### 进行中
- [任务编号 + 当前进展]

### 未开始
- [关键未开始任务]

---

## 3. 门禁与自检状态 (Verification Status)

| 检查项 | 状态 | 备注 |
|---|---|---|
| Compileall | Pass / Fail / Not Run | |
| MyPy | Pass / Fail / Not Run | |
| Import 自检 | Pass / Fail / Not Run | |
| Smoke Test | Pass / Fail / Not Run | |

---

## 4. 设计偏差与关键发现 (Design Deviations & Findings)

- 偏差说明：[是否与 design.md 一致]
- 关键发现：[新发现的问题 / 隐式依赖 / 架构问题]

### Design Sync
- 是否已同步到 `design.md`：Yes / No
- 若 No，需要更新：
  - [具体章节或内容]

---

## 5. 遗留问题与风险 (Open Issues & Risks)

- ⚠️ [技术债]
- ⚠️ [未解决问题]
- ⚠️ [潜在风险 / 阻塞]

---

## 6. 下一阶段建议 (Next Steps)

1. [优先任务 1]
2. [优先任务 2]
3. [后续验证或收口动作]

---

## 7. 下一 Session 启动 Prompt (Starter Prompt)

> 复制以下内容作为下一轮起点：

**上下文**：  
上一阶段完成：[简述]  
当前状态：[剩余任务 / 风险]

**目标**：
1. [目标 1]
2. [目标 2]

**约束**：
- 保持 [架构边界]
- 不破坏 [关键契约]
- 完成后更新 tasks.md 并生成新的 relay.md