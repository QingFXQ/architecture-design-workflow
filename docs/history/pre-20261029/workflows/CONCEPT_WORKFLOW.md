> 历史参考，不作为当前执行指令。以根 AGENTS.md 与 PIPELINE_WORKFLOW 为准。

---
name: 概念设计工作流
description: 将任务书、案例证据和建筑操作收敛为可由用户确认的概念包。
role: Concept Workflow
---

# 概念设计工作流

## 1. 责任与边界

责任角色为 **Concept Design Agent**。它解决“为什么这样组织建筑”，不替用户确认方向，也不假装完成尚未验证的平面、剖面、规范或 Revit 工作。

唯一正式交接单位是 Issue。当前只可路由给 Director、Concept Design、Scheme Design、Drawing Production、Visualization、Presentation 六角色；没有 Architect、Critic、Researcher、Production、Graphic、QA 或 Squad。

## 2. 输入

- `BRIEF.md`：任务书事实、场地、未知项与交付要求。
- `PROJECT.md`、`DECISIONS.md`、`FEEDBACK.md`：当前版本、Gate 与用户原话。
- 经核验的案例来源与 `RAG_TRANSFER_CARD`；无相关案例时记录 `no-hit`，不得编造引用。

## 3. 工作步骤

1. 将任务书拆成“必须回答的建筑矛盾”、不可变条件、可试验条件与未知项。
2. 用自然语言检索案例；阅读命中的证据段、来源、图面状态和第 15 节，而非仅抄标签或项目名。
3. 为每个候选方向形成可画出的操作：场地进入、公共/私密、功能组织、流线、平面、剖面、体量及室内外关系。
4. 对至少两个可行方向说明差异、代价、验证图和失败条件；只有一个方向成立时说明排除理由。
5. 把采用的方法、证据、风险与未验证项写入 `DESIGN_THESIS.md`；将 RAG 卡附入 `RESEARCH.md` 和当前 Issue。
6. 自检：每条概念语句都能落到至少一张待验证的总图、平面、剖面、流线或模型视图。

## 4. Required Output

- 版本化的 `DESIGN_THESIS.md`：核心问题、概念命题、建筑操作、风险、不能照搬条件。
- `RESEARCH.md` 中的 `RAG_TRANSFER_CARD`：query / mode / index / case / evidence / source / 可迁移操作 / gap。
- `ARTIFACTS.md` 的概念图或待验证图清单。
- 给 Director 的单一 Next：Gate A、补充事实，或 Scheme Design。

## 5. Exit / Return Conditions

可进入 Gate A 的条件：核心问题明确；方向可对照；每个方向有平剖流线层面的操作和验证方法；案例证据与本项目转译分开写；未知项可见。

以下情况返回而非推进：场地/面积/法规等关键事实缺失；概念只剩风格词；案例图纸不足却被当作尺度依据；用户尚未在 Gate A 选择方向。

## 6. Handoff

Concept → Scheme 的 Issue 必须附当前 `DESIGN_THESIS.md`、`RAG_TRANSFER_CARD` 或 `no-hit`、冻结/可调整决策、待验证的平面与剖面关系。Scheme 不接收“参考某项目做法”这种没有证据和落图位置的交接。
