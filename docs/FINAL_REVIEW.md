> 历史部署／验证资料，原日期与证据范围保留；不构成当前多Agent、模型分档或Gate的执行要求。当前入口：[工作流](../workflows/PIPELINE_WORKFLOW.md)。收录本文件不触发部署或安装。

# Multica Architecture Studio 最终验收审查

- 审查级别：Sol 最终审查
- 原审查日期：2026-08-11（Asia/Shanghai）；Phase 3 复测更新：2026-08-12（Asia/Shanghai）
- 当前结论：**部分可用；Scheme 基准可复跑，实机 Revit 与已部署 Multica 链路仍 blocked。**
- 本轮直接修复：历史审查记录；当前 RAG 状态以 `knowledge/architecture-case-rag/README.md`、`benchmarks/results/` 和本文件末尾增补为准。
- 内容保护：未改动案例正文与 `research/` 原始资料；案例与索引数量均由构建脚本统计。

> **Phase 3 覆盖说明（以此为准）：** 之后的“通过/可进入 Revit”文字是上一轮的仓库结构审查结论，不等于真实端到端验收。2026-08-12 已完成三套本地角色＋Skill 合成 Scheme 基准，分别为 69/95、70/95、70/95，全部因没有版本化图纸 artifact、坐标/轴网/标高与构件参数而正确停在模拟 Gate B，未进入 Drawing。2026-08-13 已在真实 Windows Revit 2021 完成 Revit MCP 插件安装、8080 监听、26 tool discovery、活动视图与模型统计两项只读调用；Level 1/2/3 与小型建筑仍未开始，不能算作建模或出图通过。`multica agent list` 也未配置 server，因此这些运行不能称作已部署 Multica Agent 实跑。详见 `benchmarks/scheme-workflow/`、`benchmarks/revit-mcp/RESULT.md` 和 RAG 的质量审计报告。

## 1. 审查范围与方法

已核读用户指定的全部范围：

- `agents/`：6 个 Agent 指令。
- `skills/`：9 个 Skill。
- `workflows/`：3 个工作流。
- `docs/`：`TEAM_ARCHITECTURE`、`MODEL_ROUTING`、`TOOLS`、`RAG`、`HUMAN_ACTION_REQUIRED`、`SQUADS`，以及根目录 `README.md`。
- `knowledge/architecture-case-rag/`：案例数量由构建脚本统计，包含 README、metadata/section semantic 检索、Benchmark、ontology、ingestion 和 JSON 索引。
- `tools/revit-mcp/`：README、SETUP、TEST_PLAN、HUMAN_ACTION_REQUIRED；并按其记录的上游源码静态核对实际工具边界。
- `research/`：Revit 资料 10 篇、建筑规范资料 7 篇、Blender/超分资料 2 篇，只读审查。

仓库根目录有 Git 元数据；本报告不代表已经创建提交。修复通过文件复读、结构扫描、派生索引比较和脚本测试验证。

## 2. 用户规格 §42 逐项结论

### 1. 有没有偷偷扩张成软件开发项目

**结论：通过。**

当前成果仍是建筑设计事务所工作流、专业 Skill、本地案例库和外部工具接入说明，没有自研设计引擎、Agent 平台、规范规则引擎或业务数据库。Case RAG 使用标准库脚本调用本机 Ollama 做 section embeddings 与可选 rerank；它不是云服务或自动设计系统。`tools/revit-mcp/repo/` 是固定上游浅克隆，不是本项目自研平台。`building-code-check` 明确禁止把规范检查扩张为自动合规规则系统，Pipeline 也禁止新增复杂系统或软件开发项目。

### 2. 有没有不必要的 Agent

**结论：问题已修复，通过。**

当前唯一有效结构是 1 个 Director + 5 个专业 Agent：Concept、Scheme、Drawing、Visualization、Presentation。旧八角色与三个 Squad 只存在于历史资料；本轮给 `docs/SQUADS.md` 加入不可路由的归档声明，并在两个旧子工作流顶部加入唯一有效的六角色执行契约。旧 Architect、Critic、Researcher、Production、Graphic、QA 不得被创建或调度。

### 3. Skill 是否真正能协同

**结论：问题已修复，通过。**

9 个 Skill 均已具备可检索的五段契约：Required Input、Required Output、Exit Criteria、Return Conditions、Next。原本缺少显式契约且仍使用旧 `Architect` 称谓的 `museum-design` 与 `kindergarten-design` 已补齐，并被定义为 Concept/Scheme 调用的类型专项检查，不是新 Agent；输出回到当前调用者。Concept/Scheme 中残留的不存在 `Researcher` 路由也已删除。

### 4. Concept → Scheme → Revit 是否能完整 Handoff

**结论：Critical 问题已修复，通过。**

Gate 含义现已统一：

| Gate | 当前含义 | 责任与决定 |
| --- | --- | --- |
| A | 概念方向选择 | Concept 提供 3–5 个方向，Director 守门，用户选择 |
| B | 方案确认/批准进入 Revit | Scheme 提供完整方案确认包，Director 守门，用户批准 |
| C | Revit 模型与图纸检查 | Drawing 提供平面、剖面、三维和图纸证据，用户检查 |
| D | 摄像机选择 | Visualization 提供候选，用户选择或人工摆机位 |

原 `scheme-development` 把 Gate C 错写成“用户批准进入 Revit”，导致 Gate B/C 重复。本轮已统一为 Gate B，并明确 Gate C 只属于 Drawing 阶段。方案确认包覆盖总图、各层平面、关键剖面、体量、主要尺寸、层高/标高、功能、门窗、楼梯电梯、结构逻辑、规范风险、冻结特征和允许微调范围；Drawing 输入契约能够直接核查这些字段。

### 5. Drawing Production Agent 是否具备 Revit 专家知识

**结论：通过。**

`revit-expert` 不是工具名清单，而是完整 Revit/BIM 成图方法：按“原生系统构件 → 成熟 Loadable Family → 参数化 Family → 必要 In-Place/Mass → 脚本/API → 纯几何 workaround”排序；覆盖类别、宿主、标高、类型/实例参数、Group/Array、幕墙、楼梯栏杆、View Template、Filter、Schedule、Tag、Sheet、PDF 和模型健康。它与源码静态核对出的 26 个 MCP tool 对齐，并明确 MCP `success`/ElementId 不等于建筑正确，重要建模后必须看关键平面、关键剖面和 3D 预览，再提交 Gate C。

### 6. Case RAG 是否真正有建筑设计价值

**结论：问题已修复，通过。**

案例均具有唯一 ID 和 1–15 节因果结构，当前数量以 `build_index.py` 输出为准。检索器以 `--query` 的 section-level semantic retrieval 为默认入口，保留 `--problem` 的 AND baseline、metadata 过滤、可选 hybrid 及本地 rerank；每个结果携带 evidence sections。本轮已重建 metadata 与 semantic index；未改案例正文。

### 7. drawing-standard 是否保持占位、没有瞎猜老师标准

**结论：通过。**

`drawing-standard` 仍是明确的刻意占位；标准未提供时唯一输出是“当前无已确认制图标准”。它禁止猜测线宽、字体、图框、比例、命名和课程偏好，并写明未来填充必须记录教师依据、适用范围、版本和样图验证。本轮只修正 `docs/HUMAN_ACTION_REQUIRED.md` 对其“尚不存在”的错误描述，没有填入任何猜测标准。

### 8. Visualization 是否保留人工摄像机接管点

**结论：通过。**

Gate D 完整保留：Visualization 先给 3–5 个低质量机位预览；用户可选择候选，也可在 Blender 人工摆机位。没有复杂自动构图算法，也禁止为了替代人工接管开发此类系统。没有 Gate D，不进入正式基础渲染与图像增强。

### 9. 是否存在明显重复功能

**结论：问题已修复，通过。**

当前 Agent 职责没有活动态重复：Director 只管路由/契约/版本，Concept 负责方向，Scheme 负责方案，Drawing 负责 Revit/图纸，Visualization 负责相机/渲染忠实度，Presentation 负责汇报。`revit-expert` 与 `revit-final-check` 分别是建模方法和终检，`building-code-check` 是风险检查，类型 Skill 是被调用的专项框架，边界不同。旧工作流/Squad 的重复角色已明确归档且不可路由。

### 10. 是否有空壳、假实现、TODO 冒充完成

**结论：问题已修复，通过。**

指定范围没有 0 字节文件。RAG 脚本是真实实现并有测试；Revit 文档诚实标注“静态核查完成、实机端到端未执行”；Blender 和超分也没有冒充已安装。上游 Revit 仓库的三个空 TypeScript 文件被 SETUP 明确排除在 26 个工具之外，没有冒充可调用工具。唯一 TODO 是用户允许的 `drawing-standard` 教师标准占位，且其输出/退出边界清楚。

### 11. 当前成果是否能用于下一次真实建筑设计作业

**结论：通过，但有明确边界。**

下一次真实作业可以直接从任务书校准、Case RAG、3–5 个概念方向、Gate A、方案深化、规范风险检查、Gate B 和完整 Revit Handoff 开始；即使工具链尚未实机接通，也可按文档人工完成 Revit/Blender 阶段。不能宣称自动化生产链已经可用：Revit 2021 插件、Blender MCP、超分链和教师制图标准仍须按人工动作清单完成。基于这一边界，整体不是 BLOCKED，但也不应判为无条件 READY。

## 3. 修复清单

| ID | 级别 | 问题 | 修复动作 |
| --- | --- | --- | --- |
| FR-01 | Critical | Scheme 把 Gate C 当作进入 Revit 批准，和 Gate B 重复 | `scheme-development` 全部统一为 Gate B；明确 Gate C 只在 Drawing 后发生 |
| FR-02 | Critical | Concept 子工作流仍路由旧 Architect/Critic/Researcher/Production | 重写为当前六角色的简洁概念执行流，并把 RAG_TRANSFER_CARD 纳入 Concept→Scheme 交接 |
| FR-03 | Critical | Feedback 子工作流仍依赖旧 Architect/Critic/Production/QA | 重写为当前角色映射、版本证据与用户 Gate 的反馈闭环 |
| FR-04 | Important | `SQUADS.md` 看起来仍是当前三 Squad 配置 | 标题和顶部加入 `ARCHIVED / DO NOT ROUTE`，指定当前唯一权威文件 |
| FR-05 | Important | museum/kindergarten 类型 Skill 缺少五段契约并沿用旧 Architect | 补齐 Required Input/Output/Exit Criteria/Return Conditions/Next，改为 Concept/Scheme 调用服务 |
| FR-06 | Important | Concept/Scheme Skill 仍请求不存在的 Researcher | 改为当前责任 Agent 自行补检索，必要时由 Director 请求用户资料 |
| FR-07 | Important | `docs/TOOLS.md` 错称 RAG 没有 README/scripts/CLI | 更新为本地 Ollama section retrieval、128 案例、semantic/hybrid/rerank 和非平台边界 |
| FR-08 | Important | `docs/RAG.md` 目录树和当前能力陈旧 | 补入 README、scripts、index 和实际命令行检索语义 |
| FR-09 | Important | 人工动作 H-01 错称 `drawing-standard` Skill 不存在 | 指向现有占位 Skill 及其受控填充规则，不新增/猜测标准 |
| FR-10 | Important | JSON 索引落后于案例文件 | 重建派生 metadata/semantic 索引；检索时会核对 corpus hash，避免使用旧向量 |

涉及的修复文件：

- `skills/scheme-development/SKILL.md`
- `skills/concept-design/SKILL.md`
- `skills/museum-design/SKILL.md`
- `skills/kindergarten-design/SKILL.md`
- `workflows/CONCEPT_WORKFLOW.md`
- `workflows/FEEDBACK_WORKFLOW.md`
- `workflows/PIPELINE_WORKFLOW.md`
- `docs/SQUADS.md`
- `docs/TOOLS.md`
- `docs/RAG.md`
- `docs/HUMAN_ACTION_REQUIRED.md`
- `knowledge/architecture-case-rag/index/cases.json`

## 4. 验证结果

- 数量核对：6 Agents、9 Skills、3 Workflows、6 指定 docs；案例数由 `build_index.py` 输出，避免文档陈旧。
- Skill 契约扫描：9/9 均包含 Required Input、Required Output、Exit Criteria、Return Conditions、Next。
- Case 结构扫描：当前案例均具备唯一 ID 与第 1–15 节；具体数量由构建输出记录。
- 索引验证：128 个案例、1,881 个可检索 sections、1024 维本地 embedding；搜索前核对 corpus hash。
- RAG 单测：19/19 通过（含 section parsing、索引新鲜度、交接卡与 rerank 降级）。
- 真实问题检索：自然语言 `--query` 可返回 section evidence；`--problem` baseline 仍保留。
- Markdown 相对链接：扫描 79 个相关 Markdown，断链 0。
- 空文件：用户指定范围内 0；上游 Revit 的三个空工具源文件已被文档显式排除，不计入可调用工具。
- 模型路由名称：`gpt-5.6-sol`、`gpt-5.6-terra`、`gpt-5.6-luna` 与 OpenAI 官方 Codex models 页面一致；仓库的成本/风险分配是本项目策略，不是模型能力事实的伪造。

## 5. 剩余 backlog

### 外部/人工依赖

这些不是仓库假实现，但在完成前不得宣称相应自动化能力已经投产：

1. **教师制图标准**：完成 H-01，保持 `drawing-standard` 占位直到有书面/批注/样图依据。
2. **Revit 2021 实机**：完成插件安装、8080 监听、`say_hello`、视图查询和 8 项可丢弃模型测试；保存返回与截图。
3. **Blender MCP 实机**：安装/启用 addon，验证 SSH 隧道、查询/截图和一次 Revit FBX 导入流程。
4. **超分链选择**：按 H-06 用一张代表图做可逆 A/B，确认工具、参数、模型与是否允许生成式细化。

### Minor backlog

1. `docs/SQUADS.md` 与两个工作流仍保留完整旧正文作为历史方法附录。顶部权威声明已阻止误路由；未来如允许整理，可整体迁入专门 `archive/`，减少全文搜索噪声。本轮为遵守“保留结构、禁止大重构”未迁移。
2. 案例文件/ID `ofiice-sakurazaka` 疑似 `office` 拼写错误。修正会改变受保护案例路径、ID、索引和既有引用，本轮未改；未来应以一次受控 ID 迁移处理。
3. `research/building-codes/` 中有作者已明确标记的边缘条文/数值待复核项，并有少量指向未纳入本仓库的未来研究文件名。执行层已经禁止将其当作自动合规结论；真实项目仍须查最新版国家/地方原文和专业意见。

## 6. 整体验收结论

**READY_WITH_BACKLOG。**

仓库具备下一次真实建筑设计作业所需的组织结构、可协同 Skill 契约、Concept → Scheme → Revit Handoff、Gate A–D、人控相机接管和本地 Architecture Case RAG。Revit MCP 已完成只读连接与查询验证；教师制图口径、可丢弃 RVT 的写模型/出图测试，以及 Windows/Blender 实机验证仍是外部前提，不能伪装为已完成。

## 7. 2026-10-20 状态更新（不改写上文历史结论）

本节是后续事实更新，不覆盖 2026-08-12 的验收结论。

- **Revit 写入**：2026-10-04 至 10-19 的真实课程项目已实际使用 `send_code_to_revit` 1,771 次，创建 123 个 Room、墙/门/楼梯/家具并导出 33 页 PDF；最新回读 0 非正面积、0 warnings。TEST_PLAN 8 项逐项记录仍未补齐，因此不能把“项目实践”写成“8 项验收完成”。
- **工作流数量**：`workflows/` 现有 4 个文件（`PIPELINE_WORKFLOW.md`、`SCHEME_DRAWING_REVIEW.md`、`CONCEPT_WORKFLOW.md`、`FEEDBACK_WORKFLOW.md`）；上文“3 个工作流”是 2026-08-12 的时点。
- **Benchmark 口径**：上文 69/70/70 是 Phase 3 六角色合成 Scheme 基准（95 分制）；`benchmarks/scheme-workflow/runs/` 的 M01 57/95、C01 57/95、K01 56/95 是另一轮 Gate B 模拟（通过线 72/95）。两者不可直接比较，引用时必须写轮次。
- **Multica**：server 尚未配置，`multica agent list` 无 server；上文“已部署 Multica 链路仍 blocked”仍成立。
- **drawing-standard**：V0.1 已建立（2026-08-11），不是“尚不存在”；课程特定字段仍待教师确认。
- **当前真实项目**：Wuchang library Gate A 已发生，Gate B 未通过；正式 Drawing 未开始。
