> 历史参考，不作为当前执行指令。以根 AGENTS.md 与 PIPELINE_WORKFLOW 为准。

---
title: Multica Architecture Studio 项目文档
status: active
updated: 2026-10-20
---

# Multica Architecture Studio 项目文档

## 1. 项目简介

`multica-arch-studio` 是面向建筑学课程设计的、平台无关的多 Agent 工作区。它不试图让 AI 替代建筑师作决定，而是把从任务书到汇报的工作组织为可追溯的协作链：AI 负责研究、方案推演、生产、检查和表达；用户始终是设计总监与唯一最终决策者。

仓库以 Markdown、YAML 和少量 Python 标准库脚本为主，可在 Multica 中部署，也可作为独立的课程设计工作区使用。它不包含 Web UI 或特定平台的运行时依赖。

## 2. 设计原则

- **人保有决定权**：四道 Gate 均须由用户明确决策，不得跳过或由 Agent 代替。
- **上游问题回上游解决**：概念、方案、建模、相机或表达问题，回到产生问题的阶段；不以下游渲染或排版掩盖缺口。
- **事实源优先**：共享项目文件和正式 Issue/Handoff 是事实源；聊天记忆不是版本记录。
- **可验证的交接**：每项 Skill 和阶段交接均明确 Required Input、Output、Exit Criteria、Return Conditions 与 Next。
- **工具不等于成果**：MCP 成功返回、脚本执行成功或图片生成成功，都不能替代建筑、图纸或视觉真实性检查。
- **平台与模型解耦**：方法和资产保存在纯文本文件中；模型路由和 Multica 部署是可替换的运行配置。

## 3. 协作架构

团队由一名轻量 Director 和五名专业 Agent 组成。Director 负责阶段路由、版本、交接和 Gate 守门，不代替用户进行建筑设计选择；每个 Issue 只有一个主要责任人。

| Agent | 阶段 | 主要职责 | 人工 Gate |
| --- | --- | --- | --- |
| Director | 全程 | Issue 拆分、路由、Handoff、版本和风险管理 | A–D 守门 |
| Concept Design | 概念 | 解析任务书、场地与类型，形成可比较概念 | Gate A |
| Scheme Design | 方案 | 总图、平剖、流线、体量、尺度与规范风险深化 | Gate B |
| Drawing Production | 生产 | Revit 模型、视图、图纸、版本和自检 | Gate C |
| Visualization | 可视化 | FBX/Blender、机位预览、渲染、增强与超分 | Gate D |
| Presentation | 汇报 | 基于已确认成果组织叙事、分析图和版式 | 无新增 Gate |

旧 8 角色和 3 Squad 架构仅作为方法论归档，不能用于当前路由。具体职责见 [`TEAM_ARCHITECTURE.md`](../../../TEAM_ARCHITECTURE.md) 与 [`agents/`](../../../../agents)。

## 4. 端到端流程与 Gate

```text
任务书 / 场地
  → Director 建立 Issue
  → Concept：案例检索与概念方向
  → Gate A：用户选择、修改、组合或重做概念
  → Scheme：总图、平剖、流线、体量、风险
  → Gate B：用户批准具备完整技术资料的方案进入正式 Drawing
  → Drawing：Revit 模型、图纸、自检
  → Gate C：用户检查模型与图纸
  → Visualization：FBX/Blender/低清机位预览
  → Gate D：用户选定或手工调整相机
  → 图像增强与本地超分
  → Presentation：仅使用已确认版本组织汇报
```

教师反馈进入 [`workflows/FEEDBACK_WORKFLOW.md`](../../../../workflows/FEEDBACK_WORKFLOW.md)，并按问题性质回流至对应阶段；重新影响上游决策的内容必须重新通过相关 Gate。

## 5. 资产与目录

| 路径 | 内容与用途 |
| --- | --- |
| [`agents/`](../../../../agents) | 六个运行角色的职责、边界、输入输出和 Gate 约束 |
| [`skills/`](../../../../skills) | 9 个可复用工作方法：概念、方案、规范、Revit、可视化和建筑类型专项 |
| [`workflows/`](../../../../workflows) | 主流程、方案/画图共同检查、Gate B 方案包、概念流程与反馈回环 |
| [`knowledge/architecture-case-rag/`](../../../../knowledge/architecture-case-rag) | 结构化建筑案例、索引、检索脚本、来源和案例模板 |
| [`research/`](../../../../research) | Revit、建筑规范、Blender MCP 与超分研究资料 |
| [`tools/revit-mcp/`](../../../../tools/revit-mcp) | Revit MCP 的集成说明、安装步骤、人工动作和实机测试计划 |
| [`tools/studio_state/`](../../../../tools/studio_state) | 项目状态核对 CLI：project.yaml 与决策/产物/文件系统的只读对账 |
| [`templates/`](../../../../templates) | 项目事实源和 Issue 模板 |
| [`demo/`](../../../../demo) | 博物馆作业演示任务书 |
| [`docs/`](../../..) | 架构、模型路由、工具、RAG、部署、验收与本项目文档 |
| [`prompts/`](../../../../prompts) | 历史角色提示词归档，不参与当前六角色流程 |

## 6. Skills

| Skill | 使用阶段 | 作用 |
| --- | --- | --- |
| `concept-design` | Concept | 从任务书、场地和类型学形成多个概念方向 |
| `scheme-development` | Scheme | 以 CAD/Revit 验证选定概念的空间、审美与技术，形成正式 Drawing 方案包 |
| `building-code-check` | Scheme | Gate B 前的规范风险自查 |
| `revit-expert` | Scheme 验证 / Drawing | Revit/BIM 建模与出图方法，含 4 份引用资料 |
| `drawing-standard` | Drawing | 课程制图标准；V0.1 已建立（2026-08-11），课程特定字段待教师确认，teacher_override 未冻结 |
| `revit-final-check` | Drawing | Gate C 前的模型、视图、图纸与版本检查 |
| `render-fidelity` | Visualization | 约束增强过程，不改变已确认的建筑事实 |
| `museum-design` | Concept / Scheme | 博物馆类型专项检查 |
| `kindergarten-design` | Concept / Scheme | 幼儿园类型专项检查 |

所有 Skills 均须按自身契约工作；类型专项 Skill 不新增审批 Gate。

## 7. 案例 RAG

案例库用于针对设计问题检索可迁移的建筑证据，而不是收集参考图。每份案例以 1–15 节因果结构记录初始条件、核心问题、概念到总图/功能/平剖/流线/尺度的实现、可迁移方法与不可照搬项，并保留来源 URL 和证据等级。

检索器只依赖 Python 标准库：

```bash
cd knowledge/architecture-case-rag
python3 scripts/search_cases.py --problem "你的具体建筑问题"
python3 scripts/test_rag_tools.py
```

新增案例后运行 `python3 scripts/build_index.py` 重建索引。详细格式、检索参数与扩充策略见 [`RAG.md`](../../../RAG.md)。

## 8. 工具链与运行边界

### Revit MCP

阶段、意图与变更检查遵守[方案与画图共同约定](../../../../workflows/SCHEME_DRAWING_REVIEW.md)。下述连接与测试记录是历史能力证据；2026-10-04 至 10-19 的真实课程项目已在 Revit 2021 中实际使用写入、房间/构件创建与 PDF 导出，但正式 TEST_PLAN 的 8 项逐项记录仍须补齐。不能把只读通过或项目经验扩大成完整建模验收。

Revit MCP 的上游源码以固定提交的独立浅克隆方式存放在本机 `tools/revit-mcp/repo/`，不随本仓库提交；本仓库版本化其接入和验证资料。目标是 Windows 上的 Revit 2021；同机直连或经 SSH 从另一台机器协作均可，执行器与 Revit 同机时不需要 SSH。MCP server 为 stdio，Revit 插件和 npm server 需要在 Windows 侧配合运行。2026-08-13 已实测发现 26 个工具，并以活动视图和模型统计完成只读端到端验证；8 项写模型测试的正式记录仍待补，真实项目已发生 1,771 次 `send_code_to_revit` 写入，但未按 TEST_PLAN 逐项留证。

### Blender 与图像增强

主选 Blender MCP 为 `ahujasid/blender-mcp`：Windows Blender addon 监听 9876，Mac 通过 SSH 端口转发连接。超分候选包括 Mac 的 `waifu2x-ncnn-vulkan` / `chaiNNer` 和 Windows ComfyUI 的 `4x-UltraSharp + UltimateSDUpscale`。它们均需以同一代表图进行实际对比后才能选择为正式链路。

### 模型与调度

模型按任务难度而不是角色固化分配：复杂导演、建筑推理和审查使用高价值推理档；研究、生产与汇报使用日常主力档；轻量收尾使用机械执行档。模型名是示例，不是流程前提；执行器负责开发、研究和资料整理，调度器只负责派发、验收、运行配置和汇总。当前可用执行器包括 Codex 与 DSH，见 [`RUNTIME_ADAPTERS.md`](../../../RUNTIME_ADAPTERS.md)。

## 9. Multica 部署

Multica 部署涉及创建/更新远端 Agent、Skill、Squad 和运行时配置。仓库的 [`MULTICA_DEPLOYMENT.md`](../../../MULTICA_DEPLOYMENT.md) 记录了幂等预检、资源 ID 台账、9 个 Skill 和 6 个 Agent 的部署映射，以及命令级操作说明。Multica server 尚未配置；当前以本地工作区运行，部署文档是待执行方案，不是已部署事实。

执行前须以远端现状为准，先列出包含已归档资源的对象，核验名称与 ID 后再创建或更新。不要依据本地文档中的历史状态直接覆盖远端资源。

## 10. 使用方式

1. 从 [`templates/PROJECT_TEMPLATE.md`](../../../../templates/PROJECT_TEMPLATE.md) 建立作业的事实源，填写任务书原文、场地、面积、交付物、已知约束和未知项。
2. Director 建立 Concept Issue，并将案例检索问题写得具体可判断。
3. Concept 产出多个方向；在 Gate A 获取用户选择或修改。
4. Scheme 深化被选方向并完成规范风险检查；在 Gate B 获取批准。
5. Drawing 根据已确认方案建模、出图和自检；在 Gate C 获取检查结论。
6. Visualization 根据确认几何输出机位预览；在 Gate D 获取相机决定，再进行增强与超分。
7. Presentation 仅引用当前有效、已确认的成果组织汇报。

开始真实作业前，优先处理 [`HUMAN_ACTION_REQUIRED.md`](../../../HUMAN_ACTION_REQUIRED.md) 中适用项，包括教师制图标准、Revit/Blender 实机接入与超分路线选择。

## 11. 验收状态与待办

已完成的工作区验收记录在 [`FINAL_REVIEW.md`](../../../FINAL_REVIEW.md)：Skill 契约、案例索引/检索和内部链接已进行静态核对。该记录不是 Revit、Blender 或超分实机测试的替代品；2026-10-20 的状态更新见该文件末尾。

当前优先待办：

1. 接收教师制图标准资料，确认 `drawing-standard` V0.1 的课程覆盖字段与例外。
2. 补齐 Revit 2021 MCP 的 8 项写模型测试记录；真实项目写入已发生，但未按 TEST_PLAN 逐项留证。
3. 安装并验证 Blender MCP 的 SSH 隧道与 FBX 往返。
4. 用相同代表图对比超分候选链，记录保真度、速度和资源占用结论。
5. 在真实课程作业中继续 Gate A–D 决策闭环；Wuchang library 已发生 Gate A，Gate B 尚未通过。

## 12. 版本管理约定

本仓库提交可复用、可审查的工作区资产：Markdown/YAML 指令、案例与索引、研究资料、脚本、模板和集成文档。不提交以下本地状态：运行日志、一次性任务产物、编辑器配置、环境密钥，以及 `tools/revit-mcp/repo/` 中独立克隆的上游源码。

上游 Revit MCP 更新时，应先更新 `tools/revit-mcp/README.md` 中记录的提交哈希、复核工具/兼容性说明和测试计划，再单独提交文档变更。
