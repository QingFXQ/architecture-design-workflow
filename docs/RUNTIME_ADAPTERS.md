> 历史部署／验证资料，原日期与证据范围保留；不构成当前多Agent、模型分档或Gate的执行要求。当前入口：[工作流](../workflows/PIPELINE_WORKFLOW.md)。收录本文件不触发部署或安装。

# 运行时适配器｜把工作流从某个工具中解耦

- 状态：active
- 更新：2026-10-20
- 目的：让 `multica-arch-studio` 的方法、Gate 和资产不依赖某一个模型、IDE 或调度器。Codex、OpenClaw、DSH 都是**适配器**，不是工作流本身。

## 1. 为什么要适配器

仓库原有文档把“执行器”写成了 Codex，把“调度器”写成了 OpenClaw，并默认 Mac → SSH → Windows Revit。这在 2026-08 的环境里成立，但会产生三个问题：

1. 换一个执行器（例如 DSH）时，文档看起来“不可用”，即使方法本身仍然成立。
2. 执行器与 Revit 同机时，SSH 和 Mac 变成不必要的硬前提。
3. 模型名（`gpt-5.6-sol/terra/luna`）被写成流程要求，而不是可替换的配置。

适配器层只回答“谁在什么环境里执行、如何记录”，不改变六角色、四道 Gate 和共享事实源。

## 2. 四个运行时职责

| 职责 | 做什么 | 不做什么 |
|---|---|---|
| Executor（执行器） | 读写文件、运行命令、调用 MCP、生成 artifact、跑测试 | 不代替用户做 Gate 决定；不把工具成功写成设计通过 |
| Scheduler（调度器） | 派发 Issue、串行/并行编排、保存运行记录、汇总状态 | 不替执行器写代码/改配置；不越过 Gate |
| Reviewer（复核者） | 按预先写明的验收项读证据、查矛盾、给出通过/退回 | 不重新设计；不以“再看看”代替验收 |
| User（用户/教师） | Gate A–D、课程要求、最终审美与取舍 | 不被 AI 的“建议”替代 |

一个工具可以同时承担多个职责，但**职责必须显式**。例如 DSH 既是执行器也是调度器；这不会自动让它获得 Gate 权力。

## 3. 当前适配器

| 适配器 | 典型职责 | 文件/工具 | Gate 约束 |
|---|---|---|---|
| Codex | Executor | 读写仓库、运行命令、调用 MCP | 不替代 Gate；不把模型名当流程前提 |
| OpenClaw | Scheduler | 读取项目状态、派发/串行调度、保留运行记录 | 不编码、不改配置、不制作设计成果 |
| DSH | Executor + Scheduler + Reviewer 辅助 | 文件读写、`subagent`/`workflow`、`cordis` 插件、MCP、Web GUI | 同 Codex；子 Agent 不获得 Gate 权力 |
| Manual | User/Teacher | 课程要求、图纸检查、机位选择、签字 | Gate 唯一来源 |

### 3.1 DSH 适配要点

- **同机优先**：DSH、Revit 2021、MCP server 在同一台 Windows 上时，链路是 `DSH → MCP stdio → localhost:8080 → Revit 插件`，不需要 SSH，也不需要 Mac。
- **跨机才用 SSH**：如果执行器在另一台机器，ssh 隧道只解决传输；npm server 仍须在 Revit 同机运行。
- **路径配置化**：`C:\Program Files\Autodesk\Revit 2021\Revit.exe`、`/path/to/user-home`、`YOUR_REVIT_HOST` 是环境示例，不是流程常量；启动前写入本机配置或环境变量。
- **子 Agent 边界**：`subagent`/`workflow` 可以并行做检索、检查、文档，但不能并行产生互相竞争的设计结论；一个 Issue 只有一个主要责任角色。
- **插件边界**：DSH 插件可以封装状态校验、日志索引、图纸清单、Gate 包检查；插件不得自动通过 Gate，也不得在 Gate B 前自动启动正式 Drawing。
- **记录**：每个会话至少写一条 `PROJECT_LOG.md` 条目；工具日志按项目存放在 `.revit-work/logs/`，不混入工作流仓库。

## 4. 模型名与路由

`docs/MODEL_ROUTING.md` 中的 `gpt-5.6-sol/terra/luna` 是**当前 Codex 适配器的模型示例**，不是跨平台要求。其他执行器按同样的三档能力映射：

| 能力档 | 用途 | 判定标准 |
|---|---|---|
| 高价值推理 | Skill 审校、跨文件矛盾、复杂方案/规范风险、最终审查 | 任务开放、涉及不可逆选择或跨阶段冲突 |
| 日常主力 | 方案深化、Revit/Blender 接入、文档集成、常规审查 | 边界清楚、有明确验收标准 |
| 机械执行 | 字段提取、分类、清单核对、结构化摘要 | 规则可枚举、结果可批量抽检 |

规则不变：机械档的输出只能作为候选/索引，不能直接写成事实、规范结论或 Gate 通过；至少由日常档复核，高影响内容再由高价值档或用户复核。

## 5. Gate 等价性检查

任何适配器接入前，必须能回答：

1. Gate A–D 是否仍由用户明确决策，且写入 `DECISIONS.md`？
2. 正式 Drawing 是否仍以 Gate B 批准为入口？
3. Scheme 的 CAD/Revit 验证是否有授权、可回滚、有回读，并按 `SCHEME_DRAWING_REVIEW.md` 标注候选状态？
4. 每次 Gate 输入是否绑定唯一设计版本，旧版本是否保留？
5. 工具调用成功是否仍与建筑/图纸/视觉真实性检查分开记录？
6. 运行日志、artifact manifest、`PROJECT_LOG.md` 是否可追溯？

任一项答“否”，该适配器只能做辅助，不能作为生产执行器。

## 6. 迁移规则

- 文档中出现“Codex 负责全部开发”时，读作“当前执行器负责全部开发”；出现“OpenClaw 仅作调度”时，读作“当前调度器仅作调度”。
- 新写文档优先使用 **Executor / Scheduler / Reviewer / User**，需要举例时再写具体工具名。
- 不因适配器变化而改 Gate 定义、共享事实源或 Skill 契约；只改运行配置、路径、模型映射和日志位置。
- 适配器变更本身要进 `PROJECT_LOG.md` 和工作流 commit，写明旧链路、新链路、验证证据和回退方式。

## 7. 相关文件

- [`MODEL_ROUTING.md`](MODEL_ROUTING.md)：模型分层与预算纪律
- [`TOOLS.md`](TOOLS.md)：Revit/Blender/超分/RAG 的接入与验证状态
- [`MULTICA_DEPLOYMENT.md`](MULTICA_DEPLOYMENT.md)：Multica 部署方案（尚未配置）
- [`../workflows/SCHEME_DRAWING_REVIEW.md`](../workflows/SCHEME_DRAWING_REVIEW.md)：Scheme 验证与正式 Drawing 的边界
- [`../templates/PROJECT_LOG_TEMPLATE.md`](../templates/PROJECT_LOG_TEMPLATE.md)：追加式工作日志模板
