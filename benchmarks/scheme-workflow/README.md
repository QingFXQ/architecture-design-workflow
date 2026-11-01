# Scheme Workflow Benchmark

这是对现行 Concept / Scheme / RAG / Gate B 接口的可复跑实战验收，而不是自动生成建筑方案的工具。每个 Brief 必须按以下顺序人工运行对应 Agent：

`Brief → Concept Package → 模拟 Gate A 决策 → Scheme Package → building-code-check → 模拟 Gate B`。

RAG 查询、原始 `RAG_TRANSFER_CARD`、stdout/stderr、exit code、案例取舍和方案包必须保存在同一 run 目录。评分由独立审查者完成；不以 RAG 排名或文档字数代替建筑判断。旧的仅 Markdown 记录必须标记为 `raw_card_missing`，不能回填或伪造历史工具日志。

## 评分

每项为 0–5，共 19 项、满分 95：问题定义质量、RAG Query 质量、案例相关度、跨类型案例使用、`RAG_TRANSFER_CARD` 质量、案例方法迁移质量、概念继承、总图逻辑、功能组织、平面逻辑、剖面逻辑、流线逻辑、室内外关系、尺度合理性、面积控制、基本结构合理性、规范风险意识、方案变体是否真的不同、Gate B Handoff 完整性。

- `0–1`：缺失、无证据或违反明确边界。
- `2`：有意图但不能落到图纸或存在关键冲突。
- `3`：可用草案，有明确风险与待验证项。
- `4`：证据、操作和图纸位置能互相核对。
- `5`：对该项目的关键矛盾有可验证、非复制式的解决。

纯文字声称“已经画出平面/剖面”的相关项最高为 2 分；每项至少应回指一个输出章节、可核查表、图纸 artifact 或工具日志。

## 通过口径

建议通过线为 72/95，且概念继承、平面、剖面、流线、面积、方案变体和 Gate B Handoff 均不得低于 3。任一 Revit readiness 字段未满足，或 Gate B 未批准却交给 Drawing，均为阻断失败。

该 Benchmark 的 Gate B 是模拟决策，仅验证交接完整性，绝不授权进入正式 Drawing。真实项目仍须由用户完成 Gate A / Gate B；工具前检与写入能力须有实际会话证据，历史 H-02 状态仅对应其记录的环境，不替代当前验证。

补充[方案与画图行为验收情景](scheme-drawing-review.md)，覆盖意图/审美偏离、整体变换、核心筒协调、数据口径、表达深度及软件恢复。它们是待执行情景与判据，不是已通过记录。Scheme 的已授权验证与正式 Drawing 分别按[共同检查约定](../../workflows/SCHEME_DRAWING_REVIEW.md)管理；模拟 Gate 和静态检查都不授权写入真实模型。
