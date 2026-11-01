> 可选历史任务单模板；不再要求每个动作创建Issue或走固定角色／Gate。普通连续制作使用PROJECT与实际成果即可。参见[主流程](../workflows/PIPELINE_WORKFLOW.md)。

# Issue 模板

Issue 是唯一正式交接单位。只可路由给 Director、Concept Design、Scheme Design、Drawing Production、Visualization 或 Presentation；不得创建旧角色、Squad 或额外审批环节。

```markdown
# [阶段][责任角色][对象 / 版本] 动作 + 可验收结果

## Context
- 项目、当前阶段、版本与上游 Issue：
- Gate 状态、用户原话与冻结决策：
- 工作模式：Scheme 验证 / 正式 Drawing；意图基准及技术准备度：
- 已确认事实、未知项与风险：

## Goal
- 本轮要证明或交付的可观察结果：

## Constraints
- 必须保留、允许调整、不在范围：
- 固定视觉对照与偏离迹象；重大取舍的决定权限：
- 若使用 RAG，附 `RAG_TRANSFER_CARD`：query / mode / index → case id/path → evidence/source → quality → transferable operation → target drawing → do-not-copy/gap。

## Relevant Files
- 项目事实源、版本、关联 Issue、关键图纸或成果：

## Expected Output
- 写入文件、成果 ID、证据、风险和唯一 Next：
- 更新当前主模型/图册及恢复点；对象深度、面积容量口径、变更影响与失效检查：

## Done Criteria
- [ ] 满足责任角色的 Required Output 与 Exit Criteria。
- [ ] 按[共同检查约定](../workflows/SCHEME_DRAWING_REVIEW.md)复核意图审美、空间功能、模型技术与表达交付，附范围、版本、限制及实际图面证据。
- [ ] 变更影响中的检查已复查，或明确待复查且未扩大完成结论。
- [ ] 未知项、证据缺口和用户决定事项已显式记录。
- [ ] Gate 尚未通过时保持对应 Scheme/修复责任并记录下一步；正式交接须满足完整准备度与用户批准，交给唯一 Next 角色。
```

## 最小 RAG 交接卡

使用 `search_cases.py --format card` 生成；Concept→Scheme 必须附卡或明确 `no-hit`。Drawing 不接收案例正文，只接收已转译、已冻结的方法决策和落图位置。
